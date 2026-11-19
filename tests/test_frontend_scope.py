"""Regression test: the archive script must coexist with other global names."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NODE_CHECK = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      textContent: "", hidden: true, style: {setProperty() {}},
      addEventListener() {}, setAttribute() {}, replaceChildren() {},
      getBoundingClientRect() { return {height: 80, bottom: 80}; },
      querySelectorAll() { return []; }
    });
  }
  return elements.get(id);
}
const context = vm.createContext({
  document: {
    getElementById: element, querySelectorAll() { return []; },
    documentElement: {style: {setProperty() {}}}
  },
  window: {addEventListener() {}, location: {hash: ""}},
  ResizeObserver: class { observe() {} },
  fetch: async () => ({ok: true, json: async () => ({
    meta: {questionCount: 0}, questions: []
  })}),
  console
});

// Reproduce a separate script owning these common global identifiers.
vm.runInContext("const get = () => {}; const state = {};", context);
vm.runInContext(fs.readFileSync("site/app.js", "utf8"), context);
setImmediate(() => {
  assert.equal(elements.get("result-count").textContent, "0 shown");
  assert.equal(elements.get("poll-count").textContent, 0);
});
"""


class FrontendScopeTests(unittest.TestCase):
    def test_existing_global_identifiers_do_not_prevent_startup(self):
        result = subprocess.run(
            ["node", "-e", NODE_CHECK],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
