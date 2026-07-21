# Topic 11977 — What to run after diminit

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> A good response from AI.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**amishkin** (2021-06-05 22:21):

Hello,

What code runs the dimer convergence after it has been created with diminit?

Thanks,

Alec

---

**amishkin** (2021-06-06 14:29):

But isn't there a part of your package that does the dimer convergence? Like calculating the curvature and then rotating the dimer and checking force gradients, etc. I saw in akmc.pl that the GetCurvature is defined but it does not look like it is ever called.

Thanks for the help,

Alec

---

**amishkin** (2021-06-07 13:25):

Thank you very much!

## Expert answer (forum ground truth)

**graeme** (2021-06-06 13:32):

These scripts are set up to work with vasp, with our VTSTcode linked in.

---

**graeme** (2021-06-07 11:43):

Oh yes, I see, you want to set ICHAIN=2 following the instructions here:

http://theory.cm.utexas.edu/vtsttools/dimer.html

## The graded AI answer (SaddleAgent (with Opus 4.8))

**The VTST‑patched VASP binary itself runs the dimer convergence — there is no separate "dimer driver" script.** `diminit.pl` only *creates* the starting point (a `POSCAR` center + `MODECAR` mode, plus copied `KPOINTS`/`POTCAR`/`INCAR`). To actually converge to the saddle you `cd` into that directory and launch VASP exactly like any normal VASP job (`mpirun`/`srun … vasp_std`). VASP's min‑mode optimizer does the rotation+translation loop and writes progress to `DIMCAR`.

What makes that VASP run *be* a dimer run is the INCAR, not the script (`docs/vtst/dimer.md`):

| Tag | Value | Why |
|---|---|---|
| `ICHAIN` | `2` | selects the VTST external dimer method (required) |
| `IBRION` | `3` | VASP does MD with a zero time step (lets VTST move the ions) |
| `POTIM` | `0` | VASP itself takes no step |
| `IOPT` | `>0` (e.g. `2`) | the optimizer that drives translation; **a dimer run with no `IOPT` dies with an error** |
| `EDIFFG` | `<0` (force criterion) | converged when DIMCAR `Force` < `|EDIFFG|` **and** curvature is negative |

So the chain is: `diminit.pl` (build inputs) → **run the VTST‑patched VASP in the dimer dir** (does the convergence) → watch `DIMCAR` / `dimplot.pl`.

Two things worth flagging:

- **The binary must be VTST‑patched.** If `ICHAIN=2` is rejected at launch, or the job "finishes" all `NSW` steps with no ionic motion, vtstcode isn't linked. Quick check: `grep VTST OUTCAR` should show a `VTST: version` banner.

- **Don't confuse this with VASP's *native* dimer.** Stock VASP has its own improved dimer at `IBRION=44`, which needs no VTST and no `ICHAIN`/`MODECAR`. The `diminit.pl`/`MODECAR` workflow is the **VTST external dimer**, so use `ICHAIN=2` (+`IBRION=3`, `POTIM=0`), *not* `IBRION=44` (`docs/vtst/dimer.md`).

Confidence: high — this is from the bundled `docs/vtst/dimer.md` and the `diminit.pl` entry in `docs/vtst/scripts.md`. If you tell me how you launch your other VASP jobs (scheduler + binary name), I can give you the exact submit line and a ready‑to‑run dimer INCAR block.
