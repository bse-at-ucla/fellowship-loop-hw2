"use strict";

// A small calculator library. Only add() and subtract() are finished.

function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

function multiply(a, b) {
  throw new Error("not implemented");
}

function divide(a, b) {
  throw new Error("not implemented");
}

function power(base, exponent) {
  throw new Error("not implemented");
}

function modulo(a, b) {
  throw new Error("not implemented");
}

function sqrt(n) {
  throw new Error("not implemented");
}

function evaluate(expression) {
  throw new Error("not implemented");
}

module.exports = { add, subtract, multiply, divide, power, modulo, sqrt, evaluate };
