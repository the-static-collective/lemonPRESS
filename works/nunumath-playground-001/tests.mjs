import assert from "node:assert/strict";
import { specimens, applePair } from "./specimens.js";
import { validateWorld, endpointEquivalent, deltaEquivalent, receiptEquivalent, receiptFor } from "./core.js";

for (const specimen of specimens) {
  assert.equal(validateWorld(specimen.mathal.source).ok, true, `${specimen.id} source malformed`);
  assert.equal(validateWorld(specimen.mathal.target).ok, true, `${specimen.id} target malformed`);
}

assert.equal(applePair.gift.target.F.includes("count:self=2"), true);
assert.equal(applePair.loss.target.F.includes("count:self=2"), true);
assert.equal(receiptEquivalent(applePair.gift, applePair.loss), false);
assert.equal(deltaEquivalent(applePair.gift, applePair.loss), false);

const endpointReceipt = receiptFor(applePair.gift, "endpoint");
assert.deepEqual(endpointReceipt.target, applePair.gift.target);

assert.equal(endpointEquivalent(applePair.gift, applePair.loss), false);

console.log(`ok — ${specimens.length} specimens validated`);
console.log("ok — same scalar count does not collapse gift and loss histories");
