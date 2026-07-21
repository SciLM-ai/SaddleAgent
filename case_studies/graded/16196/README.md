# Topic 16196 — Poor convergence near shallow energy minima

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> This is a good answer.

## Files

The user's complete uploaded files for this topic are in the deep-dive case: [`../../16196-shallow-minima/files/`](../../16196-shallow-minima/files/).

## Original question

**jordanchapman** (2025-11-13 12:41):

Hi all,

I'm interested in calculating the energy barriers of defect formation processes in LiF. While doing these calcs, I'm consistently running into convergence issues. My thinking is that the convergence is sketchy because the energies of the defect geometries I'm using as endpoints are only different on the order of ~0.01 eV. When I run the NEB calcs, I'm finding that the endpoint will not lie at a local energy minimum, for instance, or that there are lower-energy configurations along the MEP that I calculate. 

I've been using the LFBGS optimizer for many of these NEB calcs without issue, especially when the energy differences between the initial and final configurations are >1eV. So, I attempted using the first-order QM optimizer around these shallow energy minima to try to improve the convergence. I'm finding that the convergence is similarly poor using the QM opt, only taking longer than LFBGS. 

I'm wondering if this poor convergence is possibly related to one of several INCAR tags. I've been using the default 0.1 TIMESTEP value, but I worry that dropping the TIMESTEP value wouldn't improve convergence, it would only further increase the calculation time (the early steps of the NEB calcs don't show any high energy barrier). I'm also considering the sensitivity of these calcs to the number of images and the ionic relaxation criteria. I've been using -0.01 eV/A; is it possible that more stringent convergence criteria of the endpoints and along the MEP could resolve some of the issues?

I've attached my OUTCAR, POSCAR, intermediate CONTCAR, and INCAR files for reference. Any advice on resolving this issue is greatly appreciated!

Jordan Chapman

---

**jordanchapman** (2025-11-18 11:18):

This is indeed the case. I started these calculations using only GGA, which showed a PE surface without shallow, nearby minima. I don't think you need to look into these NEB calcs any further, but I do have some general questions:

1. Do you expect that these shallow energy minima I'm finding with hybrid functional calcs are physical results, or are these shallow energy minima artefacts of an HSE-level calc? I'm unfamiliar with the problem you're describing where the shallow energy minima are related to exact exchange.

2. Do you recommend using pure DFT to identify ionic geometries that should be used as endpoints in an NEB calc? Or can you comment on the suitability of hybrid functionals in NEB calcs? For instance, when running a previous NEB calc (converged at PBE level) with HSE-level theory, I similarly find additional energy minima between the transition state and a shallow energy minimum.

3. If these shallow energy minima are physically relevant results, is there a way I can probe the MEPs separating similar ionic geometries without a fully converged NEB calculation. I.e., can I run an NEB calc with loose convergence criteria to get an idea of the atomic motions associated with small transition state?

## Expert answer (forum ground truth)

**graeme** (2025-11-18 09:51):

I'm not going to be much help on this one.  There is very little motion between your initial and final states.  I can see that the endpoint does not appear minimized because it is higher in energy than the band.  I would suggest minimizing from image 02.  And maybe decrease ediffg for the minimization of 04.  If it's really important, I can look into it more, but this looks like small differences in similar states with tiny barriers. I expect the problems of shallow minima are going to be related to including exact exchange.  If you try the same calculation with pure DFT and the problem goes away, that will confirm my intuition.

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**This isn't an optimizer, timestep, or EDIFFG problem — your band's SCF is never converging. You relaxed the two endpoints with `NELM=200` (this system needs ~61 electronic steps to converge), but ran the three moving images with `NELM=20`, so every image caps out at 20 steps and quits with "EDIFF was not reached." The image energies are computed from non-self-consistent densities and are not on the same footing as the endpoints. On a path whose entire energy span is only 57 meV, that electronic inconsistency is larger than the physics you're chasing — which is exactly why image 02 sits *below* your reactant endpoint.** Fix the electronics (NELM + EDIFF), make the band's deck identical to the endpoints', and the spurious "lower-energy configurations" will go away.

## The evidence

**Energy profile, relative to reactant `00/` (E0 in eV):**
``********

| dir | role | ΔE vs 00 |
| --- | --- | --- |
| 00 | reactant (endpoint) | 0.000 |
| 01 | image | +0.005 |
| 02 | image | −0.008  ← below the endpoint |
| 03 | image | +0.026 |
| 04 | product (endpoint) | +0.057 |

The whole reaction span is 57 meV and the interior structure is ~10 meV — your exact symptom of an image dipping below the endpoint.

**The root cause — SCF convergence is inconsistent across the run:**

- Endpoints `00`/`04`: `NELM=200`, SCF **converged** every ionic step (0 capped); `00`'s last step needed **61 electronic iterations** to reach EDIFF.

- Band images `01`/`02`/`03`: `NELM=20`, SCF **hit the cap and never converged** — 10/13, 10/13, and **13/13** ionic steps printed `aborting loop EDIFF was not reached (unconverged)`. Image `03` never once reached electronic convergence.

- `EDIFF=1E-10` is the aggravator: for a 216-atom HSE06 cell it needs ~60 SCF steps (as the endpoints show), so with `NELM=20` it is *guaranteed* to burn all 20 steps and quit unconverged on every image (`docs/vasp/ediff.md`: default 1E-4, 1E-6 recommended, 1E-7 only for forces; `docs/vasp/nelm.md`: default 60).

**Why this rules out your suspects:** the band's *forces* actually did converge — image 02 reached `FORCES: max atom 0.002494` and "reached required accuracy," with clean 0.45 Å/image spacing and ~90° tangent angles. So the **optimizer and timestep are doing their job**; that's why QM behaved the same as LBFGS, just slower. You can't optimize your way out of a noisy/inconsistent potential-energy surface — the failure is electronic (energies), not ionic (forces).

There's a second, smaller inconsistency: endpoints were relaxed with `NUPDOWN=-1` (free moment), the band with `NUPDOWN=0`. For LiF (closed-shell) both should give moment 0, but unify it anyway.

## The fix

In the **band** INCAR, make the electronics match the endpoints and reachable:

```
NELM   = 80          # was 20 — too few; SCF here needs ~61 steps
EDIFF  = 1E-6        # was 1E-10 — unreachable in 20 steps; 1E-6 is plenty for ~10 meV work (use 1E-7 if you want tight forces)
NUPDOWN = -1         # match the endpoints (or re-relax endpoints with NUPDOWN=0 — just be consistent)
```

Everything else (ENCUT 400, PREC, HSE params, POTCAR, the QuickMin block) is already consistent between band and endpoints — leave it. Then:

1. **Restart each image from a WAVECAR** (`ISTART=1` is already set). HSE SCF converges far faster and more reproducibly from a decent wavefunction — pre-converge each image at PBE and carry its `WAVECAR` into the HSE band. This is what makes `NELM=80` actually converge in ~40–60 steps instead of capping.

2. **Re-run the band.** With consistent, converged SCF, re-plot the profile. The 8 meV "well" at image 02 should disappear or shrink into the noise.

**Your specific questions, answered:**

- **TIMESTEP = 0.1** — correct for QuickMin; **leave it.** Lowering it only slows the run (your forces were descending/converged, so it's not the lever — `docs/vtst/optimizers.md`).

- **EDIFFG = −0.01** — fine, and **not** the bottleneck. Do **not** tighten it yet: with the SCF unconverged you'd just be chasing electronic noise. Once the SCF is clean, −0.01 is appropriate for such a shallow path (−0.005 at most).

- **Number of images** — 3 is geometrically fine (0.45 Å/image spacing is well-resolved), but too coarse to capture a shallow, possibly multi-feature path. After the SCF is fixed, bump to **5–7 images and set `LCLIMB=.TRUE.`** — right now `LCLIMB=.FALSE.`, so no image is being driven onto the saddle, and you have no actual barrier (`docs/vtst/neb.md`).

- **QM vs LBFGS** — neither is the problem; stop switching optimizers.

## Reality check

After consistent HSE SCF, if the barrier is genuinely ~10–50 meV, you're near the practical accuracy floor for HSE forces/energies on a 216-atom, Γ-only (`NKPTS=1`) cell. For defect-formation energy *differences* this small, confirm the barrier sits clearly above your numerical noise and sanity-check k-point/cell convergence before trusting it. (Also: LiF is non-magnetic — if your defects don't trap unpaired electrons you can drop `ISPIN=2`→`1` and halve the cost; keep `ISPIN=2` only if a defect is a genuine spin center like an F-center.)

**Confidence:** high on the NELM/SCF mismatch being the root cause — it's directly visible in the OUTCARs. To go further I'd want your `KPOINTS` and the band `OSZICAR`/`neb.dat`, which weren't attached.
