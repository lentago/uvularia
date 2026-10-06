"""Run one GitHub Actions job from a template workflow, locally, step by step.

This is uvularia's own test harness — it is not shipped in any template. It
exists so CI can run a template's real job (say the vault's ``publish``) the way
GitHub would, against a throwaway local git origin, with repository variables
and secrets set or unset, and assert on the result: did the job pass, which
steps ran, and what reached the Loki step.

It is deliberately small. It understands what the templates use and refuses
anything else loudly:

  * ``run:`` steps, executed with ``bash -e`` (GitHub's default shell), with
    ``GITHUB_ENV`` / ``GITHUB_OUTPUT`` / ``GITHUB_STEP_SUMMARY`` honoured;
  * ``if:`` conditions and ``${{ }}`` expressions over ``vars``, ``secrets``,
    ``steps``, ``job``, ``github``, ``env``, with ``always()``, ``success()``,
    ``failure()``, ``cancelled()``, ``!``, ``&&``, ``||``, ``==``, ``!=``;
  * ``continue-on-error`` and the job status it implies;
  * ``uses:`` steps by handler: checkout and setup-python are no-ops (the
    workdir is already a clone and the runner's python3 is used); the
    loki-event action and anything else the caller passes in ``handlers`` are
    callables that receive the rendered ``with:`` inputs and return success.

Needs PyYAML (uvularia's CI installs it; no template depends on it).
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

LOKI_EVENT = "./.github/actions/loki-event"


# --------------------------------------------------------------------------- #
# Expressions.                                                                 #
# --------------------------------------------------------------------------- #

_TOKEN = re.compile(r"""\s*(?:
    (?P<str>'(?:[^']|'')*')
  | (?P<num>\d+(?:\.\d+)?)
  | (?P<op>==|!=|&&|\|\||!|\(|\))
  | (?P<call>[A-Za-z_][\w-]*)\(\)
  | (?P<ident>[A-Za-z_][\w-]*(?:\.[A-Za-z_][\w-]*)*)
)""", re.VERBOSE)


class ExpressionError(ValueError):
    pass


def _tokens(src):
    pos, out = 0, []
    while pos < len(src):
        if src[pos:].strip() == "":
            break
        m = _TOKEN.match(src, pos)
        if not m or m.end() == pos:
            raise ExpressionError(f"cannot parse expression near {src[pos:]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


def _truthy(v):
    return v not in (None, "", False, 0)


def _text(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _eq(a, b):
    # GitHub coerces mixed types; every comparison the templates make is
    # string-to-string (or a missing value against ''), so compare as text.
    return _text(a) == _text(b)


class _Parser:
    def __init__(self, src, ctx, status):
        self.toks = _tokens(src)
        self.i = 0
        self.ctx = ctx
        self.status = status

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        t = self.peek()
        self.i += 1
        return t

    def parse(self):
        v = self.or_()
        if self.i != len(self.toks):
            raise ExpressionError(f"trailing tokens: {self.toks[self.i:]}")
        return v

    def or_(self):
        v = self.and_()
        while self.peek() == ("op", "||"):
            self.take()
            r = self.and_()
            v = v if _truthy(v) else r
        return v

    def and_(self):
        v = self.cmp()
        while self.peek() == ("op", "&&"):
            self.take()
            r = self.cmp()
            v = r if _truthy(v) else v
        return v

    def cmp(self):
        v = self.unary()
        while self.peek() in (("op", "=="), ("op", "!=")):
            op = self.take()[1]
            r = self.unary()
            v = _eq(v, r) if op == "==" else not _eq(v, r)
        return v

    def unary(self):
        if self.peek() == ("op", "!"):
            self.take()
            return not _truthy(self.unary())
        return self.atom()

    def atom(self):
        kind, val = self.take()
        if kind == "op" and val == "(":
            v = self.or_()
            if self.take() != ("op", ")"):
                raise ExpressionError("missing )")
            return v
        if kind == "str":
            return val[1:-1].replace("''", "'")
        if kind == "num":
            return float(val) if "." in val else int(val)
        if kind == "call":
            fn = {"always": True, "success": self.status == "success",
                  "failure": self.status == "failure", "cancelled": False}
            if val not in fn:
                raise ExpressionError(f"unsupported function {val}()")
            return fn[val]
        if kind == "ident":
            if val in ("true", "false"):
                return val == "true"
            if val == "null":
                return None
            cur = self.ctx
            for part in val.split("."):
                cur = cur.get(part) if isinstance(cur, dict) else None
            return cur
        raise ExpressionError(f"unexpected token {val!r}")


def evaluate(expr, ctx, status="success"):
    return _Parser(expr, ctx, status).parse()


def render(text, ctx, status="success"):
    def sub(m):
        return _text(evaluate(m.group(1), ctx, status))
    return re.sub(r"\$\{\{(.*?)\}\}", sub, str(text), flags=re.DOTALL)


def condition(step_if, ctx, status):
    if step_if is None:
        return status == "success"
    expr = str(step_if).strip()
    if expr.startswith("${{") and expr.endswith("}}"):
        expr = expr[3:-2]
    if not re.search(r"\b(always|success|failure|cancelled)\(\)", expr):
        expr = f"success() && ({expr})"
    return _truthy(evaluate(expr, ctx, status))


# --------------------------------------------------------------------------- #
# The job.                                                                     #
# --------------------------------------------------------------------------- #

@dataclass
class StepResult:
    name: str
    id: str | None
    outcome: str          # success | failure | skipped
    conclusion: str
    log: str = ""


@dataclass
class JobResult:
    status: str
    steps: list[StepResult] = field(default_factory=list)

    @property
    def log(self):
        return "\n".join(s.log for s in self.steps)

    def step(self, name_prefix):
        return next(s for s in self.steps if s.name.startswith(name_prefix))


def _parse_kv_file(path):
    """GitHub's NAME=value and NAME<<DELIM multi-line formats."""
    out, lines, i = {}, Path(path).read_text().splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if "<<" in line and ("=" not in line or line.index("<<") < line.index("=")):
            name, delim = line.split("<<", 1)
            buf, i = [], i + 1
            while i < len(lines) and lines[i] != delim:
                buf.append(lines[i])
                i += 1
            out[name] = "\n".join(buf)
        elif "=" in line:
            name, value = line.split("=", 1)
            out[name] = value
        i += 1
    return out


def load_job(workflow_path, job_id):
    wf = yaml.safe_load(Path(workflow_path).read_text())
    return wf, wf["jobs"][job_id]


def run_job(workflow, job, workdir, *, vars_=None, secrets=None, github=None,
            handlers=None, base_env=None):
    """Run ``job`` (a parsed job mapping) from ``workflow`` in ``workdir``."""
    workdir = Path(workdir)
    handlers = dict(handlers or {})
    handlers.setdefault("actions/checkout", lambda inputs: True)
    handlers.setdefault("actions/setup-python", lambda inputs: True)
    temp = Path(tempfile.mkdtemp(prefix="runner-temp-"))
    github = dict(github or {})
    env = {k: str(v) for k, v in (workflow.get("env") or {}).items()}
    env.update({k: str(v) for k, v in (job.get("env") or {}).items()})
    ctx = {"vars": dict(vars_ or {}), "secrets": dict(secrets or {}), "github": github,
           "steps": {}, "job": {"status": "success"}, "env": env}
    result = JobResult(status="success")

    for n, step in enumerate(job["steps"]):
        name = step.get("name") or step.get("uses") or f"step {n}"
        sid = step.get("id")
        status = result.status
        ctx["job"]["status"] = status
        if not condition(step.get("if"), ctx, status):
            result.steps.append(StepResult(name, sid, "skipped", "skipped"))
            if sid:
                ctx["steps"][sid] = {"outcome": "skipped", "conclusion": "skipped", "outputs": {}}
            continue

        outputs, log = {}, ""
        if "uses" in step:
            action = step["uses"].split("@", 1)[0]
            if action not in handlers:
                raise NotImplementedError(f"no handler for uses: {step['uses']}")
            inputs = {k: render(v, ctx, status) for k, v in (step.get("with") or {}).items()}
            ok = bool(handlers[action](inputs))
            log = f"[{action}] {'ok' if ok else 'failed'}"
        else:
            out_file, env_file = temp / f"out{n}", temp / f"env{n}"
            out_file.write_text("")
            env_file.write_text("")
            step_env = {k: render(v, ctx, status) for k, v in (step.get("env") or {}).items()}
            proc_env = {
                **(base_env or {"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/tmp")}),
                **{k: render(v, ctx, status) for k, v in env.items()},
                **step_env,
                "GITHUB_OUTPUT": str(out_file), "GITHUB_ENV": str(env_file),
                "GITHUB_STEP_SUMMARY": str(temp / "summary.md"), "RUNNER_TEMP": str(temp),
                "GITHUB_REPOSITORY": github.get("repository", ""),
                "GITHUB_REPOSITORY_OWNER": github.get("repository_owner", ""),
                "GITHUB_SHA": github.get("sha", ""), "GITHUB_RUN_ID": github.get("run_id", ""),
                "GITHUB_SERVER_URL": github.get("server_url", "https://github.com"),
            }
            script = temp / f"step{n}.sh"
            script.write_text(render(step["run"], ctx, status))
            cwd = workdir / render(step.get("working-directory", "."), ctx, status)
            proc = subprocess.run(["bash", "-e", str(script)], cwd=cwd, env=proc_env,
                                  capture_output=True, text=True, timeout=300)
            ok = proc.returncode == 0
            log = proc.stdout + proc.stderr
            outputs = _parse_kv_file(out_file)
            env.update(_parse_kv_file(env_file))

        outcome = "success" if ok else "failure"
        conclusion = "success" if (ok or step.get("continue-on-error")) else "failure"
        if conclusion == "failure":
            result.status = "failure"
        result.steps.append(StepResult(name, sid, outcome, conclusion, log))
        if sid:
            ctx["steps"][sid] = {"outcome": outcome, "conclusion": conclusion, "outputs": outputs}
    return result
