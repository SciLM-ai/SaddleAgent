# Topic 12368 — Question related to TS_Extract.sh and DIMCAR

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> This is a sensible response from AI.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**spbatchu** (2021-10-04 08:42):

Hello Dr. Henkelman

I have questions related to a couple of topics; one topic being TS_Extract.sh and the other being the DIMCAR file. The questions are as follows: 

1) regarding the output displayed upon using TS_Extract.sh, 

i) What does E-E0 mean? What value is chosen as E0? 

ii) What exactly do Angle, k previous and k next mean? 

2) regarding DIMCAR 

i) Whenever I look at my DIMCAR after my dimer calculation is complete, I notice that the F Max displayed in the DIMCAR is different from that in the OUTCAR. The F Max in the OUTCAR matches with the ediffg but the F Max in DIMCAR doesn't. Any specific reason behind this? 

ii) What exactly do Torque and Angle mean/correspond to in the DIMCAR file?

iii) In the DIMCAR file, I notice that the values of torque, curvature, and angle are not displayed in the last iteration. Any specific reason behind this? 

Your answers will be of great help. Thanks in advance

## Expert answer (forum ground truth)

**graeme** (2021-10-05 11:45):

I'm not sure about the TS_Exact.sh script - I don't think that is one of ours.  If I were to guess, however, E0 would be the energy of the initial image so that E-E0 would be the relative energy along the path.  The angle, would likely be the angle between the previous and next image at each image, and k_prev and k_next would be the spring constants to the previous and next images.

The force displayed in the DIMCAR is the magnitude of the projected force at the center of the dimer.  This can be different from what is calculated in the OUTCAR when the image is displaced from the center of the dimer.  Also, F Max is the maximum force on any atom, which is used as the convergence criterion for EDIFFG.  When using the dimer method, we use the same criterion - so we calculate the max force on any atom (but don't print that in the DIMCAR).  When we reach that force, there is one more call to the dimer code in which is does nothing, and prints that final line, and then returns control back to vasp to also decide that the calculation is converged so that it cleans up and quits.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Bottom line:** Most of your questions have clean answers from how the dimer/NEB code reports its numbers. The one genuine gotcha is 2(i): the DIMCAR "F Max" and the OUTCAR force are *different quantities* — DIMCAR reports the mode‑projected force at the dimer center, while VASP tests `EDIFFG` against the plain per‑atom max in OUTCAR, so only the OUTCAR value should ever match your criterion. The missing torque/curvature/angle on the last DIMCAR line is also expected, not a bug. One caveat up front: `TS_Extract.sh` is **not** part of the core vtstscripts set I have authoritative docs for (those are the `.pl`/`.py` tools), so for question 1 I'm answering from the standard NEB output convention its column names point to — paste the script (it's short) or a couple of lines of its output and I'll confirm the exact definitions.

## 1) TS_Extract.sh output

**i) E‑E0, and what E0 is.** This is the universal NEB energy‑referencing convention: each image's energy is printed *relative to a reference* `E0`, and `E0` is the energy of the **initial endpoint — image `00`, the reactant**. That's exactly how the core post‑processors define it (`nebbarrier.pl`: "energies referenced to image‑00"; `nebef.pl`: "energies referenced to the first image" — `docs/vtst/scripts.md`). So `E-E0` puts the reactant at 0, and the **barrier is simply the largest `E-E0`** (your TS image). `E0` itself is the absolute DFT total energy `energy(sigma→0)` of `00/OUTCAR`.

**ii) Angle, k previous, k next.**

- **Angle** — the *bend in the path at that image*: the angle between the vector pointing to the **previous** image and the vector to the **next** image. This is VASP's per‑image OUTCAR line `NEB: distance to prev, next image, angle between`. On a smooth path it's ≈ **180°**; an interior image dropping toward ~90° or below flags a **kink or an intermediate minimum** the path is wrapping around (`reference/dimer-diagnostics.md`, neb2dim seed diagnostics).

- **k previous / k next** — the **spring constants** coupling the image to its previous and next neighbours along the band (set by `SPRING`, default `-5.0` eV/Å²; `docs/vtst/neb.md`). With the energy‑weighted (variable) spring scheme the two sides need not be equal, hence separate "previous"/"next" values. *This is the one column pair I'd like to confirm against the actual script* — send it over and I'll verify whether these are spring constants or projected spring forces.

## 2) DIMCAR

**i) Why DIMCAR "F Max" ≠ OUTCAR F Max (and only OUTCAR matches EDIFFG).** These are two different forces:

- **DIMCAR "F Max" (column 2)** is the **mode‑projected effective force at the dimer center** — the translational force the dimer actually steps on, with the component along the lowest (negative‑curvature) mode inverted. It's a different quantity from any single Cartesian force, and at convergence it can remain comparatively large or even roughly constant.

- **OUTCAR `FORCES: max atom`** is the plain **per‑atom maximum Cartesian force** (the 2nd, "by dimension" column of `FORCE total and by dimension`).

VASP applies the `EDIFFG` convergence test to the **OUTCAR per‑atom max**, which is why that one lines up with your `EDIFFG` and the DIMCAR value does not. This is by design, not an inconsistency (`docs/vtst/dimer.md`; `reference/dimer-diagnostics.md`). **Rule: judge convergence by OUTCAR `FORCES: max atom` together with a negative `Curvature` — never by the DIMCAR Force column.**

**ii) Torque and Angle.** Both come from the dimer's *rotation* phase, where it aligns its axis with the lowest‑curvature mode (`docs/vtst/dimer.md`):

- **Torque (column 3)** — the **rotational force on the dimer**, i.e. the force perpendicular to the dimer axis that drives it to rotate toward the true lowest mode. It measures how accurately the current axis represents that mode: large torque = axis not yet aligned. It is a *health/accuracy* indicator, **not** a convergence criterion, and it need not decrease monotonically step‑to‑step (`reference/dimer-diagnostics.md`).

- **Angle (column 6)** — the **angle (degrees) the dimer was actually rotated through** on that step. It starts large and should drop and stay small; a residual **1–2° at force convergence is normal** (don't wait for it to hit zero). A *persistently* large angle alongside high torque that won't respond to `DRotMax` points to noisy forces (tighten `EDIFF`→1e‑7/1e‑8, freeze deep layers, `LREAL=.FALSE.`).

**iii) Why torque, curvature, and angle are blank on the last iteration.** Expected. The convergence test is applied to the dimer **center** force at the *start* of an iteration, *before* any rotation. When a translation step brings the center below `|EDIFFG|`, the next pass detects convergence immediately and **exits before performing a rotation** — so there is no rotational force (torque), no freshly estimated curvature, and no rotation angle to write, and those three columns are left dashed/blank on that final line. It's the same mechanism that produces a single dashed DIMCAR row when you hand the dimer an already‑converged structure (`reference/dimer-diagnostics.md`). (Any non‑final step can also skip rotation — and thus those columns — when the rotational force falls below `DFNMin`, default `0.01`, the threshold "below which the dimer is not rotated"; `docs/vtst/dimer.md`. But for the *last* line specifically, it's the convergence exit.)

Confidence: high on 1(i), 2(i), 2(ii), 2(iii) — these are standard, documented reporting conventions. Lower on the `k previous`/`k next` labels in 1(ii) only because `TS_Extract.sh` itself isn't in the script bundle I can verify against. If you paste the script or a sample of its printed table, I'll pin those two columns down exactly.
