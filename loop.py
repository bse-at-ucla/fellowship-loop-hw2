#!/usr/bin/env python3
"""Homework #2 starter: your L7 orchestrator around headless Codex/Claude.

Run from the project directory:

    python3 loop.py --max-iterations 5

What is already done for you: argument parsing, the configuration constants,
and the overall shape of main(). What you must write: every function marked
TODO. Read HOMEWORK.md ("Interface contract") before you start; the grader
relies on it.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

# --- Configuration (part of the interface contract; do not rename) ---------

DEFAULT_AGENT_CMD = "codex exec --sandbox workspace-write --skip-git-repo-check"
# Alternative AGENT_CMD: claude --allowedTools "Read,Edit,Write,Glob,Grep,Bash(npm test)" -p
# Append the prompt as one argument; never resume the previous CLI session.
VERIFY_CMD = "npm test"
TASK_FILE = "TASK.md"

AGENT_CMD = os.environ.get("AGENT_CMD", DEFAULT_AGENT_CMD)
AGENT_TIMEOUT = int(os.environ.get("AGENT_TIMEOUT", "600"))  # seconds


# --- Pieces you implement ---------------------------------------------------

def load_task(path: str = TASK_FILE) -> str:
    """Return the contents of TASK.md.

    TODO: If the file is missing, don't crash with a traceback. Print a clear
    message and make main() exit with a nonzero status.
    """
    raise NotImplementedError


def build_prompt(task: str, iteration: int, max_iterations: int, feedback: str | None) -> str:
    """Build the prompt for one agent invocation.

    TODO: Include, at minimum:
      - the original task text,
      - the current iteration number,
      - on iterations after the first, the output of the failed verification.
    Think about how much output is too much to paste into a prompt.
    """
    raise NotImplementedError


def run_agent(prompt: str) -> tuple[str, int | None]:
    """Launch one fresh agent process/session in the same workspace and wait for it.

    Returns (status, returncode), where status is a short human-readable
    string such as "finished", "failed (exit code 1)", or "timed out".

    TODO:
      - Split AGENT_CMD with shlex.split and append `prompt` as ONE final
        argument. Do not use shell=True.
      - Enforce AGENT_TIMEOUT.
      - Do not resume a previous conversation or reset the project files.
      - If the agent can't be started (e.g. the binary doesn't exist), or
        exits nonzero, or times out, report that through the return value.
        Never raise out of this function. Agent status is diagnostic; main()
        must still run verification, which alone decides task success.
    """
    raise NotImplementedError


def run_verification() -> tuple[int, str]:
    """Run VERIFY_CMD and return (exit_code, combined stdout+stderr).

    TODO: The exit code is the ONLY thing that decides pass/fail.
    """
    raise NotImplementedError


# --- The loop ---------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Run a coding agent in a verify-and-retry loop.")
    parser.add_argument("--max-iterations", type=int, default=5,
                        help="maximum number of agent invocations (default: 5)")
    args = parser.parse_args()

    print(f"[Loop] Loading {TASK_FILE}")
    task = load_task()  # TODO: handle a missing file (see load_task)
    print(f"[Loop] Maximum iterations: {args.max_iterations}")

    # TODO: for each iteration up to args.max_iterations:
    #   1. print the "[Iteration i/N]" header
    #   2. build the prompt and run the agent; print its status
    #   3. run verification; print PASSED / FAILED
    #   4. stop with exit code 0 if verification passed
    #   5. otherwise remember the output as feedback for the next iteration,
    #      and print whether the loop is continuing or terminating
    # After the loop: report that the iteration limit was reached and return
    # a nonzero exit code.
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
