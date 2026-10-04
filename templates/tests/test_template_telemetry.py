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
  4. **The publish job writes the public board (issue #70).** ``index.html``
     lands on the published branch next to ``standing.json``.
  5. **The schedules (issue #59) are quiet when unset and never red.** The
     records template's daily snapshot jobs pass with telemetry unset and ask
     GitHub nothing; the rules template's 15-minute heartbeat passes with no
     URL, with a box that answers, and with one that does not.

Each check is also run against a mutated copy (a gate removed, a
``continue-on-error`` dropped) to prove it can fail.

    pip install pyyaml
    python3 -m unittest discover -s templates/tests -p "test_*.py" -v
"""

import copy
import http.server
import json
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

import run_job

TEMPLATES = Path(__file__).resolve().parents[1]
RECORDS = TEMPLATES / "records"
RULES = TEMPLATES / "ask-rules"

TEMPLATE_WORKFLOWS = [
    (RECORDS / ".github/workflows/intake.yml", "intake", "records", "intake"),
    (RECORDS / ".github/workflows/validate.yml", "validate", "records", "reviewed"),
    (RECORDS / ".github/workflows/publish.yml", "publish", "records", "published"),
    (RECORDS / ".github/workflows/daily-snapshot.yml", "intake", "records", "intake"),
    (RECORDS / ".github/workflows/daily-snapshot.yml", "reviewed", "records", "reviewed"),
    (RULES / ".github/workflows/evals.yml", "evals", "rules", "evals"),
    (RULES / ".github/workflows/release.yml", "release", "rules", "rules_released"),
]

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


def run_publish(job, *, vars_=None, secrets=None, loki=None, board=None):
    """Run the publish job against a throwaway origin. Returns the result, the
    Loki stand-in, and the published branch's file list; pass ``board=[]`` to
    have the published ``index.html`` appended to that list."""
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
        if board is not None and "index.html" in published.splitlines():
            board.append(_git(tmp, "--git-dir", str(origin), "show", "published:index.html"))
        return result, loki, published
    finally:
        shutil.rmtree(tmp)


def publish_job():
    return copy.deepcopy(run_job.load_job(RECORDS / ".github/workflows/publish.yml", "publish")[1])


def _step(job, prefix):
    return next(s for s in job["steps"] if s.get("name", "").startswith(prefix))


class PublishJobWritesTheBoard(unittest.TestCase):
    """Issue #70: the publish job lays a plain board page onto the published branch."""

    def test_index_html_on_the_published_branch(self):
        board = []
        result, _, published = run_publish(publish_job(), board=board)
        self.assertEqual(result.status, "success", result.log)
        self.assertEqual(result.step("Write the public board page").outcome, "success")
        self.assertIn("index.html", published.splitlines())
        page = board[0]
        self.assertIn('<html lang="en">', page)
        self.assertIn("Meeting minutes made available in a timely manner", page)
        self.assertIn("https://github.com/Example-Org/example-records/blob/published/receipts/", page)

    def test_can_fail_without_the_copy_no_board_is_published(self):
        job = publish_job()
        lay = _step(job, "Lay the artifacts")
        lay["run"] = lay["run"].replace("cp _out/index.html", "true _out/index.html")
        result, _, published = run_publish(job)
        self.assertEqual(result.status, "success", result.log)
        self.assertNotIn("index.html", published.splitlines(), "the mutation should make the check fail")


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
        self.assertIsInstance(payload["at"], int)
        self.assertNotIn("announcement_latency_s", payload, "no announcement went live")
        self.assertEqual(result.step("Telemetry — time announcements").outcome, "success")
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
        self.assertEqual(result.step("Telemetry — count").outcome, "skipped")


class DailySnapshotJobs(unittest.TestCase):
    """The daily intake/reviewed snapshot (issue #59) in the records template."""

    WORKFLOW = RECORDS / ".github/workflows/daily-snapshot.yml"

    def _run(self, job_id, *, vars_=None, secrets=None, loki=None, job=None):
        tmp = Path(tempfile.mkdtemp(prefix="snapshot-"))
        try:
            _, work = make_vault_repo(tmp)
            wf, loaded = run_job.load_job(self.WORKFLOW, job_id)
            loki = loki or LokiRecorder()
            result = run_job.run_job(
                wf, job or loaded, work, vars_=vars_, secrets=secrets, base_env=_base_env(),
                github={"repository": "Example-Org/example-records",
                        "repository_owner": "Example-Org", "run_id": "5"},
                handlers={run_job.LOKI_EVENT: loki})
        finally:
            shutil.rmtree(tmp)
        return result, loki

    def test_unset_is_quiet_and_asks_github_nothing(self):
        for job_id in ("intake", "reviewed"):
            with self.subTest(job=job_id):
                result, loki = self._run(job_id)
                self.assertEqual(result.status, "success", result.log)
                self.assertEqual(loki.calls, [])
                self.assertEqual(result.log.count("telemetry not configured"), 1)
                self.assertEqual(result.step("Telemetry — count").outcome, "skipped")

    def test_set_with_github_unreachable_sends_nothing_and_stays_green(self):
        # No token reaches the harness, so the count is left out; a scheduled
        # run with no count has nothing to say and sends no event.
        result, loki = self._run("intake", vars_={"LOKI_PUSH_URL": "https://logs.example"},
                                 secrets={"LOKI_WRITE_TOKEN": "1:glc_t"})
        self.assertEqual(result.status, "success", result.log)
        self.assertEqual(result.step("Telemetry — count").outcome, "success")
        self.assertEqual(loki.calls, [])

    COUNT = {"open": 2, "oldest_opened_at": 1_791_000_000}

    def _job_with_a_fixed_count(self, describe_run=None):
        """The intake job with the GitHub call replaced by a known count."""
        _, job = run_job.load_job(self.WORKFLOW, "intake")
        job = copy.deepcopy(job)
        _step(job, "Telemetry — count")["run"] = (
            f"echo '{json.dumps(self.COUNT)}' > \"$RUNNER_TEMP/intake-snapshot.json\"")
        if describe_run:
            d = next(s for s in job["steps"] if s.get("id") == "telemetry")
            d["run"] = describe_run(d["run"])
        return job

    def test_the_count_reaches_loki_with_at(self):
        result, loki = self._run("intake", vars_={"LOKI_PUSH_URL": "https://logs.example"},
                                 secrets={"LOKI_WRITE_TOKEN": "1:glc_t"},
                                 job=self._job_with_a_fixed_count())
        self.assertEqual(result.status, "success", result.log)
        self.assertEqual(len(loki.calls), 1)
        self.assertEqual(loki.calls[0]["stage"], "intake")
        payload = json.loads(loki.calls[0]["payload-json"])
        self.assertEqual({k: payload[k] for k in self.COUNT}, self.COUNT)
        self.assertIsInstance(payload["at"], int)
        self.assertNotIn("outcome", payload)

    def test_can_fail_without_the_scheduled_flag_no_event_goes_out(self):
        job = self._job_with_a_fixed_count(lambda run: run.replace("--scheduled", ""))
        result, loki = self._run("intake", vars_={"LOKI_PUSH_URL": "https://logs.example"},
                                 secrets={"LOKI_WRITE_TOKEN": "1:glc_t"}, job=job)
        self.assertEqual(loki.calls, [], "the mutation should make the check fail")


# --------------------------------------------------------------------------- #
# The rules template's 15-minute heartbeat (issue #59).                        #
# --------------------------------------------------------------------------- #

class _Health(http.server.BaseHTTPRequestHandler):
    hits = []

    def do_GET(self):  # noqa: N802
        type(self).hits.append(self.path)
        body = b'{"status":"ok","digest":"abc","rules_tag":"rules-v2"}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class HeartbeatPing(unittest.TestCase):
    WORKFLOW = RULES / ".github/workflows/heartbeat.yml"

    def _run(self, vars_=None, job=None):
        tmp = Path(tempfile.mkdtemp(prefix="heartbeat-"))
        try:
            wf, loaded = run_job.load_job(self.WORKFLOW, "ping")
            return run_job.run_job(wf, job or loaded, tmp, vars_=vars_, base_env=_base_env())
        finally:
            shutil.rmtree(tmp)

    def test_every_fifteen_minutes_with_no_token(self):
        wf, job = run_job.load_job(self.WORKFLOW, "ping")
        self.assertEqual(wf[True]["schedule"], [{"cron": "*/15 * * * *"}])  # YAML 1.1: on → True
        self.assertEqual(wf["permissions"], {})

    def test_unset_url_is_a_notice(self):
        result = self._run()
        self.assertEqual(result.status, "success", result.log)
        self.assertIn("ASK_HEALTH_URL is not set", result.log)

    def test_pings_health(self):
        _Health.hits = []
        server = http.server.HTTPServer(("127.0.0.1", 0), _Health)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/health"
            result = self._run({"ASK_HEALTH_URL": url})
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(result.status, "success", result.log)
        self.assertEqual(_Health.hits, ["/health"])
        self.assertIn('"rules_tag":"rules-v2"', result.log)

    def test_a_box_that_does_not_answer_is_a_warning_not_a_red_run(self):
        result = self._run({"ASK_HEALTH_URL": "http://127.0.0.1:9/health"})
        self.assertEqual(result.status, "success", result.log)
        self.assertIn("::warning title=heartbeat::", result.log)

    def test_can_fail_a_bare_curl_turns_an_outage_red(self):
        _, job = run_job.load_job(self.WORKFLOW, "ping")
        job = copy.deepcopy(job)
        job["steps"][0]["run"] = 'curl --silent --fail --max-time 5 "$ASK_HEALTH_URL"'
        result = self._run({"ASK_HEALTH_URL": "http://127.0.0.1:9/health"}, job=job)
        self.assertEqual(result.status, "failure")


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
    run = str(d.get("run", ""))
    if stage in ("intake", "reviewed") and "--snapshot" not in run:
        problems.append(f"the {stage} describe step must pass --snapshot (issue #59)")
    env = d.get("env") or {}
    if env.get("LOKI_PUSH_URL") != "${{ vars.LOKI_PUSH_URL }}":
        problems.append("describe step must read LOKI_PUSH_URL from vars")
    if any(re.search(r"secrets\.LOKI_WRITE_TOKEN\s*}}", str(v)) for v in env.values()):
        problems.append("describe step must not receive the token itself (only whether it is set)")
    return problems


class EveryTelemetryStepIsSafe(unittest.TestCase):
    def test_all_template_workflows(self):
        for path, job_id, pipeline, stage in TEMPLATE_WORKFLOWS:
            with self.subTest(workflow=path.name, job=job_id):
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
