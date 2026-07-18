# Topic 16173 — How to Handle TS with Lower Imaginary Frequency than Preceding NEB Images?

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> AI is correct.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**nidhit** (2024-11-16 14:49):

I obtained the transition state (TS) using the CI-NEB method with 5 intermediate images. The image corresponding to the TS has an imaginary frequency of ~350-400 cm⁻¹ and the highest energy along the pathway. However, when I interpolated more images between the converged 5 images along the reaction path, I noticed that the preceding two images (lower in energy by ~0.04 eV and ~0.2 eV, respectively than the TS) have significantly higher imaginary frequencies (~890 and 1100 cm⁻¹).

When I re-ran CI-NEB with the coordinates of these preceding images (as potential TS candidates), the optimization converged back to the same TS with ~350 cm⁻¹ as the imaginary frequency. I also tried connecting the preceding image and the TS through CI-NEB, but no barrier was observed. 

My questions are:

How do I ensure that the TS is correctly identified?

Are there any specific changes needed in my VASP input file to improve convergence or accuracy? Here are my current settings:

LSCALAPACK= .FALSE.  

NPAR=1  

LREAL = Auto  

ISYM= 0  

ALGO= FAST  

ENMAX=800  

EDIFF= 1E-6  

EDIFFG= -0.01  

POTIM= 0.015  

IBRION= 5  

NFREE= 2  

ISIF= 2  

ISPIN= 2  

ISMEAR= 2  

SIGMA= 0.2  

ADDGRID= .TRUE.  

LCHARG= .FALSE.  

LWAVE= .FALSE.  

IVDW= 12  

The PES does not seem flat, so I am puzzled about why these preceding images show higher imaginary frequencies. Any guidance or suggestions would be highly appreciated!

---

**nidhit** (2024-11-17 09:15):

Thank you for your response! Can I confidently report  the TS obtained via CI-NEB with an imaginary frequency of ~300 cm⁻¹ as the TS, even though preceding images show higher imaginary frequencies (~800-1100 cm⁻¹)? Would an IRC calculation be necessary to further confirm the TS, or is this setup sufficient to validate my results?

---

**nidhit** (2024-11-17 12:51):

Thank you for the clarification. I now understand that this is not a problem as long as the TS itself satisfies the criteria of a first-order saddle point.

## Expert answer (forum ground truth)

**graeme** (2024-11-16 19:53):

I don't see any problem with configurations away from the TS having higher or lower negative curvatures.  I can think of situations where either case will occur.

---

**graeme** (2024-11-17 09:19):

I just don't understand where this concern is coming from.  A first order saddle is defined as a point on the potential with zero force and one negative mode. There can be lots of other points on the potential surface with lower negative modes - but who cares?

To your other question: you can calculate the IRC if you want to but it is not 'necessary' to confirm a saddle.  Again, a first order saddle is defined as a point on the potential with zero force and one negative mode.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Your TS is correct — the "imaginary frequencies" at the preceding images are meaningless because those images are *interpolated, non-stationary points* (force ≠ 0), and a harmonic frequency is only defined where forces ≈ 0.** At an arbitrary point on the uphill slope to the saddle the Hessian eigenvalues are just local PES *curvatures*, not vibrational frequencies; many Cartesian directions there can have negative curvature, so you get large spurious "imaginary" values (your 890, 1100 cm⁻¹). They tell you nothing about where the TS is. Your two CI-NEB tests already prove the 350–400 cm⁻¹ point is the real, unique saddle.

## Why the preceding-image frequencies are not real

A normal-mode analysis (`IBRION=5`) assumes the geometry is a stationary point and diagonalizes the Hessian there. Run it on a point with a net gradient and you still get 3N eigenvalues, but they are not frequencies — and their magnitude has no relation to barrier height or to "being a TS." That's exactly why a *lower-energy* point shows a *bigger* "imaginary frequency": it's just steeper local downhill curvature on the slope, not a deeper saddle. The PES isn't flat; you're simply sampling the curvature off the stationary point.

Your own evidence confirms this — and it's strong:

- **Re-running CI-NEB from the preceding images converges back to the same 350 cm⁻¹ TS** → those images are *not* separate stationary points; they relax back to the one true saddle.

- **CI-NEB between a preceding image and the TS shows no barrier** → monotonic uphill, no intermediate saddle exists. There is one TS, and you have it.

So: **never compute or interpret frequencies at band/interpolated images.** Frequencies are meaningful only at the relaxed minima and the relaxed saddle (the highest-energy CI-NEB image). A relatively low TS imaginary frequency (350 cm⁻¹) is perfectly normal — it just means a broad/flat barrier top.

## How to *properly* confirm the TS (all at the saddle geometry only)

1. **It is the highest-energy image of the converged CI-NEB** — defining criterion, you have it.

2. **Exactly one significantly-imaginary mode** (you have one; discard any near-zero modes — for a slab expect ~3 near-zero translational modes that often read slightly imaginary, don't count them).

3. **The imaginary-mode eigenvector points along the reaction coordinate** — this is the check you haven't reported. Look at the eigenvector in the `OUTCAR` (the `f/i` block) and confirm the displacement vector connects reactant → product, not some spectator motion. A one-mode saddle for the *wrong* coordinate is the only real failure mode left, and your no-barrier CI-NEB test makes that unlikely.

4. *(Optional, gold standard)* Displace the saddle ±0.1 Å along that imaginary mode and run a **plain downhill relaxation** from each; they should fall into your reactant and product basins.

## INCAR changes — for the frequency run specifically

Your relaxation deck is mostly fine; the issue is force/Hessian accuracy at the saddle. For the `IBRION=5` confirmation run:
``**``********````````````**``**``````````**``**``````````**````**````**``````****``````````

| Tag | Now | Change to | Why |
| --- | --- | --- | --- |
| Saddle geometry | EDIFFG=-0.01 | re-relax to EDIFFG ≤ -0.002 saddle-preservingly (continue CI-NEB or hand to a dimer — never a plain IBRION=1/2 minimization, which slides off the saddle) | -0.01 is the search default and is too loose for a clean Hessian; residual gradient surfaces as spurious extra negative modes (docs/vasp/ediffg.md, reference/workflows.md). |
| EDIFF | 1E-6 | 1E-7 (or 1E-8) for the freq run | Finite-difference forces need tight SCF; 1E-6 is fine for relaxation, loose for a Hessian (docs/vasp/ediff.md, docs/vtst/dynmat.md). |
| LREAL | Auto | .FALSE. if the cell is ≲30 atoms | Real-space projectors add a systematic force error; reciprocal space is more accurate for the Hessian (docs/vasp/lreal.md). If large, keep Auto but stay consistent with the relax. |
| ISMEAR=2, SIGMA=0.2 | — | grep OUTCAR for the EENTRO / T*S per atom; if it's not ≲1 meV/atom, drop to ISMEAR=1, SIGMA=0.1 (metal) or ISMEAR=0, SIGMA=0.05 (gap) | MP-order-2 with σ=0.2 can put noise/entropy into forces, polluting frequencies. Keep the same smearing as the relax (docs/vasp/sigma.md, docs/vasp/ismear.md). |
| POTIM=0.015 | — | keep, but treat as a convergence parameter: if any mode looks marginal, scan 0.015→0.01→0.005 Å (with tight EDIFF) and accept where modes stabilize | No universal step; 0.015 is the VASP ≥5.1 default for IBRION=5/6 and is fine for a clear mode (docs/vasp/potim.md, reference/workflows.md). |

`NFREE=2` (central differences), `ISIF=2`, `ADDGRID=.TRUE.` are all appropriate — leave them.

**Confidence: high** on the diagnosis (your two CI-NEB tests are conclusive — the 350 cm⁻¹ point is the TS, and the preceding-image frequencies are an artifact of evaluating a Hessian off a stationary point). **Next thing I'd check:** the imaginary-mode eigenvector at the saddle to confirm it's the intended reaction coordinate. If you paste the `f/i` eigenvector block from the saddle `OUTCAR` (and tell me cell size + whether it's metallic), I'll verify the mode and the smearing/entropy for you.
