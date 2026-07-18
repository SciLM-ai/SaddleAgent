# Topic 15410 — How to increase resolution of images in NEB method?

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> This is a good response from the AI.

## Original question

**nokimann** (2023-03-02 21:33):

Increasing images requires more computer resources.

If we have multiple TS between locally stable images, we may split the one whole NEB run into separate NEB runs.

However, how can I increase the resolution if I need more images, i.e., the high resolution?

Can I run NEBs as if the following?

1. Run NEB with 4-8 images.

2. Separate paths if there are more than two locally stable images because the initial and final images are at least locally stable.

3. For each separate image, insert interpolated images between the locally stable and TS images (not between two locally stable images). And run NEB without the climbing method.

Is step 3 possible?

I found some comments about the steepest descent method, but how can I apply it?

Moreover, the steepest descent method in the official VTST site seems to purpose on finding TS, not the resolution.

---

**nokimann** (2023-03-06 01:44):

graeme wrote:

> You can certainly add more images by interpolation.  It is best if you can

> try to keep equal spacing, so for example, going from a 4 image to a 9

> image calculation.  You can always keep the climbing image on.

My purpose is to get the proper structures from the high-resolute images during the transition instead of the energy barrier.

I'm using NEB with VASP program.

I thought that each image will be distributed in parallelized nodes to get the MEP with increasing memory.

My cluster is limited in computer resources for more than 32 images, so can I do the NEB without parallelization to save the memory?

I mean NPAR=1 tag in INCAR file. I don't know how parallelization works with NEB.

Moreover, can I believe the calculated intermediate structures describe the real intermediate structures? Because I hope to investigate other intermediate properties instead of the intermediate energies.

## Expert answer (forum ground truth)

**graeme** (2023-03-03 16:03):

You can certainly add more images by interpolation.  It is best if you can try to keep equal spacing, so for example, going from a 4 image to a 9 image calculation.  You can always keep the climbing image on.

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**Steps 1–2 are exactly the standard workflow. Step 3 is possible but mis-framed in two ways: you cannot use "the TS image" as a fixed NEB endpoint, and if your goal is the TS you want climbing *on*, not off.** The clean way to add resolution near a saddle is a **child NEB between the two *adjacent converged images* that bracket the maximum** (they are valid fixed endpoints, no re-relaxation needed) — then a final CI-NEB. And the "steepest descent" you found is two different things: **IOPT=4 is just a (weak) optimizer**, while the *steepest-descent path trace* is for **resolution, and it requires the TS already in hand** — the opposite of what you concluded.

### Step 1–2: correct, this is the doctrine

Relax any intermediate minimum explicitly to its own local minimum, then run the segments A→B and B→C as **separate, independent NEBs** (launch them in parallel — no data dependency). Don't chain both steps into one band: a stretched band wastes images clustering in the deep intermediate well and starves *each* saddle, resolving both barriers worse at equal-or-higher cost.

One caveat that matters: the intermediate is the **shared endpoint** of both segments, so it must be a *true relaxed minimum*. You cannot reconstruct the full MEP by stitching two segments at an *unrelaxed interior NEB image* — that join is not a stationary point. Budget ≥4 images per segment for a reliable MEP (~1 image per 0.5–1 Å of path).

### Step 3: yes, but bracket the TS with two converged images — don't interpolate "minimum → TS"

The flaw: **a NEB needs both endpoints (`00` and `NN`) fixed**, and they should be relaxed minima. The TS is a saddle and is not a fixed structure — it is the *highest image of a converged band*. So "interpolate between the minimum and the TS image and run plain NEB" both (a) puts a saddle at an endpoint and (b) spends new images on the well-resolved low part of the path.

What actually works (`reference/workflows.md`, "Refining the MEP in one region"):

- Take the two **adjacent converged images of the parent band that bracket the maximum**. They already lie on/near the MEP, so they are valid fixed endpoints needing **no re-relaxation** (only the original outer endpoints had to be relaxed).

- Build a **child NEB** between just those two with extra interpolated images. This concentrates resolution exactly at the saddle region, not across the whole minimum→TS span.

- You can recurse (child band between any two converged images) until the bump is resolved. **Keep `EDIFF`/`EDIFFG` identical at every level.**

On "without the climbing method": that depends on your goal.

- **If you want the barrier / TS geometry** — you don't need more images at all. Turn the climbing image **on** (`LCLIMB = .TRUE.`, the VTST default; `docs/vtst/neb.md`). On convergence the climbing image sits at the *exact* saddle regardless of image spacing. Plain NEB (no climbing) never places any image exactly at the saddle, so "more images, no climbing" gives you a finer *picture* but still no TS. Best practice: run plain NEB first to seat the band, *then* enable climbing.

- **If you only want the path shape resolved** — plain NEB with more images (the child NEB above) is fine, and end with one CI-NEB to pin the local max.

### The "steepest descent" confusion — two different things

1.

**`IOPT = 4` (SD optimizer)** on the VTST optimizers page is just a force-based optimizer, labeled *"mainly for testing"* (`docs/vtst/optimizers.md`). It is a generic, slow band/dimer driver — it is **not** a special TS-finding method. (For converging bands, prefer `IOPT=3` Quick-Min or `IOPT=7` FIRE far from the minimum; LBFGS/CG only with accurate forces.)

2.

**Steepest-descent *path tracing*** is the high-resolution tool, and it is the reverse of what you assumed — it is *for resolution* and **needs the TS first**. Once the saddle is known (converged CI-NEB top image, or a dimer saddle) plus its negative-curvature mode:

  - Displace the saddle *slightly* along **+mode** and **−mode**.

  - From each, run a **plain single-structure downhill relaxation** (one structure — no `IMAGES`, no dimer; `ICHAIN=0`) driven by the VTST optimizer with a **small `MAXMOVE`** so each step hugs the MEP:

```
IBRION = 3
POTIM  = 0
IOPT   = 4      # SD (or IOPT = 3, Quick-Min)
MAXMOVE = 0.05  # small — default 0.2 leaves the path
EDIFFG = -0.01  # negative (force criterion)
```

  - The two trajectories roll down into the two basins; their `XDATCAR` frames **are** your high-resolution MEP. `dimmins.pl` (vtstscripts) automates both ± minimizations.

  - 2nd-order optimizers (LBFGS/CG, `IOPT=1/2`) take large steps that leave the path — don't use them here. For best curvature fidelity you'd want **RK4**, which VASP does not implement; drive it from an external tool (vtstscripts).

This is more efficient and more precise than ever-denser recursive bands once a saddle exists.

**Confidence:** high on the workflow logic and the IOPT/`LCLIMB` facts (checked against `docs/vtst/neb.md`, `docs/vtst/optimizers.md`, and `reference/workflows.md`).

**What I'd check next, if you share files:** your `neb.dat`/`nebef.pl` output and image count for the current band — so I can tell you whether you actually need a child NEB at the saddle or just `LCLIMB=.TRUE.` on the existing images, and whether any apparent "intermediate minimum" is a real relaxed basin or just an under-resolved shoulder.
