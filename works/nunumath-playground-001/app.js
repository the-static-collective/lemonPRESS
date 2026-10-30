import { specimens, applePair } from "./specimens.js";
import { receiptFor, deltaEquivalent, receiptEquivalent } from "./core.js";

const $ = (sel) => document.querySelector(sel);
const pretty = (x) => JSON.stringify(x, null, 2);
const roleBlock = (world, key) => key === "R"
  ? world.R.map(r => `${r.id}: ${r.type}(${r.participants.join(", ")})`).join("\n") || "∅"
  : world[key].join("\n") || "∅";

const select = $("#specimen");
for (const s of specimens) {
  const o = document.createElement("option");
  o.value = s.id;
  o.textContent = s.title;
  select.appendChild(o);
}

function render() {
  const s = specimens.find(x => x.id === select.value) ?? specimens[0];
  const m = s.mathal;
  $("#title").textContent = s.title;
  $("#conventional").textContent = s.conventional;
  $("#note").textContent = s.note;
  $("#warrant").textContent = m.receipt.warrant;
  $("#coarse").textContent = `δ = (${m.coarse.join(", ")})`;
  $("#source-id").textContent = m.source.id;
  $("#target-id").textContent = m.target.id;
  for (const role of ["F", "I", "R"]) {
    $(`#source-${role}`).textContent = roleBlock(m.source, role);
    $(`#target-${role}`).textContent = roleBlock(m.target, role);
  }
  $("#delta").textContent = pretty(m.delta);
  $("#receipt").textContent = pretty(receiptFor(m, $("#receipt-mode").value));
  $("#questions").innerHTML = m.receipt.questions.map(q => `<li>${q}</li>`).join("");
}

select.addEventListener("change", render);
$("#receipt-mode").addEventListener("change", render);

$("#compare-apples").addEventListener("click", () => {
  const gift = applePair.gift;
  const loss = applePair.loss;
  $("#comparison").textContent = pretty({
    same_scalar_count: gift.target.F.includes("count:self=2") && loss.target.F.includes("count:self=2"),
    exact_delta_equivalent: deltaEquivalent(gift, loss),
    receipt_equivalent: receiptEquivalent(gift, loss),
    gift_trace: gift.receipt.trace,
    loss_trace: loss.receipt.trace,
  });
});

select.value = specimens[0].id;
render();
