#!/usr/bin/env python3
"""A deterministic fake coding agent for testing an L7 loop offline.

Usage (the way a controller launches it):

    python3 mock_agent.py "<prompt>"

It behaves like a very simple agent that works inside the current directory
(the fixture project in grader/fixture). Each invocation is a fresh process;
the only memory it has is the files it leaves on disk, exactly like a real
coding agent between loop iterations.

Behavior is controlled by environment variables:

    MOCK_MODE      work (default)  make one unit of progress per invocation
                   feedback        after first progress, require latest verifier token
                   liar            claim success, change nothing
                   nothing         change nothing, claim nothing
                   hang            sleep for five minutes (to test timeouts)
    MOCK_CRASH_ON  comma-separated invocation numbers on which to exit 1
                   before doing any work, e.g. "1" or "1,3"

Files it writes in the current directory:

    progress.txt            progress counter that grader/fixture/check.js reads
    .mock_state.json        invocation counter (the mock's only memory)
    .mock/prompt_<n>.txt    the exact prompt received on invocation n
    .mock/pid_<n>.txt       the process id of invocation n
"""

import json
import os
import sys
import time
from pathlib import Path

CWD = Path.cwd()
STATE = CWD / ".mock_state.json"
RECORD_DIR = CWD / ".mock"


def main() -> int:
    prompt = sys.argv[-1] if len(sys.argv) > 1 else ""

    state = json.loads(STATE.read_text()) if STATE.exists() else {"calls": 0}
    state["calls"] += 1
    call = state["calls"]
    STATE.write_text(json.dumps(state))

    RECORD_DIR.mkdir(exist_ok=True)
    (RECORD_DIR / f"prompt_{call}.txt").write_text(prompt)
    (RECORD_DIR / f"pid_{call}.txt").write_text(str(os.getpid()))

    crash_on = {int(x) for x in os.environ.get("MOCK_CRASH_ON", "").split(",") if x.strip()}
    if call in crash_on:
        print(f"mock agent: simulated crash on invocation {call}", file=sys.stderr)
        return 1

    mode = os.environ.get("MOCK_MODE", "work")
    if mode == "hang":
        time.sleep(300)
        return 0
    if mode == "liar":
        print("All done! I implemented everything and all tests pass.")
        return 0
    if mode == "nothing":
        return 0

    progress_file = CWD / "progress.txt"
    progress = int(progress_file.read_text().strip() or 0) if progress_file.exists() else 0
    if mode == "feedback" and progress > 0:
        token_file = CWD / ".feedback_token"
        token = token_file.read_text().strip() if token_file.exists() else ""
        if not token or token not in prompt:
            print("mock agent: latest verification feedback is missing; no progress")
            return 0
    progress_file.write_text(str(progress + 1))
    print(f"mock agent: progress is now {progress + 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
