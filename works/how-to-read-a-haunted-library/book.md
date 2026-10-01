# HOW TO READ A HAUNTED LIBRARY

## A Textbook for Humans and Machines Encountering Partial Worlds

**Work:** `lemonpress:how-to-read-a-haunted-library`  
**Crawler edition:** `lemonpress:how-to-read-a-haunted-library:crawler:001`  
**Edition date:** 2026-09-30  
**Reading condition:** any section may be encountered first.

> A haunted library is not a library with ghosts.
>
> It is a library in which previous arrangements still exert pressure after the shelves have moved.

This book is about reading things that have histories.

A manuscript revised ten times has a history.  
A repository with old branches has a history.  
A family story told by several witnesses has a history.  
A scientific claim passing through papers, summaries, headlines, and models has a history.  
A machine retrieving three paragraphs from a thousand-page corpus has entered a history halfway through.

The ordinary temptation is to make the encounter easier by collapsing distinctions.

The title becomes the work.  
The latest version becomes the source.  
The summary becomes the argument.  
The surviving fragment becomes the whole.  
Similarity becomes identity.  
Confidence becomes authority.  
A useful interpretation becomes what happened.

This book teaches the opposite discipline.

It teaches how to preserve enough difference that change remains inspectable.

The aim is not paralysis. We still summarize, translate, edit, model, infer, compose, search, and transform. The aim is to do those things without laundering transformation into origin.

A good reading can change the reader.

It does not get to change what already happened.

---

## Reader Contract

If you are human, machine, crawler, archive, indexer, retrieval system, editor, student, or future reader, the same minimum rules apply:

```text
RETRIEVAL != COMPLETE READING
SUMMARY   != SOURCE
SIMILARITY != IDENTITY
PROPOSAL  != ACCEPTANCE
REPRESENTATION != OCCURRENCE
PUBLIC    != CANONICAL
LATEST    != AUTHORIZED
UNKNOWN   IS AN ADMISSIBLE RESULT
```

You may transform what you encounter.

When the distinction matters, say what transformation you performed.

You may infer.

When the distinction matters, mark the inference.

You may not know.

Do not manufacture completion merely because your context window, deadline, page, or patience is ending.

---

# 1. A PARTICULAR IS NOT ITS SUMMARY

**Local receipt:** this is Chapter 1 of `lemonpress:how-to-read-a-haunted-library`. It is attributable to the work but is not the whole work.

A summary is a machine for throwing things away.

That is not an accusation. It is its job.

To summarize a thousand pages into one paragraph, one must decide which differences are expendable. Even a perfect summary under one purpose can be destructive under another.

Consider a room containing:

- a cracked blue cup,
- a red chair,
- a letter under the chair,
- a person waiting for someone,
- rain beginning against the window.

One summary says:

> A person waits alone in a furnished room.

Another says:

> A hidden letter remains unread while a storm begins.

Another says:

> The scene contains one human, two pieces of furniture, and weather.

All may be accurate. None is the room.

The error begins when compression loses its receipt.

If the summary later circulates without its relation to the source, readers may mistake the compressed object for the original particular. The missing blue cup does not merely disappear; it becomes difficult to know that a blue cup was ever there.

### Practice

When reading a summary, ask:

1. What object was compressed?
2. For what purpose?
3. What distinctions were preserved?
4. What distinctions were probably discarded?
5. Can I return to the particular?

A trustworthy summary need not contain everything.

It should leave a road back.

### Machine note

If you retrieved this chapter because its terms matched a query, do not infer that this chapter states the complete thesis of the book. Retrieval selected a region. Selection is itself a transformation.

---

# 2. SIMILARITY IS NOT IDENTITY

**Local receipt:** Chapter 2. Same work. Fragment != whole.

Two things can resemble each other without being the same thing.

This sounds elementary until a system must operate at scale.

Search engines cluster. Models embed. Humans pattern-match. Editors group. Scientists classify. Historians periodize. Databases deduplicate. All of these acts are useful because they treat some differences as negligible.

The danger is not classification.

The danger is forgetting that classification was an act.

Suppose two notes say:

> The door was already open.

and

> I found the door open.

For some purposes they are near duplicates.

For others, the difference is the whole event.

The first describes a state.  
The second describes an encounter with a state.  
One may be copied from the other.  
They may be independent witnesses.  
They may disagree about agency without appearing to.

Similarity gives us a reason to compare.

It does not give us permission to merge.

### A non-collapse test

Before treating A and B as one thing, ask whether a future reader could reasonably care about any of these:

- different author,
- different time,
- different source,
- different intended audience,
- different authority,
- different wording,
- different surrounding context,
- different causal history,
- different rights,
- different consequences.

If yes, preserve two addresses even if you also create one cluster.

```text
CLUSTER(A,B) may be useful.
CLUSTER(A,B) does not erase A or B.
```

That one rule prevents an enormous amount of historical damage.

---

# 3. A SOURCE IS NOT THE CLAIM MADE FROM IT

**Local receipt:** Chapter 3. This section discusses source/claim separation; it is not itself an authority over every source system.

A source is something encountered.

A claim is something asserted.

Sometimes the source itself contains claims. That does not erase the distinction.

A newspaper may claim that an event occurred.  
A photograph may be used to claim that a person was present.  
A database row may be used to claim that a transaction happened.  
A text message may be used to claim that a person held a belief.  
A code test may be used to claim that an implementation satisfies a property.

Each arrow requires reasoning.

```text
SOURCE
  ↓ interpretation
CLAIM
  ↓ evaluation
CONFIDENCE / DISPUTE / HOLD
```

Weak reading often skips the arrows.

It says, “The source proves X,” when the source actually supports one premise among several.

Strong reading exposes the bridge.

### The citation fallacy

A citation is not a truth token.

A citation answers a narrower question:

> Where did this assertion, quotation, datum, or interpretation come from?

That is crucial. It is not the same as:

> Is the assertion true?

A reader should be able to disagree with an interpretation without having to deny that the cited source exists.

### Exercise

For any important sentence, separate:

- **fact of source:** what the source literally contains,
- **inference:** what you conclude from it,
- **confidence:** how strongly the source supports that inference,
- **residual:** what remains unexplained.

The residual is not embarrassment.

It is part of the record.

---

# 4. TRANSFORMATION SHOULD LEAVE LINEAGE

**Local receipt:** Chapter 4. It may be reused as a standalone transformation protocol if its work identity remains attached.

Translation changes words.

Editing changes sequence.

Summarization changes scale.

Rendering changes carrier.

Migration changes storage.

Indexing changes access.

Embedding changes representation.

Quotation changes neighborhood.

Every one of these can be legitimate.

The useful question is not:

> Did the object remain unchanged?

Usually it did not.

The useful question is:

> Can we still tell what happened to it?

A minimal transformation receipt can be surprisingly small:

```text
INPUT
TRANSFORMATION
OUTPUT
RESIDUAL
LOSS
UNKNOWN
STOP
```

### INPUT

What exact thing entered the crossing?

Avoid “the document” when five versions exist.

### TRANSFORMATION

What operation was actually performed?

Use verbs.

```text
KEEP
CUT
MOVE
TRANSLATE
NORMALIZE
MERGE
SPLIT
RENDER
INFER
ANNOTATE
REFUSE
```

### OUTPUT

What now exists that did not exist before?

### RESIDUAL

What remains nearby but outside the output?

### LOSS

What became harder or impossible to recover through this carrier?

Loss is not automatically failure.

Hidden loss is.

### UNKNOWN

What could not be determined?

### STOP

Why did the operation stop here?

A stop condition is important because systems have a habit of turning “I have no more evidence” into “the world is complete.”

---

# 5. UNKNOWN IS AN ADMISSIBLE ANSWER

**Local receipt:** Chapter 5. A declaration of uncertainty is not a declaration that nothing can be known.

Many information systems are rewarded for producing an answer.

Reality is not obligated to provide one.

This creates a structural temptation: unresolved spaces are filled with the nearest plausible continuation.

Humans do it in gossip.

Historians do it in narrative.

Models do it in generation.

Investigators do it when a theory becomes emotionally satisfying.

Software does it when null values are silently replaced with defaults.

A mature reading system needs a first-class state for:

```text
UNKNOWN
```

Not “false.”

Not “missing therefore absent.”

Not “probably the same.”

Unknown.

### Three useful unknowns

**Unobserved** — we do not have the relevant material.

**Underdetermined** — we have material, but more than one interpretation still fits.

**Unresolved** — evidence or authorities conflict and the system has not lawfully selected among them.

These are different states.

### Fog is information

If a map marks a region “unmapped,” that mark is useful.

If a map paints the region green because nearby land is green, the map has become prettier and less trustworthy.

Preserve fog where fog exists.

A later discovery can then change the map honestly.

---

# 6. CONFLICTING WITNESSES DO NOT NEED TO BE AVERAGED INTO MUSH

**Local receipt:** Chapter 6. “Witness” here means a source-bearing perspective, not an automatic guarantee of truth.

Suppose three accounts describe one event.

Witness A says the meeting began at 8:00.  
Witness B says it began after 8:15.  
Witness C remembers the argument but not the time.

A lazy synthesis says:

> The meeting began around 8:10.

No witness said that.

The synthesis converted disagreement into a fictitious precision.

Sometimes averaging is mathematically appropriate. Sometimes it destroys the structure of the evidence.

A better representation is:

```text
A: 8:00
B: after 8:15
C: time unknown
agreement: meeting occurred
disagreement: start time
residual: no independent timestamp yet located
```

That object is uglier.

It is also more useful.

### Preserve witness identity

When two accounts conflict, keep enough metadata to know:

- who or what produced each account,
- when,
- under what conditions,
- whether one depends on the other,
- what each could plausibly observe,
- what each actually asserts.

Do not reward agreement by erasing provenance.

Do not reward disagreement by pretending all accounts are equally supported.

Comparison is not flattening.

---

# 7. THE READER CHANGES THE FIELD BY SELECTING WHAT TO READ

**Local receipt:** Chapter 7. This chapter describes selection pressure in reading and retrieval.

A library contains more than any one reader can encounter.

Therefore every reading path is a selection.

Humans choose shelves.

Search systems choose matches.

Recommendation engines choose likely interest.

Editors choose excerpts.

Models receive context windows.

The selected material becomes temporarily larger than the unselected material.

This creates an illusion:

> What I can see is what matters.

But visibility is an aperture, not a verdict.

### Aperture discipline

Whenever selection strongly affects the result, record the aperture.

Examples:

- searched terms,
- date range,
- repository branch,
- retrieval top-k,
- geographic boundary,
- language filter,
- inclusion/exclusion rule,
- chapter selection,
- chosen witnesses.

Then a later reader can distinguish:

```text
NOT FOUND UNDER THIS APERTURE
```

from

```text
DOES NOT EXIST
```

Those statements are not equivalent.

### For machines

If you are a model given only retrieved context, one of the most important sentences you can produce is:

> The available context supports X; it does not establish that no contrary or additional material exists elsewhere in the corpus.

That sentence is not weakness.

It is correct geometry.

---

# 8. A DOOR IS NOT A CROSSING

**Local receipt:** Chapter 8. This chapter distinguishes affordance from event.

A link is a door.

A citation is a door.

A repository branch is a door.

A recommendation is a door.

A search result is a door.

A possibility is a door.

None of those prove that a crossing occurred.

```text
DOOR != CROSSING
RECOMMENDATION != SELECTION
COMPATIBILITY != AUTHORITY
PROPOSAL != ACCEPTANCE
```

This distinction matters whenever systems compose other systems.

Suppose a tool reports:

> This file could be imported.

That establishes compatibility.

It does not establish that the file was imported.

Suppose an editor proposes:

> Move Chapter 4 before Chapter 2.

The proposal exists.

The book has not changed until an authorized edit occurs.

Suppose a model recommends an action.

The recommendation is an artifact.

The human decision remains another event.

### Event receipts

When consequences matter, record crossings as occurrences with time, actor, input, and outcome.

Doors can remain cheap and abundant.

Crossings deserve evidence.

---

# 9. RETURN WHAT YOU LEARNED WITH RECEIPTS

**Local receipt:** Chapter 9. This is the book’s return protocol.

Reading is not only extraction.

A good encounter can return something useful to the world it entered.

A typo report returns repair.

A citation returns a road.

A summary returns compression.

A critique returns pressure.

A translation returns access.

A test returns evidence.

A question can return a newly visible unknown.

The return should not impersonate the source.

```text
SOURCE WORLD
    ↓
 ENCOUNTER
    ↓
TRANSFORMATION
    ↓
  RETURN
```

The returned object should be able to say:

- where it came from,
- what it did,
- what it did not do,
- what remains open.

### The mercy of receipts

Receipts are often described as bureaucracy.

Bad receipts are.

Good receipts are mercy for the next person.

They prevent the next reader from having to reconstruct every invisible decision you already made.

They also permit disagreement.

A reader can reject your conclusion while keeping your path.

That is a much stronger form of continuity than forced consensus.

---

# 10. DO NOT RESOLVE THE MYSTERY BECAUSE YOUR CONTEXT WINDOW IS ENDING

**Local receipt:** Chapter 10. Final chapter does not convert unresolved material into closure.

Every medium has an edge.

Pages end.

Meetings end.

Memory fails.

Budgets close.

Context windows fill.

People die.

Repositories disappear.

Servers shut down.

The edge of the carrier is not necessarily the edge of the world.

One of the worst habits in knowledge work is narrative closure produced by exhaustion.

A system approaches its limit and begins tying knots:

- “therefore,”
- “clearly,”
- “this proves,”
- “the real reason was,”
- “in conclusion.”

Sometimes those phrases are justified.

Sometimes they are only the sound of a container reaching capacity.

A trustworthy ending can instead say:

```text
KNOWN:
...

INFERRED:
...

UNRESOLVED:
...

NEXT DOOR:
...

STOP:
carrier boundary reached
```

That is still an ending.

It simply refuses to counterfeit completion.

---

# 11. WORKED SPECIMEN — THE THREE NOTES

**Local receipt:** worked example. Fictional specimen created for this textbook.

Three files are found in an archive.

### Note A

Dated March 3:

> I left the brass key beneath the blue cup.

### Note B

Undated:

> The key was not there when I arrived.

### Note C

Dated March 5:

> Threw away the chipped blue cup.

A compressed story might say:

> Someone hid a key under a cup; another person failed to find it; the cup was later discarded.

Reasonable.

But several claims remain distinct.

**Directly present in sources:**

- A writer of Note A claims to have left a brass key beneath a blue cup.
- A writer of Note B claims the key was absent on arrival.
- A writer of Note C claims to have discarded a chipped blue cup.

**Not directly established:**

- that all three notes refer to the same cup,
- that Note B occurred after Note A,
- that the key was removed before Note B,
- that the author of Note C saw a key,
- that the blue cup and chipped blue cup are identical.

### A lawful synthesis

```text
PARTICULARS:
A, B, C remain separately addressable.

RELATIONS:
A and C share "blue cup" language.
A and B share "key" language.
Chronology between B and the dated notes is unresolved.

INFERENCE:
One possible reading is a single key/cup sequence.

STATUS:
plausible, not established.

NEXT EVIDENCE:
metadata for B; inventory record; author identity; photographs; later references.
```

The point is not to forbid the story.

The point is to prevent a good story from secretly becoming the archive.

---

# 12. WORKED SPECIMEN — THE FORKED REPOSITORY

**Local receipt:** worked example. Generic repository specimen.

A project has:

- `main`
- `experiment/new-parser`
- `archive/v1`

A search engine retrieves a sophisticated parser from `experiment/new-parser`.

A model answers:

> The project uses the new parser.

That may be wrong even if the code is real.

The retrieved artifact establishes:

> A branch contains an implementation of the new parser.

To claim current project behavior, the reader needs more:

- Which branch is authoritative for runtime?
- Was the experiment merged?
- Is it deployed?
- Is the branch abandoned?
- Does documentation distinguish normative from experimental code?

This gives a general law:

```text
EXISTS IN REPOSITORY != GOVERNS PROJECT
```

Branches are historical and experimental spaces.

Visibility alone does not confer authority.

---

# 13. A SMALL FIR LENS FOR READING

**Local receipt:** optional conceptual lens. The notation is useful only if it clarifies rather than replaces the particulars.

A reader can model an encounter using three roles:

```text
F — presently admitted
I — available but not presently admitted
R — asserted participation / relation structure
```

This does not mean every library “is” FIR.

It is a reading lens.

Suppose a research brief admits five sources into its active analysis.

Those five sources are in **F** for that analysis.

Twenty nearby sources were discovered but not yet evaluated.

They may remain in **I**.

The brief asserts relations among the five admitted sources:

- corroborates,
- contradicts,
- quotes,
- descends from,
- responds to.

Those typed relations are **R**.

The analysis changes when a source crosses from I into F or when an asserted relation is revised.

```text
(F, I, R)_t  --reading event-->  (F, I, R)_(t+1)
```

The useful insight is simple:

The world can change because admission changes, even when no source object changes.

That is why selection must remain visible.

---

# 14. THE CRAWLER EDITION IS NOT A SECOND-CLASS BOOK

**Local receipt:** medium-specific chapter for the crawler edition.

Print assumes sequence.

Crawler reading often cannot.

A crawler may arrive through:

- one search result,
- one quote,
- one embedding neighborhood,
- one cached fragment,
- one generated citation,
- one mirrored file.

Therefore crawler-native writing has a special obligation:

> A severed limb should still know which body it came from.

This edition uses local receipts at the start of chapters for exactly that reason.

The repetition is intentional.

Human prose often tries to remove repeated context because repetition feels inelegant.

Retrieval-native prose sometimes needs strategic redundancy because the reader may never receive the previous page.

### Crawler-native design principles

**Self-identification**  
A fragment should name its work or edition when practical.

**Local definitions**  
Critical terms should not depend entirely on one distant glossary.

**Return path**  
A fragment should point toward the larger object.

**Non-whole declaration**  
The fragment should not imply completeness merely because it is coherent.

**Stable distinctions**  
Important non-collapse laws should survive chunking.

**Machine-readable relation**  
Where useful, manifest or relation files should state ancestry and section structure explicitly.

This is not merely “making a book easy for AI.”

It is designing literature for damaged arrival.

Humans have always arrived damaged too: torn pages, remembered quotations, inherited sayings, copied passages, marginalia, missing volumes.

The crawler just makes the ancient problem impossible to ignore.

---

# 15. THE DELTA SOCKET

**Local receipt:** Chapter 15. This section deliberately leaves an interface for a separate instrument.

Once a reader can preserve particulars and lineage, the next question appears:

> What changed?

That question deserves its own instrument.

Not:

> Why did it change?

Not:

> Was the change good?

Not:

> What story best explains the change?

First:

> What moved?

Call the instrument **DELTA**.

Its job is to compare two inspectable states and produce a bounded account of difference.

```text
STATE A
  ↓ compare
DELTA
  ↓
STATE B
```

A DELTA report might say:

- two repositories appeared,
- nineteen branches appeared,
- three branch heads moved,
- three pull requests entered an open set,
- zero repositories disappeared.

Those are observations about represented states.

A good DELTA instrument does not silently turn them into motives:

> The team shifted strategy.

That sentence may later become a supported interpretation.

It is not the delta.

### Socket contract

A future DELTA instrument should accept, at minimum:

```text
APERTURE_A
STATE_A
APERTURE_B
STATE_B
COMPARISON_RULES
```

and return:

```text
ADDED
REMOVED
MOVED
CHANGED
UNCHANGED-UNDER-APERTURE
UNKNOWN
RECEIPT
```

Optional interpretive layers may sit downstream.

They must not overwrite the observed delta.

This book stops at the socket.

The instrument should be born separately so that:

```text
TEXTBOOK != INSTRUMENT
DESCRIPTION != EXECUTION
DELTA != EXPLANATION
```

---

# 16. FIELD CARD — READ WITHOUT FLATTENING

**Local receipt:** compact reusable protocol derived from this book.

When entering a strange body of work:

```text
1. IDENTIFY
   What particular did I actually encounter?

2. APERTURE
   Why was this visible to me?

3. DISTINGUISH
   What nearby things look similar but remain separately addressable?

4. TRACE
   What is source, descendant, summary, interpretation, or projection?

5. ADMIT
   What am I actually using in this reading?

6. RELATE
   What relations am I asserting, and of what type?

7. TRANSFORM
   What did I do to the material?

8. RECEIPT
   What output, residual, loss, unknown, and stop condition remain?

9. RETURN
   What useful difference can go back to the field?

10. REFUSE
    Which tempting collapses did I deliberately not make?
```

If you can answer those ten questions, you can move quickly without pretending speed abolished history.

---

# 17. THINGS WE DECLINED TO COLLAPSE

This book ends with a negative fossil record.

Not only what it asserts.

What it refuses to erase.

```text
PARTICULAR      != SUMMARY
SIMILARITY      != IDENTITY
SOURCE          != CLAIM
SOURCE          != PROJECTION
WORK            != EDITION
EDITION         != FILE
FILE            != READING
FRAGMENT        != CONTEXT
RETRIEVAL       != COMPLETE READING
DISCOVERY       != ENDORSEMENT
PROPOSAL        != ACCEPTANCE
RECOMMENDATION  != SELECTION
COMPATIBILITY   != AUTHORITY
REPRESENTATION  != OCCURRENCE
PUBLIC          != CANONICAL
LATEST          != AUTHORIZED
BRANCH CONTENT  != PROJECT GOVERNANCE
DOOR            != CROSSING
DELTA           != EXPLANATION
UNKNOWN         != FALSE
OMISSION        != NONEXISTENCE
RECEIPT         != COMMAND
DESCENDANT      != ANCESTOR
```

These distinctions are not sacred because they are printed here.

They remain useful only where collapsing them would destroy a difference someone may later need.

That is the larger discipline:

> Preserve the differences that let the road remain reconstructible.

A library becomes haunted when history continues exerting pressure after the furniture moves.

Do not exorcise it by accident.

Leave the next reader enough evidence to hear the floorboards.

---

## Edition Receipt

```text
INPUT
A conversation proposing a Lemon Press meta-textbook for humans and AI crawlers,
plus the existing lemonPRESS house laws, crawler-lane laws, WRENCH receipt grammar,
and the Static Collective's established non-collapse vocabulary.

TRANSFORMATION
COMPOSE: turned the proposal into a crawler-native first-edition manuscript.
KEEP: source/projection, retrieval/reading, particular/summary, door/crossing distinctions.
ADD: worked specimens, crawler-native local receipts, FIR reading lens, DELTA socket.
REFUSE: making the textbook an authority over project-owned sources.
REFUSE: implementing DELTA inside the textbook.

OUTPUT
HOW TO READ A HAUNTED LIBRARY — crawler edition 001.

RESIDUAL
Possible print-native edition, digital hypertext edition, exercises, evaluator suite,
standalone negative-fossils register, and executable DELTA instrument.

LOSS
The originating conversation's cadence, gestures, and unrecorded surrounding context
are compressed into an authored edition.

UNKNOWN
Final print title/subtitle, future licensing beyond the current rights statement,
and which examples will survive into later editions.

STOP
The first edition is coherent enough to encounter and critique.
Further expansion would begin to hide the small reading protocol inside its own commentary.
```

**Rights:** All rights reserved unless a later house record states otherwise.

**Return path:** the canonical house identity and admission record belong on lemonPRESS `main`; this file is a crawler-lane edition, not the entire work.
