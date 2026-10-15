"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const calc = require("../calculator.js");

test("add", () => {
  assert.equal(calc.add(2, 3), 5);
  assert.equal(calc.add(-2, 3), 1);
  assert.equal(calc.add(0.5, 0.25), 0.75);
});

test("subtract", () => {
  assert.equal(calc.subtract(5, 3), 2);
  assert.equal(calc.subtract(3, 5), -2);
});

test("multiply", () => {
  assert.equal(calc.multiply(4, 5), 20);
  assert.equal(calc.multiply(-3, 6), -18);
  assert.equal(calc.multiply(7, 0), 0);
});

test("divide", () => {
  assert.equal(calc.divide(10, 2), 5);
  assert.equal(calc.divide(7, 2), 3.5);
  assert.equal(calc.divide(-9, 3), -3);
});

test("divide by zero throws", () => {
  assert.throws(() => calc.divide(1, 0), Error);
});

test("power", () => {
  assert.equal(calc.power(2, 10), 1024);
  assert.equal(calc.power(5, 0), 1);
  assert.equal(calc.power(2, -1), 0.5);
});

test("modulo", () => {
  assert.equal(calc.modulo(10, 3), 1);
  assert.equal(calc.modulo(9, 3), 0);
  assert.equal(calc.modulo(-7, 3), -1);
});

test("modulo by zero throws", () => {
  assert.throws(() => calc.modulo(5, 0), Error);
});

test("sqrt", () => {
  assert.equal(calc.sqrt(16), 4);
  assert.equal(calc.sqrt(0), 0);
  assert.ok(Math.abs(calc.sqrt(2) - 1.4142135623) < 1e-9);
});

test("sqrt of a negative number throws", () => {
  assert.throws(() => calc.sqrt(-1), Error);
});

test("evaluate: single numbers and whitespace", () => {
  assert.equal(calc.evaluate("42"), 42);
  assert.equal(calc.evaluate("  3.5  "), 3.5);
  assert.equal(calc.evaluate(" 1 +   2 "), 3);
});

test("evaluate: operator precedence", () => {
  assert.equal(calc.evaluate("2 + 3 * 4"), 14);
  assert.equal(calc.evaluate("2 * 3 + 4"), 10);
  assert.equal(calc.evaluate("10 - 4 / 2"), 8);
});

test("evaluate: left associativity", () => {
  assert.equal(calc.evaluate("10 - 3 - 2"), 5);
  assert.equal(calc.evaluate("100 / 10 / 5"), 2);
  assert.equal(calc.evaluate("2 * 3 / 4"), 1.5);
});

test("evaluate: parentheses", () => {
  assert.equal(calc.evaluate("(2 + 3) * 4"), 20);
  assert.equal(calc.evaluate("2 * (3 + 4) * 5"), 70);
  assert.equal(calc.evaluate("((1 + 2) * (3 + 4))"), 21);
});

test("evaluate: unary minus", () => {
  assert.equal(calc.evaluate("-5"), -5);
  assert.equal(calc.evaluate("-5 + 10"), 5);
  assert.equal(calc.evaluate("3 * -2"), -6);
  assert.equal(calc.evaluate("-(2 + 3)"), -5);
  assert.equal(calc.evaluate("2 - -3"), 5);
});

test("evaluate: decimals", () => {
  assert.ok(Math.abs(calc.evaluate("0.1 + 0.2") - 0.3) < 1e-9);
  assert.equal(calc.evaluate("1.5 * 4"), 6);
});

test("evaluate: division by zero throws", () => {
  assert.throws(() => calc.evaluate("1 / 0"), Error);
  assert.throws(() => calc.evaluate("5 / (3 - 3)"), Error);
});

test("evaluate: malformed input throws", () => {
  assert.throws(() => calc.evaluate(""), Error);
  assert.throws(() => calc.evaluate("2 +"), Error);
  assert.throws(() => calc.evaluate("(1 + 2"), Error);
  assert.throws(() => calc.evaluate("1 + 2)"), Error);
  assert.throws(() => calc.evaluate("2 $ 3"), Error);
  assert.throws(() => calc.evaluate("1 2"), Error);
});

test("evaluate: does not execute code", () => {
  assert.throws(() => calc.evaluate("process.exit(0)"), Error);
  assert.throws(() => calc.evaluate("require('fs')"), Error);
});
