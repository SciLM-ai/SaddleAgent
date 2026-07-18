# Topic 16184 — General NEB question with VaspSol

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> AI provided a good answer.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**jess_white** (2025-05-23 09:09):

Hi,

I was just wondering if I am able to run NEB calculations with VaspSol? Such as the following? 

LSOL = .TRUE.

EB_K = 35 

Also I was wondering if IOPT = 3 is the best way to go and how do you know when you should change the IOPT?

NSW    =  500          (number of ionic steps)

ISMEAR =  0            (gaussian smearing method)

SIGMA  =  0.05         (please check the width of the smearing)

IBRION =  3            (do MD with a zero time step)

POTIM  =  0            (Zero time step so that VASP does not move the ions)

SPRING =  -5.0         (spring force (eV/A2) between images)

LCLIMB =  .TRUE.       (turn on the climbing image algorithm)

ICHAIN =  0            (Indicates which method to run. NEB (ICHAIN=0) is the default)

IOPT   =  3            (LBFGS = Limited-memory Broyden-Fletcher-Goldfarb-Shanno)

EDIFFG = -0.01

Many thanks in advance!

---

**jess_white** (2025-05-24 08:39):

Thank you so much! I appreciate it :) Thank you also for the explanation as it made it super clear to me. Will be giving them a go now

## Expert answer (forum ground truth)

**graeme** (2025-05-23 09:48):

For sure, NEB with vaspsol is no problem

I like IOPT=3, but that is usually because I am debugging some problem calculation and that optimizer is very stable.  IOPT=1 (and probably 7) should be faster, but it is also less stable and you need a sufficiently small INVCURV as appropriate for any high frequencies in the system.  I suggest using IOPT=3 and when you see steady convergence, you can switch to IOPT=1 and see if you can speed things up with that.  I also like to use IOPT=3 when there are high forces and when I see a sensible band and forces below 0.5 eV/Ang, switch to IOPT=1

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Yes — NEB runs fine with VASPsol; solvation is force-method-agnostic, so it doesn't interfere with the band. The one hard rule is consistency: relax *both* endpoints with `LSOL=.TRUE.` and run *every* image with it on — never relax in vacuum and add solvent as single-points (that puts the TS below the IS). And a correction: `IOPT=3` is Quick‑Min, *not* LBFGS — your comment is mislabeled. Quick‑Min is the right, robust default to start with; LBFGS is `IOPT=1`.**

Confidence is high on the optimizer and consistency points (verified against `docs/vtst/optimizers.md` and the solvation guidance in the bundled reference). Detail below.

### VASPsol + NEB

- **It's allowed and standard.** CI‑NEB only ever sees forces and energies, so an implicit-solvent contribution enters exactly like any other term — it doesn't break the method.

- **Consistency is the trap.** The common failure is relaxing IS/FS in vacuum and bolting `LSOL` on as static single-points; relative energies then become meaningless (you can even get TS *below* IS). Fix: relax IS and FS *with* solvation, then run the whole NEB with `LSOL=.TRUE.` throughout. Solvation is rarely the expensive part, so there's no real savings in doing it post-hoc.

- **For charged cells** (non-default `NELECT`), solvation is effectively mandatory — it screens the charge locally and removes the uniform-background-charge artifact.

- **`EB_K = 35` is the bulk relative permittivity (dielectric constant) of the solvent**, not water. Water is `EB_K = 78.4` (the VASPsol default); 35 is a less polar/aprotic solvent (≈ methanol/acetonitrile range). Just confirm 35 is the solvent you intend. (Note: `EB_K` is a VASPsol plugin tag, not in the bundled VASP tag docs — worth a quick check against your VASPsol README/version.)

- **Accurate forces matter** with solvation: use a tight `EDIFF` (≈1e‑6) so the solvation forces feeding NEB are clean — this matters more if you later switch to LBFGS, which relies on force accuracy.

### Is `IOPT=3` best, and when to change it

Per `docs/vtst/optimizers.md`:

| IOPT | Method | Use when |
| --- | --- | --- |
| 3 | Quick‑Min (your value) | high forces / far from basin / noisy forces — robust, beginner-friendly default |
| 1 | LBFGS | accurate forces, near convergence — fastest, but uses curvature so it overshoots if started far/high |
| 7 | FIRE | like Quick‑Min, sometimes faster |
| 2 | CG | accurate forces, line search |

- **Start with `IOPT=3` (Quick‑Min) — your choice is good.** With VASPsol (slightly noisier forces) and an un-pre-relaxed band, it's the safe one. Keep `TIMESTEP=0.1` (the default).

- **Switch to LBFGS (`IOPT=1`) to accelerate the tail** once the band is well-behaved and max force is moderate (≈ ≤ 0.3 eV/Å). LBFGS converges the last stretch much faster.

- **Symptoms that tell you to switch:** Quick‑Min crawling/plateauing just above `EDIFFG` while still descending → go to `IOPT=1`. Conversely, if you started on LBFGS and forces *grow* or geometries go unphysical → it overshot; drop back to `IOPT=3`. If Quick‑Min merely oscillates near convergence, raise `TIMESTEP` toward 0.1 before changing optimizer.

### Two things to check in the deck you pasted

- **`IMAGES` is missing** from what you pasted — make sure it's set (it's required for NEB). For a reliable MEP use **≥4** interior images, more if the path is long/curved (~1 image per 0.5–1 Å).

- **`EDIFFG = -0.01`** is a tight (good) force criterion for a CI‑NEB saddle — fine. `NSW=500` is sensible; NEB often wants hundreds of steps, and that's the real limit, not a failure.

- **Smearing (you asked):** `ISMEAR=0, SIGMA=0.05` is correct for a molecule/semiconductor. If this is a **metal surface**, use `ISMEAR=1` (or 2) with `SIGMA≈0.1–0.2` instead — Gaussian + tiny SIGMA converges poorly for metals. Tell me the system if you want a firm call.

The rest (`IBRION=3`, `POTIM=0`, `SPRING=-5.0`, `LCLIMB=.TRUE.`, `ICHAIN=0`) is the correct CI‑NEB skeleton. What's the system — metal surface vs. molecule, and is the cell charged? That determines the smearing choice and whether `NELECT`/screening matters.
