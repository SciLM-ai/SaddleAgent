# Topic 12662 — POSCAR.IS for NEB

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> The AI is giving a sensible response.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**ndsram** (2022-03-08 12:10):

Going to perform NEB for MXene, but back to basic question like from where should I get this POSCAR.IS file, is the base file I define or from the CONTCAR  after optimization or from CONTCAR of SCF and what is POSCAR>FS file CONTCAR OF SCF or CONTCAR of Band structure? Which one should I consider

---

**ndsram** (2022-03-10 13:15):

Thank you Graeme, I've done the optimization of the structure Ti2CO2_CO2, so consider the CONTCAR --> as POSCAR.IS and 

secondly I've done my Self consistent field (SCF) calculation and then copied the CONTCAR to POSCAR for Band Structure calculation. so to consider POSCAR.FS which one should I consider? the CONTCAR of Band structure or the CONSTCAR of SCF

I'm not getting the POSCAR.FS to use the nebmake.pl  POSCAR.IS POSCAR.FS 5

Please guide me to get the POSCAR.FS

## Expert answer (forum ground truth)

**graeme** (2022-03-09 10:53):

Yes, that's right, the initial structure should be from an optimized CONTCAR from a geometry in your initial state.  The final structure should be a CONTCAR from an optimized calculation of your final state.  I don't understand the difference between SCF and Band structure - these optimization calculations should converge the geometry, but of course to do that you have to also optimize the band structure and this is done via an SCF calculation.

---

**graeme** (2022-03-11 14:40):

Again, you are always doing SCF calculations to determine the energy and force; with those, you can optimize the structure.  It doesn't make any sense (to me) to talk about "secondly doing an SCF calculation".  But then, once you have your initial state, you need to determine to what state you want to calculation a reaction to - you are the one who needs to determine the final state that you are interested in.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Both POSCAR.IS and POSCAR.FS come from the CONTCAR of a full geometry (ionic) optimization — never from an SCF single-point and never from a band-structure run.** POSCAR.IS = the relaxed CONTCAR of your reactant (initial) structure; POSCAR.FS = the relaxed CONTCAR of your product (final) structure. The "base file you define" is only the *starting guess* you feed into those two relaxations — not the endpoint itself.

### Why not the others

- **SCF / single-point CONTCAR** (`IBRION=-1`, `NSW=0`) → the atoms never move, so that CONTCAR is essentially a copy of your input POSCAR. Using it means your "endpoint" is unrelaxed, and NEB will waste images relaxing the endpoints instead of finding the saddle. Confirm a real relaxation with `grep 'reached required accuracy' OUTCAR` and `grep EDIFFG INCAR` (want a force criterion, e.g. `EDIFFG = -0.02`).

- **Band-structure CONTCAR** → a band run is non-self-consistent (`ICHARG=11`) at *fixed* geometry, just to get eigenvalues/DOS. It does no ionic motion and is geometrically meaningless as an NEB endpoint. Don't use it.

### The correct workflow for your MXene NEB

1. **Reactant (IS):** build your base MXene + adsorbate/defect in the starting site → relax ions (`IBRION=2`, `NSW≈100`, `EDIFFG=-0.02`, **`ISIF=2`** = fixed cell) → the resulting **CONTCAR is POSCAR.IS**.

2. **Product (FS):** take that *same* cell, move only the migrating atom/group to the final site → relax with the **identical** cell and INCAR electronic settings → the resulting **CONTCAR is POSCAR.FS**.

3. Build the band: `nebmake.py POSCAR.IS POSCAR.FS <N_images>` creates `00/ … NN/`; then **copy the two relaxation OUTCARs into `00/` and `NN/`** (post-processing needs them).

### Two MXene-specific pitfalls to lock down now

- **Same cell for both endpoints.** Relax both with `ISIF=2` (ions only, fixed lattice). If IS and FS were each relaxed with cell freedom (`ISIF≥3`), their lattice vectors differ, NEB's linear interpolation then deforms the slab between images, and you get a garbage/barrier-less path.

- **Identical per-atom ordering** in POSCAR.IS and POSCAR.FS — same atom on the same line, not just matching element counts. Mismatched ordering makes the interpolation drag the wrong atoms across the cell.

Confidence: high — this is the standard endpoint preparation, confirmed against the VTST `nebmake` docs (endpoints are two *relaxed* POSCAR/CONTCAR files in `00`/`NN`).

If you share your relaxation INCAR (or the two endpoint OUTCAR tails), I'll verify the endpoints actually converged and that the cells match before you build the band.
