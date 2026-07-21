# Topic 16186 — NEB with charged defect using vtstcode-205

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> The AI is correct and actually noted problems that the expert did not see in terms of electronic convergence.  That said, the real problem with the NEB calculations is a mis-ordering of atoms between the initial and final states so that atoms are too close in the intermediate images.  These are somewhat orthogonal problems; there has to be electronic structure convergence, which the AI describes, but the initial band also has to make sense; it does not and the AI failed to notice that serious problem.

## Files

The user's complete uploaded files for this topic are in the deep-dive case: [`../../16186-charged-defect-neb/files/`](../../16186-charged-defect-neb/files/).

## Original question

**jordanchapman** (2025-06-06 12:39):

Hi all,

I'm attempting to find an energy barrier for the migration of an anionic vacancy in LiF. I've been able to run calculations with a neutral defect (i.e., the number of electrons matches the expected number from the POSCAR + POTCAR files), but I'm running into an issue when performing a similar calc with one fewer electron. Specifically, the electronic optimization initializes until NELM=5, when I get the following message from VASP:

BRMIX: very serious problems

 the old and the new charge density differ

 old charge density:  1073.00000 new 1072.00000

The end points were both geometry-relaxed with the following INCAR tags:

! initialization

System = LiF

ISTART = 1       

ICHARG = 2

NCORE = 8

ISPIN = 2

NELM = 200

ENCUT = 400

PREC = Accurate

ISMEAR = 0; SIGMA = 0.01

EDIFF = 1E-10

! ionic relaxation

NELECT = 1072 ! 1073 neutral

IBRION = 3

NSW = 500

POTIM = 0.1

ISIF = 0

IOPT = 1

EDIFFG = -0.010

And the NEB routine I'm trying to run uses the following INCAR tags:

! initialization

System = LiF

ISTART = 0       

ICHARG = 2

NCORE = 8

ISPIN = 2

NELM = 20

ENCUT = 400

PREC = Accurate

ISMEAR = 0; SIGMA = 0.01

EDIFF = 1E-10

ALGO = Normal

! ionic relaxation

NELECT = 1072 ! 1073 neutral

IBRION = 3

NSW = 500

POTIM = 0

ISIF = 0

IOPT = 1

EDIFFG = -0.010

! NEB

ICHAIN = 0

IMAGES = 5

SPRING = -5.0

LCLIMB = .FALSE.

I'm a bit perplexed by this error message. The endpoints were run with the same number of electrons, and converged to the above specs; I verified in the INCAR that there were 1072 electrons in the final electronic configuration. I tried running the NEB calc with ICHARG=0 + ISTART=0, but ran into the same error. I also tried changing the ALGO to Fast and VeryFast. If anyone could provide any insight as to why VASP isn't reading NELECT from the NEB INCAR file (or if there's an oversight I'm not seeing), I would greatly appreciate it.

Jordan Chapman

VTNSI

---

**jordanchapman** (2025-06-06 14:24):

Thanks for getting back to me quickly. I've attached a zip file containing the parent directory for the NEB calcs. 

To your reply, the WAVECAR and CHGCAR files weren't generated at any point in the runs for the intermediate geometries. I included the OUTCAR files of the endpoints, too. I've linked the VTST source code with version 6.4.2 of VASP, FYI.

## Expert answer (forum ground truth)

**graeme** (2025-06-06 12:52):

If you post the calculation, I can take a look, but I expect that you need to remove and CHG* and WAV* files.  It will read those files by default and if you have changed the number of electrons in your INCAR file, vasp will complain.

---

**graeme** (2025-06-06 17:34):

The problem is that in your initial band, you have atoms running into each other.  Take a look at the initial movie in a viewer and you will see the problem.  Also, there is a warning in each ??/OUTCAR that atoms are too close - you can see it in the neighborlists.

The problem is a result of atom ordering; make sure that each atom in your initial structure corresponds to the same atom in the final structure.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**The BRMIX error is not VASP ignoring NELECT — it's the opposite. VASP *is* reading `NELECT=1072` (that's your "new" charge density). The "old: 1073" is a leftover *neutral* charge density/wavefunction being read from `CHGCAR`/`WAVECAR` files sitting in your image directories. Old − new = 1073 − 1072 = exactly your one removed electron. Delete `CHG*` and `WAV*` from every image (and endpoint) directory and rerun.**

### Why this is the cause

The signature is textbook for a charged-defect NEB started on top of stale density (observed on VASP 6.4.2 / vtstcode-205):

- The mismatch is **exactly the electron-count change** (1 e⁻), not a random sloshing amount.

- It fires **at the first few NELM steps** (your "until NELM=5"), because VASP reads the old density at SCF startup, finds it integrates to the wrong electron count, and the mixer screams `BRMIX: very serious problems`.

- `1073` is the **neutral** count from POSCAR+POTCAR — i.e. a density produced by a run that had the full electron count, not your charged endpoints.

So NELECT is fine. The starting density is the problem.

### The fix

From the NEB working directory (with image dirs `00`–`06`):

```
rm [0-9][0-9]/CHGCAR [0-9][0-9]/WAVECAR
```

Keep your existing `ISTART=0 ICHARG=2` (atomic superposition → built from scratch, then correctly renormalized to NELECT=1072). The interior images `01`–`05` are the ones VASP actually computes, but clear all dirs to be safe.

### Why your attempts didn't work

Flipping `ICHARG=0`/`ISTART=0` and changing `ALGO` doesn't help **because the stale files are still physically present and get picked up regardless** — deleting them is the only reliable cure. Likewise `ALGO=Fast/VeryFast` only changes the SCF algorithm, not what density it starts from.

### Two things to fix before you trust the barrier

Once it runs, your current electronic deck will quietly give you a bad barrier:

1.

**`NELM=20` with `EDIFF=1E-10` is a trap.** A charged defect with `ISMEAR=0; SIGMA=0.01` will not reach 1E-10 in 20 steps. Every image will hit NELM unconverged, and the VTST optimizer will then minimize *non-self-consistent* forces and still report "converged" — a silently wrong barrier. For a saddle *search*, `EDIFF≈1E-5` is plenty (tighten to ~1E-7 only for a final reconverge/frequency). Use something like `EDIFF=1E-6`, `NELM=60`. Keep `ALGO=Normal` (good choice for charged cells; avoid `VeryFast` here).

2.

**Charged cell = automatic uniform compensating background.** That's fine for a barrier where *q* and the cell are constant along the path (the spurious term largely cancels), but the absolute energies carry a finite-size electrostatic error. If you ever compare formation energies, apply a finite-size correction (FNV/Makov–Payne); for migration of a fixed charge state, the barrier itself is usually safe. (If you want to kill the background-charge artifact entirely, VASPsol `LSOL` screens it locally — optional.)

Your `IBRION=3 / POTIM=0 / IOPT=1` setup is correct (stepping handed to the VTST L-BFGS optimizer).

### Confidence and what to check

High confidence on the root cause — the exact-integer charge mismatch is diagnostic. To confirm before/after:

```
ls [0-9][0-9]/CHGCAR [0-9][0-9]/WAVECAR     # should show the stale files now
grep -L BRMIX 0*/OUTCAR                      # after the fix: no BRMIX
grep NELECT 01/OUTCAR                        # should echo NELECT = 1072
```

If after deleting the files you *still* see `old: 1073`, send me one interior image's `OUTCAR` head (the line where it reports the initial charge) and an `ls -la` of that dir — that would point to a neutral file being copied in by your setup script.
