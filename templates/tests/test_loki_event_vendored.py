"""The vendored ``loki-event`` action: unchanged, identical in both templates, used locally.

The records and rules templates each carry a copy of drosera's ``loki-event``
composite action under ``.github/actions/loki-event/``, so a client's workflows
reference nothing outside the client's own repository (ADR-0007, client-owned
delivery). GitHub downloads every action a job names at "Set up job", even a
step that is later skipped, so a remote reference would be a dependency on a
lentago repository whether telemetry is on or not.

Held here (uvularia's own CI; none of this ships):

  1. ``action.yml`` carries a six-line header naming the upstream commit and the
     sha256 of upstream ``action.yml`` and ``push.sh``; the body below the header
     and ``push.sh`` match those hashes, so a hand edit fails the build. With
     ``UVULARIA_CHECK_UPSTREAM=1`` both are also fetched from drosera at the
     named commit and compared; an unreachable GitHub is a skip with a notice.
  2. The two templates' copies are byte-identical and ``push.sh`` is executable.
  3. No template workflow names an action in a lentago repository, and every
     loki-event step uses the local copy.
  4. ``push.sh`` really pushes: against a local HTTP server it sends the labels
     and payload drosera documents, with basic auth, and refuses a bad label.

To take a newer drosera: copy ``action.yml`` (below the header) and ``push.sh``
into both templates, update the commit and the two hashes in the header, and
run these tests.

    python3 -m unittest discover -s templates/tests -p "test_*.py" -v
"""

import base64
import hashlib
import http.server
import json
import os
import re
import subprocess
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1]
COPIES = [TEMPLATES / "records/.github/actions/loki-event",
          TEMPLATES / "ask-rules/.github/actions/loki-event"]
HEADER_LINES = 6
LOCAL_REF = "./.github/actions/loki-event"


def split_action(text: bytes):
    """(header, body, commit, [sha256 of action.yml, sha256 of push.sh])."""
    lines = text.splitlines(keepends=True)
    header = b"".join(lines[:HEADER_LINES]).decode("utf-8")
    body = b"".join(lines[HEADER_LINES:])
    commit = re.search(r"\b([0-9a-f]{40})\b", header)
    digests = re.findall(r"^#\s*([0-9a-f]{64})\s*$", header, re.MULTILINE)
    return header, body, commit and commit.group(1), digests


def vendoring_problems(action: bytes, push: bytes):
    """Everything wrong with one vendored copy; empty means unchanged."""
    header, body, commit, digests = split_action(action)
    if "lentago/drosera .github/actions/loki-event" not in header:
        return ["header must name lentago/drosera .github/actions/loki-event"]
    if not commit:
        return ["header must name the upstream commit"]
    if len(digests) != 2:
        return [f"header must carry two sha256 lines (action.yml, push.sh), got {len(digests)}"]
    problems = []
    if hashlib.sha256(body).hexdigest() != digests[0]:
        problems.append("action.yml was edited after vendoring; re-copy it from drosera")
    if hashlib.sha256(push).hexdigest() != digests[1]:
        problems.append("push.sh was edited after vendoring; re-copy it from drosera")
    return problems


class VendoredCopiesAreUnchanged(unittest.TestCase):
    def test_each_copy_matches_its_recorded_hashes(self):
        for d in COPIES:
            with self.subTest(copy=str(d.relative_to(TEMPLATES))):
                self.assertEqual(vendoring_problems((d / "action.yml").read_bytes(),
                                                    (d / "push.sh").read_bytes()), [])

    def test_can_fail(self):
        action = (COPIES[0] / "action.yml").read_bytes()
        push = (COPIES[0] / "push.sh").read_bytes()
        self.assertNotEqual(vendoring_problems(action + b"# edit\n", push), [])
        self.assertNotEqual(vendoring_problems(action, push.replace(b"--max-time 10", b"--max-time 99")), [])
        self.assertNotEqual(vendoring_problems(b"name: loki-event\n" + action, push), [])

    def test_the_two_templates_carry_the_same_copy(self):
        for name in ("action.yml", "push.sh"):
            with self.subTest(file=name):
                self.assertEqual((COPIES[0] / name).read_bytes(), (COPIES[1] / name).read_bytes(),
                                 f"templates/{{records,ask-rules}}/.github/actions/loki-event/{name} "
                                 "have drifted; copy one over the other")

    def test_push_sh_is_executable(self):
        # action.yml runs "$GITHUB_ACTION_PATH/push.sh" directly.
        for d in COPIES:
            with self.subTest(copy=str(d.relative_to(TEMPLATES))):
                self.assertTrue(os.access(d / "push.sh", os.X_OK))

    def test_the_composite_action_uses_no_other_action(self):
        _, body, _, _ = split_action((COPIES[0] / "action.yml").read_bytes())
        self.assertNotRegex(body.decode("utf-8"), r"(?m)^\s*-?\s*uses:")

    @unittest.skipUnless(os.environ.get("UVULARIA_CHECK_UPSTREAM") == "1",
                         "set UVULARIA_CHECK_UPSTREAM=1 to compare against drosera")
    def test_matches_upstream_at_the_named_commit(self):
        _, body, commit, _ = split_action((COPIES[0] / "action.yml").read_bytes())
        local = {"action.yml": body, "push.sh": (COPIES[0] / "push.sh").read_bytes()}
        for name, mine in local.items():
            url = (f"https://raw.githubusercontent.com/lentago/drosera/{commit}"
                   f"/.github/actions/loki-event/{name}")
            try:
                with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310
                    upstream = resp.read()
            except (urllib.error.URLError, TimeoutError) as exc:
                self.skipTest(f"notice: could not reach {url} ({exc})")
            self.assertEqual(mine, upstream, f"{name} differs from drosera at {commit}")


class TemplateWorkflowsUseTheLocalCopy(unittest.TestCase):
    def test_no_lentago_actions_and_loki_event_is_local(self):
        workflows = sorted(TEMPLATES.glob("*/.github/workflows/*.yml"))
        self.assertTrue(workflows)
        seen = 0
        for wf in workflows:
            for n, line in enumerate(wf.read_text().splitlines(), 1):
                m = re.match(r"\s*(?:-\s*)?uses:\s*(\S+)", line)
                if not m:
                    continue
                ref = m.group(1)
                where = f"{wf.relative_to(TEMPLATES)}:{n}"
                self.assertFalse(ref.lower().startswith("lentago/"),
                                 f"{where} uses {ref}: a client's workflow must not depend on a "
                                 "lentago repository")
                if "loki-event" in ref:
                    self.assertEqual(ref, LOCAL_REF, f"{where} must use {LOCAL_REF}")
                    seen += 1
        self.assertGreater(seen, 0, "expected the templates' telemetry steps to use loki-event")


class _Loki(http.server.BaseHTTPRequestHandler):
    calls: list = []

    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        type(self).calls.append({"path": self.path, "auth": self.headers.get("Authorization"),
                                 "body": json.loads(body)})
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


class PushShPushes(unittest.TestCase):
    def setUp(self):
        _Loki.calls = []
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _Loki)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def _push(self, **over):
        env = {"PATH": os.environ["PATH"], "LE_LOKI_URL": self.url,
               "LE_LOKI_TOKEN": "123456:glc_test", "LE_CLUSTER": "example-org",
               "LE_SOURCE": "uvularia", "LE_PIPELINE": "records", "LE_STAGE": "published",
               "LE_REPO": "Example-Org/example-records", "LE_PAYLOAD_JSON": '{"records": 3}'}
        env.update(over)
        return subprocess.run([str(COPIES[0] / "push.sh")], env=env, capture_output=True,
                              text=True, timeout=30)

    def test_sends_the_documented_labels_and_payload(self):
        proc = self._push()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(_Loki.calls), 1)
        call = _Loki.calls[0]
        self.assertEqual(call["path"], "/loki/api/v1/push")
        self.assertEqual(call["auth"], "Basic " + base64.b64encode(b"123456:glc_test").decode())
        stream = call["body"]["streams"][0]
        self.assertEqual(stream["stream"], {
            "log_source": "uvularia_published", "cluster": "example-org", "source": "uvularia",
            "pipeline": "records", "stage": "published", "repo": "Example-Org/example-records"})
        self.assertEqual(json.loads(stream["values"][0][1]), {"records": 3})

    def test_refuses_a_bad_label_and_sends_nothing(self):
        proc = self._push(LE_STAGE="pub-lished")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(_Loki.calls, [])


if __name__ == "__main__":
    unittest.main()
