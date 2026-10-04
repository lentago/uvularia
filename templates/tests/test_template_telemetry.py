"""Telemetry across the templates' workflows (issue #52).

Three things are held here, in uvularia's own CI (none of this ships):

  1. **The records template's publish job passes with telemetry unset.** The
     real ``publish.yml`` job runs step by step (``run_job.py``) against a
     throwaway local origin seeded from ``templates/records/``: it must go green,
     print the "telemetry not configured" notice once, and never reach the Loki
     step. With the variables set and Loki down, it must still go green, and the
     event it tried to send must be well formed. The validate job is held to the
     same "unset is quiet" rule.
  2. **Every telemetry step in every template workflow has the same safe
     shape** — gated on the describe step, unable to fail the job, time-boxed,
     labelled ``source: uvularia`` with a stage drosera accepts.
  3. **The two copies of ``scripts/telemetry.py`` are byte-identical.**

Each check is also run against a mutated copy (a gate removed, a
``continue-on-error`` dropped) to prove it can fail.

    pip install pyyaml
    python3 -m unittest discover -s templates/tests -p "test_*.py" -v
"""

import copy
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import run_job

TEMPLATES = Path(__file__).resolve().parents[1]
RECORDS = TEMPLATES / "records"
RULES = TEMPLATES / "ask-rules"

TEMPLATE_WORKFLOWS = {
    RECORDS / ".github/workflows/intake.yml": ("intake", "records", "intake"),
    RECORDS / ".github/workflows/validate.yml": ("validate", "records", "reviewed"),
    RECORDS / ".github/workflows/publish.yml": ("publish", "records", "published"),
    RULES / ".github/workflows/evals.yml": ("evals", "rules", "evals"),
    RULES / ".github/workflows/release.yml": ("release", "rules", "rules_released"),
}

# The label rules from drosera's loki-event push.sh (drosera#219). The action
# rejects anything else, so a template that sent it would only ever log an error.
DROSERA_CHECKS = {
    "source": r"[a-z][a-z0-9_]{0,31}",
    "stage": r"[a-z][a-z0-9_]{0,31}",
    "pipeline": r"[a-z0-9][a-z0-9_-]{0,62}",
    "cluster": r"[a-z0-9][a-z0-9_-]{0,62}",
}

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True, env={**_base_env(), **GIT_ENV}).stdout.strip()


def _base_env():
    import os
    return {"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/tmp")}


class LokiRecorder:
    """Stands in for the loki-event action: validates inputs as drosera would,
    records the call, and answers like a Loki that is up or down."""

    def __init__(self, up=True):
        self.up = up
        self.calls = []

    def __call__(self, inputs):
        self.calls.append(inputs)
        for name, pattern in DROSERA_CHECKS.items():
            if not re.fullmatch(pattern, inputs.get(name, "")):
                return False
        if not inputs.get("loki_url") or not re.fullmatch(r".+:.+", inputs.get("loki_token", "")):
            return False
        if not isinstance(json.loads(inputs.get("payload-json") or "{}"), dict):
            return False
        return self.up


def make_vault_repo(tmp):
    """A clone of templates/records/ whose origin is a local bare repo."""
    origin, work = tmp / "origin.git", tmp / "work"
    shutil.copytree(RECORDS, work, ignore=shutil.ignore_patterns("__pycache__"))
    _git(tmp, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(work, "init", "-q", "-b", "main")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "seed")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "-q", "origin", "main")
    return origin, work


def run_publish(job, *, vars_=None, secrets=None, loki=None):
    tmp = Path(tempfile.mkdtemp(prefix="publish-"))
    try:
        origin, work = make_vault_repo(tmp)
        wf, _ = run_job.load_job(RECORDS / ".github/workflows/publish.yml", "publish")
        loki = loki or LokiRecorder()
        result = run_job.run_job(
            wf, job, work, vars_=vars_, secrets=secrets, base_env=_base_env(),
            github={"repository": "Example-Org/example-records", "repository_owner": "Example-Org",
                    "sha": _git(work, "rev-parse", "HEAD"), "run_id": "4242"},
            handlers={run_job.LOKI_EVENT: loki,
                      "actions/attest-build-provenance": lambda inputs: True})
        published = _git(tmp, "--git-dir", str(origin), "ls-tree", "-r", "--name-only",
                         "published") if result.status == "success" else ""
        return result, loki, published
    finally:
        shutil.rmtree(tmp)


def publish_job():
    return copy.deepcopy(run_job.load_job(RECORDS / ".github/workflows/publish.yml", "publish")[1])


def _step(job, prefix):
    return next(s for s in job["steps"] if s.get("name", "").startswith(prefix))


class PublishJobWithTelemetryUnset(unittest.TestCase):
    def test_passes_quietly_and_never_reaches_loki(self):
        result, loki, published = run_publish(publish_job())
        self.assertEqual(result.status, "success", result.log)
        self.assertEqual(loki.calls, [])
        self.assertEqual(result.log.count("telemetry not configured"), 1)
        self.assertEqual(result.step("Telemetry — push").outcome, "skipped")
        self.assertIn("standing.json", published.splitlines())

    def test_can_fail_an_ungated_push_reaches_loki(self):
        job = publish_job()
        del _step(job, "Telemetry — push")["if"]
        result, loki, _ = run_publish(job)
        self.assertEqual(len(loki.calls), 1, "the mutation should make the check fail")


class PublishJobWithTelemetrySetAndLokiDown(unittest.TestCase):
    VARS = {"LOKI_PUSH_URL": "https://logs-prod-000.grafana.net"}
    SECRETS = {"LOKI_WRITE_TOKEN": "123:glc_test"}

    def test_outage_never_fails_the_publish_and_the_event_is_well_formed(self):
        result, loki, published = run_publish(publish_job(), vars_=self.VARS, secrets=self.SECRETS,
                                              loki=LokiRecorder(up=False))
        self.assertEqual(result.status, "success", result.log)
        self.assertIn("standing.json", published.splitlines())
        self.assertEqual(len(loki.calls), 1)
        call = loki.calls[0]
        self.assertEqual((call["source"], call["pipeline"], call["stage"], call["cluster"]),
                         ("uvularia", "records", "published", "example-org"))
        payload = json.loads(call["payload-json"])
        self.assertRegex(payload["digest"], r"^[0-9a-f]{64}$")
        self.assertTrue(payload["receipt"].endswith(f"-{payload['digest']}.md"))
        self.assertEqual(payload["records"]["total"], 0)
        self.assertEqual(payload["standing"]["total"], 1)
        self.assertEqual(payload["job_status"], "success")
        self.assertEqual(result.step("Telemetry — push").outcome, "failure")

    def test_can_fail_without_continue_on_error_an_outage_fails_the_publish(self):
        job = publish_job()
        del _step(job, "Telemetry — push")["continue-on-error"]
        result, _, _ = run_publish(job, vars_=self.VARS, secrets=self.SECRETS,
                                   loki=LokiRecorder(up=False))
        self.assertEqual(result.status, "failure")


class ValidateJobWithTelemetryUnset(unittest.TestCase):
    def test_passes_quietly(self):
        tmp = Path(tempfile.mkdtemp(prefix="validate-"))
        try:
            _, work = make_vault_repo(tmp)
            wf, job = run_job.load_job(RECORDS / ".github/workflows/validate.yml", "validate")
            loki = LokiRecorder()
            result = run_job.run_job(
                wf, job, work, base_env=_base_env(),
                github={"repository": "o/r", "repository_owner": "o", "base_ref": "main",
                        "event": {"pull_request": {"number": 3}}},
                handlers={run_job.LOKI_EVENT: loki, "actions/github-script": lambda i: True})
        finally:
            shutil.rmtree(tmp)
        self.assertEqual(result.status, "success", result.log)
        self.assertEqual(loki.calls, [])
        self.assertEqual(result.log.count("telemetry not configured"), 1)


# --------------------------------------------------------------------------- #
# Static shape of every telemetry step.                                        #
# --------------------------------------------------------------------------- #

def telemetry_problems(job, pipeline, stage):
    """Everything wrong with a job's telemetry steps; empty means safe."""
    problems = []
    steps = job["steps"]
    describe = [s for s in steps if s.get("id") == "telemetry"]
    push = [s for s in steps if str(s.get("uses", "")).startswith(run_job.LOKI_EVENT + "@")]
    if len(describe) != 1 or len(push) != 1:
        return [f"want one describe step (id: telemetry) and one loki-event step, "
                f"got {len(describe)} and {len(push)}"]
    d, p = describe[0], push[0]
    if steps.index(d) > steps.index(p):
        problems.append("the describe step must come before the push")
    for label, s in (("describe", d), ("push", p)):
        if s.get("continue-on-error") is not True:
            problems.append(f"{label} step must be continue-on-error: true")
        if "always()" not in str(s.get("if", "")):
            problems.append(f"{label} step must run if: always()")
    if "steps.telemetry.outputs.enabled == 'true'" not in str(p.get("if", "")):
        problems.append("push step must be gated on steps.telemetry.outputs.enabled == 'true'")
    if not p.get("timeout-minutes"):
        problems.append("push step needs a timeout-minutes")
    w = p.get("with") or {}
    want = {"source": "uvularia", "pipeline": pipeline, "stage": stage,
            "loki_url": "${{ vars.LOKI_PUSH_URL }}", "loki_token": "${{ secrets.LOKI_WRITE_TOKEN }}"}
    for k, v in want.items():
        if w.get(k) != v:
            problems.append(f"push step with.{k} is {w.get(k)!r}, want {v!r}")
    for k in ("source", "stage", "pipeline"):
        if not re.fullmatch(DROSERA_CHECKS[k], str(w.get(k, ""))):
            problems.append(f"with.{k} {w.get(k)!r} breaks drosera's label rule")
    if f"telemetry.py {stage}" not in str(d.get("run", "")):
        problems.append(f"describe step must run scripts/telemetry.py {stage}")
    env = d.get("env") or {}
    if env.get("LOKI_PUSH_URL") != "${{ vars.LOKI_PUSH_URL }}":
        problems.append("describe step must read LOKI_PUSH_URL from vars")
    if any(re.search(r"secrets\.LOKI_WRITE_TOKEN\s*}}", str(v)) for v in env.values()):
        problems.append("describe step must not receive the token itself (only whether it is set)")
    return problems


class EveryTelemetryStepIsSafe(unittest.TestCase):
    def test_all_template_workflows(self):
        for path, (job_id, pipeline, stage) in TEMPLATE_WORKFLOWS.items():
            with self.subTest(workflow=path.name):
                _, job = run_job.load_job(path, job_id)
                self.assertEqual(telemetry_problems(job, pipeline, stage), [])

    def test_can_fail(self):
        _, job = run_job.load_job(RECORDS / ".github/workflows/publish.yml", "publish")
        for mutate in (lambda s: s.pop("continue-on-error"),
                       lambda s: s.__setitem__("if", "always()"),
                       lambda s: s.pop("timeout-minutes"),
                       lambda s: s["with"].__setitem__("stage", "pub-lished")):
            j = copy.deepcopy(job)
            mutate(_step(j, "Telemetry — push"))
            self.assertNotEqual(telemetry_problems(j, "records", "published"), [])


class TelemetryHelperCopiesMatch(unittest.TestCase):
    def test_records_and_rules_copies_are_byte_identical(self):
        a = (RECORDS / "scripts/telemetry.py").read_bytes()
        b = (RULES / "scripts/telemetry.py").read_bytes()
        self.assertEqual(a, b, "templates/{records,ask-rules}/scripts/telemetry.py have drifted; "
                               "edit one and copy it over the other")


if __name__ == "__main__":
    unittest.main()
