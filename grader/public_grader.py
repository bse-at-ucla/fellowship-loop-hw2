#!/usr/bin/env python3
"""Public grader for Homework #2 (Build Your First Loop).

Usage:

    python3 grader/public_grader.py [--submission DIR] [--verbose]

By default it looks for loop.py / loop.js / loop.ts / loop.sh in the folder that
contains this grader/ directory.

It runs your controller against a tiny fixture project (grader/fixture) using a
deterministic fake agent (tools/mock_agent.py), so it needs no API access.
These checks cover the core behaviors. They are a smoke test, not the full
grade: a larger hidden set of checks is run on submissions.

Works on macOS and Linux. Requires Node.js (for `npm test` in the fixture).
"""

import argparse
import atexit
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

GRADER_DIR = Path(__file__).resolve().parent
ROOT = GRADER_DIR.parent
FIXTURE = GRADER_DIR / "fixture"
MOCK_AGENT = ROOT / "tools" / "mock_agent.py"

LOOP_NAMES = ["loop.py", "loop.js", "loop.ts", "loop.sh"]


# --- Tiny test framework ----------------------------------------------------

class Fail(Exception):
    """Raised by expect() when a check fails."""


def expect(condition: object, message: str) -> None:
    if not condition:
        raise Fail(message)


@dataclass
class Check:
    id: str
    title: str
    fn: Callable[[Path], None]  # takes the loop file path; raises Fail on failure


TESTS: list[Check] = []


def check(check_id: str, title: str):
    def register(fn):
        TESTS.append(Check(check_id, title, fn))
        return fn
    return register


# --- Running a controller against the fixture --------------------------------

_tmp_root: Optional[Path] = None


def tmp_root() -> Path:
    """A scratch directory whose path deliberately contains a space."""
    global _tmp_root
    if _tmp_root is None:
        _tmp_root = Path(tempfile.mkdtemp(prefix="loop grader "))
        atexit.register(shutil.rmtree, _tmp_root, ignore_errors=True)
    return _tmp_root


def runner_for(loop_path: Path) -> list[str]:
    suffix = loop_path.suffix
    if suffix == ".py":
        return [sys.executable, str(loop_path)]
    if suffix == ".js":
        return ["node", str(loop_path)]
    if suffix == ".ts":
        return ["node", "--experimental-strip-types", str(loop_path)]
    if suffix == ".sh":
        return ["bash", str(loop_path)]
    raise SystemExit(f"Don't know how to run {loop_path.name}")


@dataclass
class Run:
    returncode: Optional[int]
    output: str
    elapsed: float
    timed_out: bool
    proj: Path

    def prompt(self, n: int) -> str:
        path = self.proj / ".mock" / f"prompt_{n}.txt"
        return path.read_text() if path.exists() else ""

    @property
    def calls(self) -> int:
        """How many times the agent was launched."""
        state = self.proj / ".mock_state.json"
        if not state.exists():
            return 0
        import json
        return json.loads(state.read_text()).get("calls", 0)

    @property
    def pids(self) -> list[str]:
        d = self.proj / ".mock"
        if not d.exists():
            return []
        return [p.read_text().strip() for p in sorted(d.glob("pid_*.txt"))]

    @property
    def verify_runs(self) -> int:
        log = self.proj / "verify_runs.log"
        return len(log.read_text().splitlines()) if log.exists() else 0

    def section(self, n: int) -> str:
        """The part of the output belonging to iteration n (header to next header)."""
        headers = list(re.finditer(r"Iteration\s+(\d+)\s*/\s*\d+", self.output))
        for i, m in enumerate(headers):
            if int(m.group(1)) == n:
                end = headers[i + 1].start() if i + 1 < len(headers) else len(self.output)
                return self.output[m.start():end]
        return ""


def run_scenario(
    loop_path: Path,
    *,
    required: int = 3,
    max_iter: Optional[int] = 5,
    mode: str = "work",
    crash_on: str = "",
    agent_timeout: str = "30",
    task: Optional[str] = None,
    remove_task: bool = False,
    agent_cmd: Optional[str] = None,
    loop_timeout: float = 90,
) -> Run:
    proj = Path(tempfile.mkdtemp(dir=tmp_root())) / "proj dir"
    shutil.copytree(FIXTURE, proj)
    (proj / "required.txt").write_text(str(required))
    if task is not None:
        (proj / "TASK.md").write_text(task)
    if remove_task:
        (proj / "TASK.md").unlink()

    env = {k: v for k, v in os.environ.items()
           if k not in ("AGENT_CMD", "AGENT_TIMEOUT") and not k.startswith("MOCK_")}
    env["AGENT_CMD"] = agent_cmd or shlex.join([sys.executable, str(MOCK_AGENT)])
    env["AGENT_TIMEOUT"] = agent_timeout
    env["MOCK_MODE"] = mode
    env["MOCK_CRASH_ON"] = crash_on

    cmd = runner_for(loop_path)
    if max_iter is not None:
        cmd += ["--max-iterations", str(max_iter)]

    start = time.time()
    proc = subprocess.Popen(
        cmd, cwd=proj, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace", start_new_session=True,
    )
    timed_out = False
    try:
        out, _ = proc.communicate(timeout=loop_timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, _ = proc.communicate()
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # clean up stray children
        except (ProcessLookupError, PermissionError):
            pass
    return Run(None if timed_out else proc.returncode, out or "", time.time() - start, timed_out, proj)


def iteration_mentioned(prompt: str, n: int, total: int = 5) -> bool:
    """Does the prompt tell the agent which iteration it is on?"""
    pats = [rf"iteration\s*(number\s*)?:?\s*#?{n}\b", rf"\b{n}\s*/\s*{total}\b", rf"\b{n}\s+of\s+{total}\b",
            rf"attempt\s*#?{n}\b"]
    return any(re.search(p, prompt, re.IGNORECASE) for p in pats)


# --- Public checks ----------------------------------------------------------

@check("A1", "launches the agent from AGENT_CMD, passing a prompt as the final argument")
def a1(loop: Path) -> None:
    r = run_scenario(loop, required=1, max_iter=3)
    expect(not r.timed_out, "the controller hung")
    expect(r.calls >= 1, "the agent was never launched (is AGENT_CMD being used?)\n" + r.output[-600:])
    expect(len(r.prompt(1).strip()) > 0, "the agent was launched but received an empty prompt")
    expect(r.returncode == 0, f"expected exit code 0 after a passing run, got {r.returncode}")


@check("A2", "each iteration is a new agent process (one launch per iteration)")
def a2(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5)
    expect(r.calls == 3, f"expected 3 agent launches for 3 iterations, saw {r.calls}")
    expect(len(set(r.pids)) == 3, "iterations did not each get a separate agent process")


@check("B1", "does not report success just because the agent says it's done")
def b1(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=3, mode="liar")
    expect(not r.timed_out, "the controller hung")
    expect(r.calls >= 1 and r.verify_runs >= 1,
           "the controller never launched the agent and ran `npm test` (a loop that does nothing doesn't count)")
    expect(r.returncode not in (0, None), "exit code was 0 even though `npm test` never passed")
    expect(not re.search(r"completed successfully|task complete", r.output, re.IGNORECASE),
           "the output claims success even though `npm test` never passed")


@check("B2", "stops with exit code 0 as soon as `npm test` passes")
def b2(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5)
    expect(r.returncode == 0, f"expected exit code 0, got {r.returncode}\n" + r.output[-600:])
    expect(r.calls == 3, f"expected exactly 3 agent launches (stop on first pass), saw {r.calls}")


@check("C1", "every prompt contains the original task text")
def c1(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5)
    for n in (1, 2, 3):
        expect("FIXTURE-TASK-MARKER-7f3a" in r.prompt(n), f"the prompt for iteration {n} is missing the task text")


@check("C2", "the verification output from a failed run reaches the next iteration's prompt")
def c2(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5, mode="feedback")
    expect(r.returncode == 0 and r.calls == 3,
           "the feedback-dependent agent must reach success in 3 invocations; forward the latest verifier output and preserve workspace changes")
    expect("progress 1 < required 3" in r.prompt(2),
           "iteration 2's prompt doesn't contain the failing `npm test` output from iteration 1")


@check("C3", "every prompt tells the agent the current iteration number")
def c3(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5)
    for n in (1, 2, 3):
        expect(iteration_mentioned(r.prompt(n), n), f"the prompt for iteration {n} doesn't state the iteration number")


@check("D1", "stops at --max-iterations and exits nonzero")
def d1(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=4, mode="nothing")
    expect(not r.timed_out, "the controller did not terminate")
    expect(r.calls == 4, f"expected exactly 4 agent launches, saw {r.calls}")
    expect(r.returncode not in (0, None), "expected a nonzero exit code when the iteration limit is hit")


@check("D2", "survives an agent crash and keeps going")
def d2(loop: Path) -> None:
    r = run_scenario(loop, required=2, max_iter=5, crash_on="1")
    expect("Traceback" not in r.output, "the controller crashed with a traceback\n" + r.output[-800:])
    expect(r.returncode == 0, f"expected the loop to recover and pass, got exit code {r.returncode}")
    expect(r.calls == 3, f"expected 3 agent launches (crash, then 2 working runs), saw {r.calls}")


@check("E1", "prints an [Iteration i/N] header for every iteration")
def e1(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5)
    found = [int(m) for m in re.findall(r"Iteration\s+(\d+)\s*/\s*5", r.output)]
    expect(found[:3] == [1, 2, 3], f"expected headers for iterations 1, 2, 3 (as 'Iteration i/5'), found {found}")


@check("E3", "prints PASSED / FAILED for each verification result")
def e3(loop: Path) -> None:
    r = run_scenario(loop, required=3, max_iter=5)
    failed = len(re.findall(r"\bFAILED\b", r.output))
    passed = len(re.findall(r"\bPASSED\b", r.output))
    expect(failed >= 2, f"expected a FAILED line for each of the 2 failing iterations, found {failed}")
    expect(passed >= 1, "expected a PASSED line for the passing iteration")


# --- Entry point ------------------------------------------------------------

def find_loop(submission: Path) -> Path:
    found = [submission / n for n in LOOP_NAMES if (submission / n).exists()]
    if not found:
        raise SystemExit(f"No loop.py / loop.js / loop.ts / loop.sh found in {submission}")
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Public grader for Homework #2")
    parser.add_argument("--submission", type=Path, default=ROOT, help="folder containing your loop file")
    parser.add_argument("--verbose", action="store_true", help="show the controller's output for failed checks")
    args = parser.parse_args()

    if not shutil.which("npm"):
        raise SystemExit("npm not found: the fixture project runs `npm test`")

    loop = find_loop(args.submission.resolve())
    print(f"Public grader — {loop.name}\n")

    passed = 0
    for t in TESTS:
        try:
            t.fn(loop)
        except Fail as e:
            print(f"  [FAIL] {t.id}  {t.title}")
            for line in str(e).splitlines():
                print(f"           {line}")
        except Exception as e:  # a bug in the grader or an unexpected environment problem
            print(f"  [ERROR] {t.id}  {t.title}\n           {type(e).__name__}: {e}")
        else:
            passed += 1
            print(f"  [PASS] {t.id}  {t.title}")

    print(f"\n{passed}/{len(TESTS)} public checks passed.")

    missing = [n for n in ("REFLECTION.md", "execution.log") if not (args.submission / n).exists()]
    if missing:
        print(f"Reminder: you still need to include {', '.join(missing)} in your submission.")
    print("Passing every public check does not guarantee full marks: hidden checks and a human read of your reflection also count.")
    return 0 if passed == len(TESTS) else 1


if __name__ == "__main__":
    sys.exit(main())
