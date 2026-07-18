# Topic 16198 — CO2 gas formation NEB does not converge well

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> There are some accurate statements from the AI, but as usual, when there are inaccurate statements, it makes the entire response seem sketchy.  So yes, resolution is a problem, and in my response I just went to 8 images and got nice convergence.  This business about breaking up the band is not a terrible idea, but it is also not the key problem.  Again, I relaxed the full band with 8 images.  Sure, there may be an intermediate minimum, but that is not a serious problem.  Also, I firmly reject the notion (which I have heard many times) that users should to NEB before CI-NEB.  If your 'clever' AI brain can show me an example, I would be eager to see it.  I could cook up a pathological case, but my advice is always to use climbing image from the start; an NEB pre-relax only wastes computer time.

## Files

The user's complete uploaded files for this topic are in the deep-dive case: [`../../16198-co2-neb/files/`](../../16198-co2-neb/files/).

## Original question

**shkwon** (2025-12-07 22:02):

Hello,

I have simulated the NEB calculation on CO2 gas formation on Pd (111) surface.

The results showed that it has multiple barriers. 

I expected one single barrier at the initial phase of the CO2 formation.

I simulated this system directly setting climbing image, no initial regular NEB.

Is that could be a problem? Or maybe other problem such as final phase CO2 gas is too above the surface or too low image numbers... 

I have attached the calculation files.

Thank you.

## Expert answer (forum ground truth)

**graeme** (2025-12-09 12:18):

There are two problems with the calculation.  First, you have a fairly long path.  Most of the path involves CO2 moving away from the surface.  With only 4 images, only 1 is really involved in the reaction step.

Second, for CO2, you will need a smaller timestep.  This is because CO2 has high frequency modes.  In your endpoints you used CG, which is why they converged.  Note, you can used the default CG from vasp with NEB.

In the attached I used 8 images and a time step of 0.05 with quickmin (IOPT=3) and the convergence is smooth.  I didn't quite finish it because I wanted to write back, but if you do continue it will converge.  That said, notice that there is a lower initial state.  Putting it another way, the CO would prefer to first hop along the surface and then combine with O to form CO2.  If you do a similar band, I recommend minimizing image 02 to get a new (lower energy) initial state.

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**Your own second guess is the real problem: the final image is gas‑phase CO₂ floating ~4.8 Å above the Pd top layer, so your band bundles *two* physical processes into one path — (1) the C–O bond‑forming chemical step at the surface and (2) CO₂ desorption lifting the molecule ~3.4 Å off the slab. That is exactly what produces the multi‑hump profile.** Two secondary issues compound it: the band is **far from converged** (images 03/04 sit at ~17 eV/Å vs your `EDIFFG = -0.026`, and the job crashed with an MKL/FFT error), and at 4 images over an 8.5 Å path you have **~1.7 Å/image** — badly under‑resolved. Going straight to climbing‑image with no plain‑NEB pre‑relax made it worse but is not the root cause.

The fix is to redefine the final state as the *adsorbed* CO₂ (not gas‑phase), rebuild the band, and run regular NEB before turning on the climb.

## Evidence from your files

- **Version is fine** (`01/OUTCAR`): `vasp.5.4.4` + `VTST: version 3.2` — VTST is linked, so this is not a build/tag problem.

- **The two endpoints are different processes** (`00/POSCAR` vs `05/POSCAR`, cell c = 16.52 Å, top Pd layer at z≈0.44 → 7.3 Å):

  - IS (00): C at z≈8.65 Å (~1.4 Å above the surface) bonded to one O = **CO*** + a separate atomic **O*** adsorbed nearby. A surface co‑adsorbed state.

  - FS (05): C, O, O all clustered at z≈12.0 Å = a **CO₂ molecule ~4.8 Å above the top Pd layer** — i.e. desorbed gas.

  - So the path = O migrates toward C, the C–O bond forms, *and then* CO₂ lifts ~3.4 Å off the slab and floats away. Three structural changes, hence multiple humps.

- **`neb.dat` profile** (cols = `index dist relE force`): rel. energies 0 → +0.22 → +0.07 → **+0.80** → +0.71 → −0.46. The dip at image 2 then a peak at image 3 is the classic "two processes in one band" shoulder. Image spacing ≈1.68–1.72 Å each (`dist` column), >1 Å/image.

- **Not converged — barrier numbers are meaningless:** `reached required accuracy` appears only in `00` and `05` (the endpoints). Interior `FORCES: max atom` last steps: 01≈0.18, 02≈0.29, **03≈16.8, 04≈17.3 eV/Å**. (The near‑zero `force` for image 3 in `neb.dat` is the *along‑path* tangential force, ~0 at any maximum by construction — not the convergence force.) The `.e` file also shows an MKL `DftiCreateDescriptor` FFT crash, and the per‑image step counts differ (121/113/66/70), so the run ended abnormally, unconverged.

## What to do

1. **Redefine the final state as adsorbed CO₂*, not gas‑phase CO₂.** Relax a CO₂ molecule sitting on/near the Pd(111) surface (same cell, same `INCAR`/k‑points) and use *that* as image 05. CO₂ is only weakly bound on Pd(111), so its desorption is essentially barrierless — get that energy from the adsorption energy (or a simple height scan), **don't put it in the NEB**. The barrier you actually want (CO* + O* → CO₂*) is the surface chemical step.

2. **Rebuild the band over the now‑short path** with `nebmake.pl` (IDPP is its default and avoids the unphysical straight‑line geometries that blew images 03/04 up). With the near‑surface FS the path collapses to ~1–2 Å, so **4–6 images** gives ≤~0.5 Å/image — plenty for one step. Keep adding images only until the climbing image's own force meets `EDIFFG`.

3. **Run plain NEB first, then climb.** Set `LCLIMB = .FALSE.`, converge the band to ~0.3–0.5 eV/Å, then restart from the `CONTCAR`s with `LCLIMB = .TRUE.` to seat the saddle. So yes — your instinct about skipping regular NEB is a real (secondary) contributor: launching CI directly on a poor interpolation that threads the desorption region is part of why the middle images diverged.

4. **Before submitting, play the initial band** (`nebmovie.pl`) — every atom should move smoothly and sub‑Å per image, and *only* the reacting C/O atoms should move. If the whole molecule still translates several Å, your endpoints are still encoding desorption.

Your optimizer deck is otherwise correct and needs no change: `IOPT=3` (Quick‑Min) + `IBRION=3` + `POTIM=0` is the right VTST driver; commented `TIMESTEP` defaults to 0.1, which is fine. `EDIFFG=-0.026` is acceptable (you can tighten to −0.02 once the path is sane).

**Confidence:** high on the root cause (the FS geometry and the multi‑hump+unconverged profile are unambiguous in your files).

One thing I couldn't see: whether you intend CO₂ to ultimately leave as gas. If the desorption energetics matter to you, compute them as a separate adsorption‑energy step — but keep them out of the formation NEB. If you want, share the relaxed CO₂* adsorbed structure and I'll sanity‑check the rebuilt endpoints and image count.
