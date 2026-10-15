# Homework #2: Build an L7 Ralph Loop

**BSE Fellowship — Loop Engineering**

**Assigned:** Week 3, Lecture B
**Due:** Week 4, Lecture A
**Estimated time:** 2–3 hours

## Overview

In Homework #1, you implemented a basic Layer 5 harness that executed tool calls from a mock agent.

Now, we're moving up the Agentic Computing Stack to **Layer 7: Loop**.

Your goal is to write your own `loop.py` L7 orchestrator that runs **Codex or Claude Code headlessly**, evaluates the resulting workspace, and decides whether to launch another invocation.

By the end of this assignment, you should have a working implementation of a **Ralph-style loop**.

### What you are building

In the Agentic Stack model, L7 controls iterative execution and evaluation. Your deliverable is that controller: `loop.py` (or its equivalent). The calculator is the workload used to exercise it. Manually finishing the calculator does not complete this assignment.

This is a bounded teaching version of [Geoffrey Huntley's Ralph technique](https://ghuntley.com/ralph/): repeatedly launch a coding agent with fresh context, carry work forward in files, and use tests as feedback. We add an explicit iteration limit and controller-owned verification to make completion measurable.

```text
L7 controller: task + latest feedback → fresh agent invocation
                        ↑                       ↓
                     retry ← failing tests ← workspace changes
                                                ↓
                                 passing tests → stop successfully
                                 budget spent  → stop unsuccessfully
```

| Layer | Role in this homework |
|---|---|
| L7 Loop | Your program builds prompts, schedules fresh invocations, runs verification, feeds back failures, and decides when to stop. |
| L6 Agent | The existing coding agent reasons about the task and chooses edits and tool calls within one invocation. |
| L5 Harness | The existing CLI/runtime supplies file access, tools, and the execution environment. |
| L4 Model | The existing agent's model supplies inference. |

The CLI is the entry point to the existing L5 harness and L6 agent together. Your Python process sits outside that invocation at L7. The agent may use its own internal reasoning/tool loop, but your `loop.py` owns the outer execution → verification → feedback → retry cycle. Do not replace your controller with a built-in agent loop command, a prompt asking the agent to keep trying, or a direct model API call.

One agent invoked sequentially is sufficient. Coordination here means sequencing agent work and verification; multiple agents, parallel execution, and a new agent framework are not required.

## Learning Objectives

By completing this assignment, you should be able to:

1. Distinguish an agent's internal execution loop (L6) from an external orchestration loop (L7).
2. Programmatically invoke an existing coding agent.
3. Evaluate an agent's work using objective success criteria.
4. Implement retry and termination logic.
5. Understand why an external loop can accomplish tasks that a single agent invocation might fail to complete.

## The Challenge

Build a command-line program that takes a coding task and repeatedly runs a coding agent until the task is completed or a maximum number of iterations is reached.

Your program should implement the following workflow:

1. **Read the task.** Load a task description from a local `TASK.md` file.
2. **Invoke an agent.** Launch an existing coding agent, such as Claude Code or Codex, with the task and relevant feedback.
3. **Evaluate the result.** Run a predefined verification command to determine whether the task has been completed.
4. **Provide feedback.** If verification fails, make the failure information available to the next agent invocation.
5. **Repeat or terminate.** Continue until verification passes or the iteration limit is reached.

The controller, not the agent, must determine when the overall task is complete.

## What's in this package

```text
HOMEWORK.md              this file
loop.py                  starter skeleton: your L7 controller goes here
TASK.md                  the task your loop hands to the agent (provided)
REFLECTION.md            template for your written reflection
package.json             the calculator project's `npm test` entry point
calculator.js            incomplete calculator the agent must finish
test/calculator.test.js  the calculator's test suite (do not edit)
tools/mock_agent.py      deterministic fake agent for offline testing
grader/                  public grader + the fixture project it runs against
```

Requirements: macOS or Linux (Windows users should use WSL), Python 3.10+, Node.js 18+ with `npm`, and an installed, authenticated [Codex CLI](https://developers.openai.com/codex/cli) or Claude Code CLI with access to a model. TypeScript submissions require Node.js 22.6+ and must run with `node --experimental-strip-types loop.ts`. The calculator has no dependencies; no `npm install` is needed.

Run commands from a normal terminal in the assignment folder. Before implementation, `npm test` is expected to fail and `python3 loop.py` raises `NotImplementedError`: these are intentional starter files.

## Requirements

### Part 1: Agent Invocation

Your program must invoke an existing coding agent programmatically in headless (non-interactive) mode. It must not depend on a person entering prompts or clicking Continue between iterations.

You may use Python, TypeScript, JavaScript, or Bash to implement your controller. (The starter is Python; if you choose another language, name your file `loop.ts`, `loop.js`, or `loop.sh` and remove the unused `loop.py` starter. Keep exactly one controller file so the grader selects yours. Substitute your language's runner in the examples below.)

You are **not** expected to build your own L4 model, L5 harness, or L6 agent.

Each iteration should launch a new agent invocation rather than simply asking the same ongoing conversation to continue.

Use a fresh session/context each time: do not use session-resume or conversation-continuation options. Preserve the same project directory and the edits from previous iterations. Rebuild the prompt from the original task, iteration number, and latest verification output; do not replay an ever-growing conversation. The project files are the persistent work state, while the controller carries the latest feedback.

### Part 2: Verification

Your program must execute verification independently of the agent. For this homework the externally supplied command is fixed; a configurable verifier is optional.

For this assignment the command is:

`npm test`

After each agent invocation, execute the command and capture its exit code and output.

- Exit code `0` indicates successful verification.
- A nonzero exit code indicates failed verification.

The agent's own claim that the task is complete does not count as verification.

Run verification even when the agent crashes or times out: it may have changed files before failing. An agent exit code of `0` is not task success, and an agent failure alone does not determine the final result. Only the controller's verification exit code determines whether the workspace passes.

### Part 3: Feedback Loop

When verification fails, the next iteration must receive enough information to understand what went wrong.

At minimum, provide:

- The original task description.
- The verification command's output.
- The current iteration number.

The agent should be able to inspect and modify the existing project files across iterations.

### Part 4: Termination

Your loop must stop when either:

- The verification command succeeds.
- The configured maximum number of iterations is reached.

Your program must not run indefinitely.

If the agent invocation fails or times out, your controller must handle that outcome without crashing or incorrectly reporting success.

### Part 5: Logging

For every iteration, print:

- Iteration number.
- Agent invocation status.
- Verification result.
- Whether the loop will continue or terminate.

You don't need to build a sophisticated logging system. Readable terminal output is sufficient.

## Interface contract (required)

The grader drives your controller from the outside, so your program must follow this contract. The starter `loop.py` already contains the argument parsing and constants for it.

| Item | Requirement |
|---|---|
| Working directory | The controller runs in the project directory. It reads `./TASK.md` and runs `npm test` there. |
| `--max-iterations N` | Maximum number of agent invocations. Default `5`. |
| `AGENT_CMD` env var | The agent command, split like a shell would (`shlex.split`). Default: `codex exec --sandbox workspace-write --skip-git-repo-check`. |
| Passing the prompt | Append your prompt to the agent command as **one final argument**. Do not run it through a shell, and do not assume the prompt is free of quotes, `$`, or backticks. |
| `AGENT_TIMEOUT` env var | Seconds to let one agent invocation run before killing it. Default `600`. |
| Exit code | `0` if and only if verification passed. Nonzero otherwise (iteration limit reached, missing `TASK.md`, etc.). |
| Output | Print readable progress to the terminal as in the example below. Use the words `PASSED` and `FAILED` for verification results, and print the header `[Iteration i/N]` for each iteration. |

`AGENT_CMD` and `AGENT_TIMEOUT` exist so the grader can swap in a fake agent. Your real runs should use the defaults (or your own `AGENT_CMD` if you use a different agent).

## Example Execution

```text
$ python loop.py --max-iterations 5

[Loop] Loading TASK.md
[Loop] Maximum iterations: 5

[Iteration 1/5]
  Starting coding agent...
  Agent finished.
  Running: npm test
  Result: FAILED (3 tests failing)
  Continuing...

[Iteration 2/5]
  Starting coding agent...
  Agent finished.
  Running: npm test
  Result: FAILED (1 test failing)
  Continuing...

[Iteration 3/5]
  Starting coding agent...
  Agent finished.
  Running: npm test
  Result: PASSED

[Loop] Task completed successfully!
[Loop] Total iterations: 3
```

## Testing Your Loop

We provide a small JavaScript project containing an incomplete calculator implementation (`calculator.js`) and a set of automated tests (`test/calculator.test.js`). `TASK.md` instructs the agent to implement the missing functionality.

Your loop should:

1. Launch the agent against the project.
2. Run the provided test suite.
3. Feed any failures back into subsequent iterations.
4. Stop when all tests pass.

### Primary workflow: run a real coding agent

The required integration is a real coding agent. `tools/mock_agent.py` is only a test double for checking the controller; it is not the agent used to complete the calculator.

1. Install and authenticate the [Codex CLI](https://developers.openai.com/codex/cli), or configure another coding agent with `AGENT_CMD`. For Codex, check `codex --version` and `codex login status`; run `codex login` if needed.
2. Implement the TODOs in `loop.py`.
3. From this project directory, capture your first real run:

```bash
# Clear any fake-agent override from earlier testing.
unset AGENT_CMD
set -o pipefail
echo '=== REAL AGENT RUN: Codex CLI ===' > execution.log
echo 'Command: python3 loop.py --max-iterations 5 (default AGENT_CMD)' >> execution.log
python3 loop.py --max-iterations 5 2>&1 | tee -a execution.log
```

Each iteration launches `codex exec --sandbox workspace-write --skip-git-repo-check` with a new prompt. The real agent reads and edits `calculator.js`. Your controller then runs `npm test`, forwards failures to a fresh agent invocation, and repeats until success or the iteration limit. This uses your configured Codex account/model; there is no automatic fallback to the mock.

To use Claude Code instead, install and authenticate its CLI, then select its headless print mode:

```bash
set -o pipefail
export AGENT_CMD='claude --allowedTools "Read,Edit,Write,Glob,Grep,Bash(npm test)" -p'
echo '=== REAL AGENT RUN: Claude Code ===' > execution.log
echo "AGENT_CMD=$AGENT_CMD" >> execution.log
python3 loop.py --max-iterations 5 2>&1 | tee -a execution.log
```

The controller appends the prompt as one final argument. The tool allowance lets Claude read/edit the project and run its tests without an interactive approval prompt. Your controller still runs its own verification afterward. Do not add resume/continue flags for either CLI. See the official [Codex non-interactive documentation](https://developers.openai.com/codex/noninteractive) and [Claude headless documentation](https://code.claude.com/docs/en/headless). Record whichever command you actually used in your run log.

Use a clean copy of the provided calculator project if an earlier run already completed it. Choose one CLI workflow above; you do not need to run both. `pipefail` preserves a failing controller's exit status when output is piped through `tee`.

A successful real run may finish in one iteration. Record unsuccessful results honestly. If access or authentication prevents a real run, record that limitation for instructor review; a mock-only log does not demonstrate real-agent integration.

### Demonstrating retry behavior

Your submission must also demonstrate more than one iteration, with `FAILED → retry → PASSED` within one controller run. If your real-agent run already demonstrates that, it is sufficient. Otherwise, append this controlled offline scenario to the real-agent log:

```bash
cp -r grader/fixture demo_run && cd demo_run
echo 3 > required.txt
echo '=== MOCK RETRY RUN (controller test only) ===' >> ../execution.log
MOCK_MODE=feedback AGENT_CMD="python3 ../tools/mock_agent.py" python3 ../loop.py --max-iterations 5 2>&1 | tee -a ../execution.log
cd .. && rm -rf demo_run
```

The fixture needs three successful agent steps. Its feedback mode refuses further progress unless the next prompt contains the latest verifier token. Do not modify the provided tests or verification command to manufacture a passing result.

### Public grader (offline controller tests)

```bash
python3 grader/public_grader.py
```

The grader runs your controller in temporary fixture projects with the fake agent. It checks invocation, independent verification, feedback, retries, and termination without API access. It does not replace the required real-agent run. **Passing it does not guarantee full marks:** hidden checks and human review of the real run and reflection also count.

## Deliverables

Submit **three files**:

- `loop.py`, `loop.ts`, `loop.js`, or `loop.sh` — your L7 controller.
- `REFLECTION.md` — your written reflection (use the provided template).
- `execution.log` — a labeled real-agent run, plus a mock retry run if the real run completed in one iteration.

Your reflection must answer:

1. What part of your implementation belongs to L7 rather than L6?
2. Why should the controller verify the agent's work instead of trusting the agent's response?
3. What limitations does your current loop have?

Keep each answer to a short paragraph of at least 40 words (at least 120 words across the three answers).

For question 1, explain what starts fresh each iteration, what persists, and which component owns the stop decision. For question 3, discuss what your mock run proves and what still depends on the real agent and the quality of the tests.

### Completion checklist

- The controller works on the grader's unrelated fixture as well as the calculator; it contains no calculator-solving logic.
- Each invocation starts a fresh agent context against the same evolving workspace.
- Failed verification output reaches the next invocation and is refreshed after every attempt.
- Verification, not agent prose or agent exit status, controls success.
- The controller recovers from invocation failures and stops at the iteration budget.
- Your log demonstrates real-agent integration and a retry (real or controlled).

---

## Final Note

The point of this assignment isn't to write a sophisticated AI agent.

It's to recognize that **an agent and the system orchestrating that agent are two different things**.

Your coding agent decides how to approach and execute the coding task. Your Layer 7 controller decides when to invoke the agent, how to evaluate its progress, and whether another iteration is necessary.

That's the foundation of Loop Engineering.
