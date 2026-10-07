# RELETTER BATCH 001 + MASK LETTERING 001

These two primitives close the visual seam exposed by BOX BINDING 001.

## RELETTER BATCH 001

Consumes a materialized PAGE INTAKE bundle plus BOX BINDING candidate.

Every `solid-dark` and `solid-light` particular is rendered with returned English. Font size is deterministically reduced within a declared role-specific range until the text fits; failure below the declared minimum refuses.

Art/sign blockers are copied through untouched.

For THE LAST STOP MOVED this means 59 / 68 particulars render in the first pass.

## MASK LETTERING 001

Consumes the verified batch output and requires an explicit overlay for the exact blocker set.

The overlay is a declared polygon, declared RGBA matte, declared foreground, and declared font-fit range.

It is intentionally **not inpainting**. Pixels inside the polygon may be covered or alpha-blended. Pixels outside the polygon survive exactly from the batch parent. No hidden attempt is made to reconstruct artwork underneath the old letters.

For THE LAST STOP MOVED the blocker set is exactly nine particulars: six art surfaces and three physical signs.

## Final state

After both passes, all 68 returned-English particulars are visibly represented across the ten page candidates.

That is still not edition admission.

```text
PAGE INTAKE
  -> BOX BINDING
     -> RELETTER BATCH (59)
        -> MASK LETTERING (9)
           -> COMPLETE_VISUAL_CANDIDATE
              -> explicit human selection / edition admission later
```
