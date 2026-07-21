# Topic 16187 — Re: Shape of MEP curve

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> AI gets this completely wrong.  The problem with the calculation is that the VTSTcode is not linked into the vasp binary and so when the VTSTscripts grep for NEB forces (which the VTSTcode prints), it does not find them and defaults to zero.  That is the real reason why the spline has a zero slope at each image.

## Files

`files/` — the complete upload (50 files; `POTCAR` excepted, for licensing).

## Original question

**manishk** (2025-06-09 10:28):

Hi All,

I was performing NEB, but not getting the smooth shape of the mep curve (attached). What could be the possible reason for this?

Here are the settings of my INCAR file

ADDGRID = True

ALGO = Fast

EDIFF = 1e-06

EDIFFG = -0.05

ENCUT = 520.0

IBRION = 1

ISIF = 2

ISMEAR = 0

ISPIN = 2

ISYM = 0

LASPH = True

LDAU = True

LDAUJ = 0 0 0 0

LDAUL = 0 0 2 0

LDAUPRINT = 1

LDAUTYPE = 2

LDAUU = 0 0 4.38 0

LMAXMIX = 4

LORBIT = 11

LREAL = False

LWAVE = False

MAGMOM = 93*0.6

NELM = 100

NELMIN = 3

NSW = 450

POTIM = 0.2

PREC = Accurate

SIGMA = 0.05

IMAGES = 7

SPRING = -5.0

ICHAIN = 0

LCLIMB = .TRUE.

LNEBCELL = .FALSE.

IOPT = 3

I am using vasp version 6.3.2

---

**manishk** (2025-06-09 11:00):

Thanks for the quick reply.

I have checked the OUTCAR of an image and found that the VTST is not linked to VASP.

## Expert answer (forum ground truth)

**graeme** (2025-06-09 10:40):

I would have to see your calculation, but my guess that that you do not have our vtstcode linked into vasp and so it is not extracting the forces at each image.  If those forces are zero, the spline will have a derivative of zero at each image.  You can grep for VTST in any OUTCAR file to check if the vtstcode is link into your binary.

Another possible reason is that there is net translation and/or rotation along your path.  If the distance between images is not consistent with the force at each point, the spline will look weird.  The solution to that is to freeze one atom in the same position for each image.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Your MEP isn't "non-smooth" because of bad physics — the band simply isn't converged yet, and the reason it can't converge cleanly is a broken optimizer setup in your INCAR. `IOPT=3` (VTST Quick-Min) requires `IBRION=3` and `POTIM=0`, but you have `IBRION=1` and `POTIM=0.2`. So VASP's own quasi-Newton optimizer — not the VTST optimizer you asked for — is driving the band, and `EDIFFG=-0.05` lets it stop while forces are still large. Fix the three tags, tighten `EDIFFG`, and continue from your CONTCARs; the kinks will smooth out.**

### Why the curve looks kinked

`nebspline.pl`/`nebresults.pl` builds the curve by fitting, at *each* image, both its **energy** and its **path-perpendicular force** (the local slope). When the band is converged those two are consistent and the spline is smooth. Below convergence they disagree, and the spline overshoots into exactly the shoulders/inflections you see flanking the peak (~0.6 eV on both sides). With `EDIFFG=-0.05` your images can still carry ~0.05 eV/Å of residual force — more than enough to make those bumps. They are residual-force noise, **not** a real flat-top saddle or intermediate (you can't tell which until forces are tight).

Your image count is *not* the problem: 7 images over a ~3.2 Å path ≈ 0.4 Å/image, well under the ~1 Å/image resolution limit.

### The concrete bug

Per the VTST docs (`optimizers.md`, `POTIM` wiki): to use a VTST `IOPT` optimizer you **must** set `IBRION=3` and `POTIM=0` so VASP doesn't move the ions and the `IOPT` optimizer does. You set `IOPT=3` but left `IBRION=1`, `POTIM=0.2` — i.e. you asked for two different optimizers at once. With `POTIM≠0` VASP's quasi-Newton (`IBRION=1`) is the one actually stepping the ions, using the NEB-projected force. That force includes springs and a projection, so it is **not** the gradient of a single energy — quasi-Newton's Hessian model assumes it is, so it relaxes the band poorly and leaves kinks.

### Fix — edit these tags, then continue (don't restart)

```
IBRION = 3        # was 1
POTIM  = 0        # was 0.2  → VASP makes no move; VTST IOPT does
IOPT   = 3        # keep (Quick-Min); TIMESTEP defaults to 0.1
EDIFFG = -0.03    # was -0.05; use -0.01 to -0.02 for the final barrier
```

Restart from the partially-relaxed band rather than throwing it away: in each image dir copy `CONTCAR → POSCAR` (`for d in 0[1-7]; do cp $d/CONTCAR $d/POSCAR; done`), then resubmit. `NSW=450` is fine (NEB wants 100s of steps); `SPRING=-5.0`, `ENCUT`, `EDIFF=1e-6`, `LMAXMIX=4` are all reasonable.

### Verify

- Confirm the VTST optimizer actually engaged this time: `grep 'OPT: QM, TIMESTEP' OUTCAR` should now appear (it won't have, with your old deck).

- Check the real convergence criterion — the NEB-projected force — not the picture: `nebef.pl`, or `grep 'FORCES: max atom' */OUTCAR`, against `|EDIFFG|`. Once every image (incl. the climbing image) is below it, re-run `nebresults.pl` — the shoulders should collapse into a clean hump. If a shoulder *survives* tightly converged forces, it's then a real feature (broad saddle or shallow intermediate), not an artifact.

### One secondary check (you're DFT+U, spin-polarized)

Your profile is clean and roughly symmetric, so the magnetism is probably fine — but since this is `LDAU` + `ISPIN=2` with a blanket `MAGMOM=93*0.6`, glance at `grep -e magnetization */OUTCAR` for any single image whose moment falls off the smooth IS→FS trend. An image stuck on a different magnetic minimum can also distort the path; if you see one, set explicit `MAGMOM` interpolated from the relaxed endpoints.

Confidence: high that the optimizer-tag mismatch + loose `EDIFFG` is the cause (both confirmed against the VTST docs). To pin it down completely I'd want your `OUTCAR` (or `nebef.pl` output) and `neb.dat` — they'd show whether the run stopped at `EDIFFG` and what residual force the images carry.
