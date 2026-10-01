# Physical Composer 001

Physical Composer proposes material forms for admitted works before they cross Press Gate.

It is intentionally split into two actions:

    compose -> recommendation set
    select  -> explicit human selection receipt

The composer never turns a recommendation into a production fact by itself.

## Brief

A minimal brief names:
- work_id
- title
- edition_intent

Useful optional fields:
- content.estimated_pages
- content.image_density
- constraints.budget
- constraints.home_printable
- affordances
- notes

## Run

    python tools/physical_composer.py compose physical-composer/example-brief.json --out composition.json

The output contains several candidate bodies. Every candidate is state: recommended.

A human may then explicitly select one:

    python tools/physical_composer.py select composition.json staircase --out selection.json

Only that second command emits state: human_selected.

## Current archetypes

The first executable vocabulary can propose:
- ordinary codex
- saddle-stitched booklet
- staircase edition
- field / receipt book
- pamphlet cluster
- folio / insert edition
- mechanical book

These are starting apertures, not a closed taxonomy.

## Law

RECOMMENDATION != SELECTION

FORM != SOURCE

MATERIAL EFFECT != SOURCE FACT

PROOF != PUBLICATION

The composer imagines the body. Press Gate proves which body crossed.
