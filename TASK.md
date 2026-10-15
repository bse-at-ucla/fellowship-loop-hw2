# Task: Finish the calculator

This directory contains a small JavaScript calculator in `calculator.js` and a
test suite in `test/calculator.test.js`. The calculator is incomplete: `add` and
`subtract` work, but the rest of the module throws "not implemented".

## Goal

Implement everything in `calculator.js` so that `npm test` passes.

## What to implement

- `multiply(a, b)`
- `divide(a, b)`: throw an `Error` when `b` is `0`
- `power(base, exponent)`
- `modulo(a, b)`: throw an `Error` when `b` is `0`
- `sqrt(n)`: throw an `Error` when `n` is negative
- `evaluate(expression)`: evaluate an arithmetic expression given as a string.
  It must support `+`, `-`, `*`, `/`, parentheses, decimal numbers, unary minus,
  and arbitrary whitespace, with standard operator precedence (`*` and `/` bind
  tighter than `+` and `-`; operators of equal precedence are left-associative).
  It must throw an `Error` on malformed input and on division by zero.
  Do not use `eval`, `Function`, or any other way of executing the string as code.

## Rules

- Only edit `calculator.js`.
- Do not modify anything in `test/`, and do not modify `package.json`.
- Do not add dependencies.
- Read the tests to see the exact behavior expected. Run `npm test` to check your work.
