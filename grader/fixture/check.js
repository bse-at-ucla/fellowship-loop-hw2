"use strict";

// The fixture's "test suite". Passes once progress.txt reaches required.txt.
// Every run is appended to verify_runs.log so the grader can count verifications.

const fs = require("node:fs");

function readInt(file, fallback) {
  try {
    const n = parseInt(fs.readFileSync(file, "utf8").trim(), 10);
    return Number.isNaN(n) ? fallback : n;
  } catch {
    return fallback;
  }
}

const required = readInt("required.txt", 3);
const progress = readInt("progress.txt", 0);

fs.appendFileSync("verify_runs.log", `progress=${progress} required=${required}\n`);

if (progress < required) {
  const failing = required - progress;
  console.log(`check: progress ${progress} < required ${required}`);
  console.log(`${failing} check(s) failing`);
  if (process.env.MOCK_MODE === "feedback") {
    // A new token on EVERY failure makes stale or omitted feedback ineffective.
    const token = `VERIFIER-FEEDBACK-${require("node:crypto").randomUUID()}`;
    fs.writeFileSync(".feedback_token", token);
    console.log(`Include this diagnostic in the next agent prompt: ${token}`);
  }
  process.exit(1);
}

console.log(`check: all ${required} steps complete`);
process.exit(0);
