export const ROLE_KEYS = ["F", "I", "R"];

const clone = (value) => JSON.parse(JSON.stringify(value));
const uniq = (xs) => [...new Set(xs)];
const sorted = (xs) => [...xs].sort();
const stableRelation = (r) => JSON.stringify({
  id: r.id,
  type: r.type,
  participants: [...r.participants],
  warrant: r.warrant ?? null,
});

export function normalizeWorld(world) {
  return {
    id: world.id ?? "world",
    label: world.label ?? world.id ?? "world",
    addresses: uniq(world.addresses ?? []),
    F: uniq(world.F ?? []),
    I: uniq(world.I ?? []),
    R: (world.R ?? []).map(r => ({
      id: r.id,
      type: r.type,
      participants: [...(r.participants ?? [])],
      ...(r.warrant ? { warrant: r.warrant } : {}),
    })),
  };
}

export function validateWorld(input) {
  const world = normalizeWorld(input);
  const errors = [];
  const addressSet = new Set(world.addresses);
  const overlap = world.F.filter(x => world.I.includes(x));

  if (overlap.length) errors.push(`strict FIR violation: F ∩ I contains ${overlap.join(", ")}`);
  for (const role of ["F", "I"]) {
    for (const x of world[role]) {
      if (!addressSet.has(x)) errors.push(`${role} item is not addressable: ${x}`);
    }
  }

  const relationIds = new Set();
  for (const r of world.R) {
    if (!r.id || !r.type) errors.push("every relation needs id and type");
    if (relationIds.has(r.id)) errors.push(`duplicate relation id: ${r.id}`);
    relationIds.add(r.id);
    for (const p of r.participants) {
      if (!addressSet.has(p)) errors.push(`relation participant is not addressable: ${p}`);
    }
  }

  return { ok: errors.length === 0, errors, world };
}

function relationMap(R) {
  return new Map(R.map(r => [stableRelation(r), r]));
}

export function fineDelta(sourceInput, targetInput) {
  const s = validateWorld(sourceInput);
  const t = validateWorld(targetInput);
  if (!s.ok || !t.ok) throw new Error(`invalid world(s): ${[...s.errors, ...t.errors].join("; ")}`);

  const added = (a, b) => sorted(b.filter(x => !a.includes(x)));
  const sR = relationMap(s.world.R);
  const tR = relationMap(t.world.R);

  return {
    F_plus: added(s.world.F, t.world.F),
    F_minus: added(t.world.F, s.world.F),
    I_plus: added(s.world.I, t.world.I),
    I_minus: added(t.world.I, s.world.I),
    R_plus: [...tR.keys()].filter(k => !sR.has(k)).map(k => tR.get(k)),
    R_minus: [...sR.keys()].filter(k => !tR.has(k)).map(k => sR.get(k)),
  };
}

export function coarseDelta(delta) {
  return [
    delta.F_plus.length,
    delta.F_minus.length,
    delta.I_plus.length,
    delta.I_minus.length,
    delta.R_plus.length,
    delta.R_minus.length,
  ];
}

export function worldBody(worldInput) {
  const { world } = validateWorld(worldInput);
  return JSON.stringify({
    F: sorted(world.F),
    I: sorted(world.I),
    R: world.R.map(stableRelation).sort(),
  });
}

export function deriveMathal({ id, label, source, target, warrant, admissibility = [], trace = [], questions = [] }) {
  const s = validateWorld(source);
  const t = validateWorld(target);
  if (!s.ok || !t.ok) throw new Error(`cannot derive mathal from malformed world: ${[...s.errors, ...t.errors].join("; ")}`);
  const delta = fineDelta(s.world, t.world);
  return {
    id,
    label,
    source: clone(s.world),
    target: clone(t.world),
    delta,
    coarse: coarseDelta(delta),
    admissibility: [...admissibility],
    receipt: {
      mathal: id,
      source: s.world.id,
      target: t.world.id,
      warrant,
      delta: clone(delta),
      trace: [...trace],
      questions: [...questions],
    },
  };
}

export function endpointEquivalent(a, b) {
  return worldBody(a.target) === worldBody(b.target);
}

export function deltaEquivalent(a, b) {
  return JSON.stringify(a.delta) === JSON.stringify(b.delta);
}

export function receiptEquivalent(a, b) {
  return JSON.stringify(a.receipt) === JSON.stringify(b.receipt);
}

export function receiptFor(mathal, questionClass) {
  if (questionClass === "endpoint") return { target: clone(mathal.target) };
  if (questionClass === "delta") return { source: mathal.source.id, target: mathal.target.id, delta: clone(mathal.delta) };
  if (questionClass === "history") return clone(mathal.receipt);
  throw new Error(`unknown receipt policy: ${questionClass}`);
}
