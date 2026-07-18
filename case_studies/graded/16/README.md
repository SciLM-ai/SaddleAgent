# Topic 16 — dimer reorientation

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> AI did pretty well.  This is tricky in that this question is from a long time ago when we had 01 and 02 directories for a central difference dimer.  So I don't fault the answer too much.  In the current scheme, it should really copy the CENTCAR to the POSCAR, but the response is pretty good.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**tamas** (2005-05-25 04:47):

Could anybody please let me know, how one can continue a previous

dimer run so that the initial orientation of the dimer be the same as

it was at the end of the previous dimer run? Is it enough to copy the

previous CONTCAR files to the POSCAR or shall I also include some flag

in the INCAR file in order not to start with a random orientation again? 

Thank you in advance!

T.

## Expert answer (forum ground truth)

**graeme** (2005-05-25 09:23):

As you suggest, copying the CONTCAR file to POSCAR in the 01 and 02 directories will be enough.

If you have our scripts downloaded, there is a convenient way to archive a finished run and be ready to start a new one from where it left off, using:

vfin.pl <archive dir name>

This will work with regular vasp, dimer, lanczos and neb runs.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**No — copying CONTCAR→POSCAR alone is not enough. That only restarts the *position*; without a `MODECAR` file the dimer re-draws a random orientation. To keep the previous orientation, also copy the final `NEWMODECAR` → `MODECAR`. There is no INCAR flag for this — the orientation is controlled entirely by whether a `MODECAR` file is present at launch.**

Concretely, in the restart directory:

```
cp CONTCAR    POSCAR     # the dimer center (geometry)
cp NEWMODECAR MODECAR    # the final dimer orientation (mode vector)
```

Why this is the fix:

- **The orientation lives in `MODECAR`, not the INCAR.** Per `docs/vtst/dimer.md`, `MODECAR` is the initial dimer direction (a Cartesian unit vector estimating the lowest-curvature mode); **"if absent, a random direction is used."** So the *presence* of the file is the switch — there is no `ICHAIN`/`Dxxx` tag that says "don't randomize." You just keep your usual dimer deck: `ICHAIN=2`, `IBRION=3`, `POTIM=0`, and your `IOPT`.

- **The end-of-run orientation is in `NEWMODECAR`.** The dimer (re)writes the current lowest mode to `NEWMODECAR` every ionic step, so at termination it holds exactly the orientation you want to resume from. Copy it onto `MODECAR` and the new run starts aligned instead of from a random guess. (Confirmed in `docs/vtst/scripts.md` — `CENTCAR`+`NEWMODECAR` are the canonical final center+mode pair the VTST scripts consume.)

One caveat on the geometry file (`reference/dimer-diagnostics.md`, CENTCAR/CONTCAR entry):

- On **modern VTST builds** the dimer center is written to `CONTCAR` every ionic step, so `CONTCAR→POSCAR` is correct and pairs cleanly with `NEWMODECAR`.

- On **old builds** (pre ~2011 vtstcode), `CONTCAR` could be a *displaced* image (center ± ½·DdR) rather than the center. The tell on restart is curvature flipping negative→positive and forces jumping ~10×. If you ever see that, copy **`CENTCAR`→POSCAR** instead. `vfin.pl` does this substitution for you automatically, which is why its restart POSCAR may match neither the old POSCAR nor CONTCAR — that's expected, not a bug.

Confidence: high on the core answer (MODECAR-presence controls random vs. seeded; `NEWMODECAR` is the saved final mode). If you tell me your VASP/VTST version I can confirm whether you're in the "CONTCAR is fine" or the "use CENTCAR" regime — `grep 'VTST: version' OUTCAR` from the previous run settles it.
