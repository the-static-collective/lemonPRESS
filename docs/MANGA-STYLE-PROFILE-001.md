# MANGA STYLE PROFILE 001

A style is frozen behavior, separately identified from page content. Language-through, Renji color and Renji monochrome profiles can be reused independently. The eight founding profiles encode the declared behavior evidenced by the supplied pages; they do not claim pixel extraction, aesthetic equivalence, source ownership, or a renderer's visual success.

Profiles declare every domain as `own`, `suggest` or `none`. Populated behavior with `none`, empty behavior with `own`/`suggest`, unknown fields and authority assertions refuse. Ownership is bounded to declared fields within a domain. This lets receipt, screen and artifact overlays coexist within `worldMotifs` without replacing each other.

Stacks reference profile IDs and explicit scopes. Global entries list all six domains. Domain-scoped entries list their domain mask. Channel-scoped entries name `textChannels` and an additional `channelMask`; this is required because channel scope cannot safely be inferred from prose.

For each field, a single explicit override wins. Multiple overrides refuse. Otherwise owners outrank suggestions regardless of priority. Multiple owners refuse unless `resolutionPolicy` explicitly selects `explicit-priority`, and tied owners still refuse. Suggestions fill unowned fields only; tied contradictory suggestions refuse. Profile scope applies before overrides, so an override cannot reach outside the entry's declared scope.

The canonical resolution carries the full stack hash, ordered entry declarations, all applied profile hashes, chosen field provenance, laws and false authority flags. The `resolutionHash` hashes that body before adding the hash itself. `candidate_identity(parent_sha256, resolution)` binds page parent and resolution. Reordering a stack, changing an override or changing behavior therefore creates a different candidate identity even if a renderer happens to emit identical pixels.

Primary/gloss languages stay distinct. Text channel records retain their channel purpose, including `world_text` and `dialogue`. Callers declare renderer-required fields; absent fields refuse rather than becoming invented renderer defaults.

```sh
python3 -m pip install -r requirements-style.txt
python3 -m unittest discover -s tests -p 'test_manga_style_*.py'
python3 tools/manga_style_lint.py works/style-stacks/RENJI_JP_RELAY_COLOR_001/stack.json
python3 tools/manga_style_resolve.py compose works/style-stacks/RENJI_JP_RELAY_COLOR_001/stack.json out/color.json
python3 tools/manga_style_resolve.py verify works/style-stacks/RENJI_JP_RELAY_COLOR_001/stack.json out/color.json
```

Style-aware render declarations use `styleStackRef` pointing to a stack JSON, then retain `stackHash`, `resolutionHash` and profile ancestry in the candidate. This branch adds the resolver and candidate identity seam; each renderer must explicitly consume the resolved fields it supports. Resolution itself creates no page render, edition admission or publication.

WRENCH: INPUT: eight frozen behavior profiles and a stack. TRANSFORMATION: resolve explicit field ownership and scoping. OUTPUT: replayable behavior candidate. RESIDUAL: original profile/stack declarations and source pages remain independent. LOSS: aesthetic prose becomes a bounded behavior vocabulary. UNKNOWN: visual quality and downstream renderer support. STOP: unresolved conflicts refuse; the resolver never selects content or admits an edition.
