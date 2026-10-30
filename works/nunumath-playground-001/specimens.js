import { deriveMathal } from "./core.js";

const R = (id, type, participants, warrant) => ({ id, type, participants, ...(warrant ? { warrant } : {}) });

const applesAddresses = [
  "self", "neighbor", "apple:a", "apple:b", "apple:c",
  "count:self=3", "count:self=2", "proposal:give-c", "event:give-c",
];

const applesSource = {
  id: "apples:t0",
  label: "Three apples before the gift",
  addresses: applesAddresses,
  F: ["count:self=3"],
  I: ["proposal:give-c"],
  R: [
    R("own:a", "possesses", ["self", "apple:a"]),
    R("own:b", "possesses", ["self", "apple:b"]),
    R("own:c", "possesses", ["self", "apple:c"]),
  ],
};

const applesGiftTarget = {
  id: "apples:t1-gift",
  label: "Two apples after giving one away",
  addresses: applesAddresses,
  F: ["count:self=2", "event:give-c"],
  I: [],
  R: [
    R("own:a", "possesses", ["self", "apple:a"]),
    R("own:b", "possesses", ["self", "apple:b"]),
    R("own:c-neighbor", "possesses", ["neighbor", "apple:c"]),
    R("gift:c", "gave", ["self", "apple:c", "neighbor"]),
  ],
};

const applesLostTarget = {
  id: "apples:t1-lost",
  label: "Two apples after losing one",
  addresses: [...applesAddresses, "event:lose-c"],
  F: ["count:self=2", "event:lose-c"],
  I: [],
  R: [
    R("own:a", "possesses", ["self", "apple:a"]),
    R("own:b", "possesses", ["self", "apple:b"]),
  ],
};

export const specimens = [
  {
    id: "APPLES-GIFT-001",
    title: "Three apples → give one away",
    conventional: "3 − 1 = 2",
    note: "Arithmetic gets the endpoint count right. FIR keeps the proposal, transfer relation, changed possession, and warrant addressable.",
    mathal: deriveMathal({
      id: "APPLES-GIFT-001",
      label: "Give apple:c to neighbor",
      source: applesSource,
      target: applesGiftTarget,
      warrant: "declared toy event: apple:c was transferred to neighbor",
      admissibility: ["apple:c is possessed by self at source", "neighbor and apple:c are addressable"],
      trace: ["proposal:give-c active", "gift executed", "count recomputed as 2", "possession relation retyped"],
      questions: ["How many apples remain?", "Where did apple:c go?", "Was the path a gift or a loss?"],
    }),
  },
  {
    id: "APPLES-LOSS-001",
    title: "Three apples → lose one",
    conventional: "3 − 1 = 2",
    note: "Same numerical endpoint as the gift. Different relation structure and receipt.",
    mathal: deriveMathal({
      id: "APPLES-LOSS-001",
      label: "Lose apple:c",
      source: applesSource,
      target: applesLostTarget,
      warrant: "declared toy event: apple:c left possession with recipient unknown",
      trace: ["proposal:give-c was not executed", "apple:c lost", "count recomputed as 2"],
      questions: ["How many apples remain?", "Where did apple:c go?", "Was the path a gift or a loss?"],
    }),
  },
  {
    id: "DEBT-PAY-001",
    title: "Debt: pay $20 on a $100 obligation",
    conventional: "100 − 20 = 80",
    note: "The number 80 is not enough to say whether debt was paid, forgiven, disputed, or re-denominated.",
    mathal: deriveMathal({
      id: "DEBT-PAY-001",
      label: "Partial payment",
      source: {
        id: "debt:t0",
        addresses: ["debtor", "creditor", "debt=100", "debt=80", "payment=20"],
        F: ["debt=100"], I: ["payment=20"],
        R: [R("owes:100", "owes", ["debtor", "creditor", "debt=100"])],
      },
      target: {
        id: "debt:t1",
        addresses: ["debtor", "creditor", "debt=100", "debt=80", "payment=20"],
        F: ["debt=80", "payment=20"], I: [],
        R: [R("owes:80", "owes", ["debtor", "creditor", "debt=80"]), R("paid:20", "paid", ["debtor", "creditor", "payment=20"])],
      },
      warrant: "toy ledger entry: $20 payment admitted",
      trace: ["payment proposed", "payment admitted", "obligation relation updated"],
      questions: ["What balance remains?", "Why did it change?"],
    }),
  },
  {
    id: "MISSING-INFO-001",
    title: "Missing information: the count is proposed, not admitted",
    conventional: "?",
    note: "FIR can hold an answer-shaped object in I without laundering it into F.",
    mathal: deriveMathal({
      id: "MISSING-INFO-001",
      label: "Generate candidate count without promotion",
      source: { id: "missing:t0", addresses: ["box", "candidate:12"], F: [], I: [], R: [] },
      target: { id: "missing:t1", addresses: ["box", "candidate:12"], F: [], I: ["candidate:12"], R: [] },
      warrant: "generation only; no counting or observation warrant supplied",
      trace: ["candidate 12 generated", "promotion refused: warrant absent"],
      questions: ["What is available to consider?", "What is actually admitted?"],
    }),
  },
  {
    id: "WITNESSES-001",
    title: "Contradictory witnesses: preserve source-indexed claims",
    conventional: "one event, two claims",
    note: "The first-course strict world cannot admit the same judgment-token into F and I at once; source-indexed addresses keep the conflict visible without pretending it is resolved.",
    mathal: deriveMathal({
      id: "WITNESSES-001",
      label: "Register conflicting source claims",
      source: { id: "witness:t0", addresses: ["w1", "w2", "claim:w1=red", "claim:w2=blue", "event"], F: [], I: [], R: [] },
      target: {
        id: "witness:t1",
        addresses: ["w1", "w2", "claim:w1=red", "claim:w2=blue", "event"],
        F: [], I: ["claim:w1=red", "claim:w2=blue"],
        R: [R("said:w1", "asserted-about", ["w1", "claim:w1=red", "event"]), R("said:w2", "asserted-about", ["w2", "claim:w2=blue", "event"])],
      },
      warrant: "direct registration of two attributed claims; truth of either claim remains unadmitted",
      trace: ["claim from w1 registered", "claim from w2 registered", "conflict retained"],
      questions: ["Who said what?", "Has either color claim been admitted?"],
    }),
  },
  {
    id: "REMIX-001",
    title: "Song remix: derivative relation without identity collapse",
    conventional: "song A → remix B",
    note: "The remix can become an admitted artifact while the derivation relation remains separately typed.",
    mathal: deriveMathal({
      id: "REMIX-001",
      label: "Render and admit a remix",
      source: { id: "remix:t0", addresses: ["song:A", "remix:B", "proposal:render-B"], F: ["song:A"], I: ["proposal:render-B"], R: [] },
      target: {
        id: "remix:t1",
        addresses: ["song:A", "remix:B", "proposal:render-B"],
        F: ["song:A", "remix:B"], I: [],
        R: [R("derived:B<-A", "derived-from", ["remix:B", "song:A"])],
      },
      warrant: "toy render receipt: remix:B exists as an addressable output",
      trace: ["render proposed", "render completed", "remix admitted", "derivation relation recorded"],
      questions: ["Does B exist?", "Is B identical to A?", "What ancestry is retained?"],
    }),
  },
  {
    id: "ROOM-ENTRY-001",
    title: "A person enters a room",
    conventional: "outside → inside",
    note: "Endpoint location can match while route, permission, escort, timing, and witness differ. The first slice keeps only the relation change plus a trace field.",
    mathal: deriveMathal({
      id: "ROOM-ENTRY-001",
      label: "Enter room through declared door",
      source: {
        id: "room:t0",
        addresses: ["person", "room", "door:north", "outside"], F: [], I: [],
        R: [R("loc:outside", "located-at", ["person", "outside"])],
      },
      target: {
        id: "room:t1",
        addresses: ["person", "room", "door:north", "outside"], F: [], I: [],
        R: [R("loc:room", "located-at", ["person", "room"]), R("via:north", "entered-via", ["person", "door:north", "room"])],
      },
      warrant: "toy observation: entry through north door",
      trace: ["outside relation withdrawn", "room relation born", "north-door path retained"],
      questions: ["Where is the person now?", "How did they enter?"],
    }),
  },
];

export const applePair = { gift: specimens[0].mathal, loss: specimens[1].mathal };
