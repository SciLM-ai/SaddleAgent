# Topic 16189 — Negative transition state energies along reaction coordinates

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> The AI response is correct.

## Files

The user's complete uploaded files for this topic are in the deep-dive case: [`../../16189-potcar-order-swap/files/`](../../16189-potcar-order-swap/files/).

## Original question

**jordanchapman** (2025-06-30 15:33):

Hi all,

I'm trying to calculate the energy barrier associated with the dislocation of a F ion to an interstitial position in LiF. I've located what I think are two stable end points and generate intermediate images while keeping the atomic ordering in the POSCAR files consistent. When I do the NEB calculation, I find that VASP will calculate the intermediate configurations to have energies nearly 10 eV lower than either endpoint configuration, but was still able to locate an energy maximum along the band. 

I've doublechecked that the INCAR settings (in particular, the ENCUT and k-points mesh) are consistent for the endpoint and intermediate steps. I've also run geometry optimizations for both endpoints with symmetry turned off (ISYM = 0) to make sure that the endpoints aren't getting caught at high-symmetry points. The geometries of the POSCAR files also look to be reasonable, i.e., no close contacts between neighboring atoms.

Any input as to what could be causing this downward shift in the intermediate energies would be appreciated. I attached the POSCAR and OUTCAR files for the run.

Jordan

VT Postdoc

## Expert answer (forum ground truth)

**graeme** (2025-07-01 16:41):

It looks like you switched the order of Li and F in your POTCAR file, between the endpoints and the band.

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Root cause: the POTCAR element order is reversed in the NEB band relative to the POSCARs and the endpoints

**Your interior images were run with `POTCAR = F, Li_sv`, but every POSCAR lists `Li F` (Li = first 108 atoms) and your two endpoints were run with the correct `POTCAR = Li_sv, F`. VASP assigns pseudopotentials strictly by POTCAR order, so in images 01–07 the F potential was put on the Li sites and the Li potential on the F sites — a chemically wrong "identity-swapped" crystal. Its total energy (~−1054 to −1056 eV) simply isn't comparable to the correctly-set-up endpoints (−1048 / −1043 eV), which is your ~10 eV downward shift. Fix: rebuild the band's POTCAR as `Li_sv` then `F` to match the POSCAR, and rerun.**

### The evidence

`grep TITEL` on every OUTCAR:

| dir | POTCAR order VASP used |
| --- | --- |
| 00 (endpoint) | Li_sv, F ✓ |
| 01–07 (band) | F, Li_sv ✗ reversed |
| 08 (endpoint) | Li_sv, F ✓ |

- All nine POSCARs declare `Li F` / `108 108` (Li block first). The displacement check confirms this: the only atom that migrates 3.7 Å is index 166, which lies in the *second* block — i.e. the F sublattice. So the endpoints' `Li_sv, F` ordering is the correct one.

- In a band OUTCAR, VASP registered `VRHFIN =F` as type 1 and `VRHFIN =Li` as type 2 with `ions per type = 108 108` → the first 108 atoms (Li positions) were computed as F, the last 108 (F positions) as Li.

- This was **invisible to your ENCUT/k-point check** because `Li_sv`(3 e⁻) + `F`(7 e⁻) gives `NELECT = 1080` *either way* — ENCUT (400), KPOINTS (Γ-only), ISMEAR, ISPIN, volume, XC (PBE), PREC all match across all images. Only the species mapping differs.

- I verified the energies are genuinely converged, not noise: endpoint 0 is flat at −1048.239 over its last 6 SCF steps, and image 01's final step is flat to 1e-8 at −1056.678. Two *converged* minima 0.68 Å apart can't differ by 8 eV on one PES — they're two different chemistries. (Magnetization is ~0 everywhere, so spin is not involved.)

### Fix

1. In the NEB directory, rebuild the POTCAR to match the POSCAR/endpoint order:

```
cat /path/to/potpaw_PBE/Li_sv/POTCAR /path/to/potpaw_PBE/F/POTCAR > POTCAR
grep TITEL POTCAR        # must show Li_sv first, then F
```

2. Rerun the NEB. The geometry/interpolation is fine (one F moving lattice→interstitial, ordering consistent, no close contacts) — only the POTCAR was wrong.

3. Sanity gate before trusting anything: `for d in 0*/; do echo -n "$d "; grep TITEL $d/OUTCAR | tr '\n' ' '; echo; done` — every image, endpoints included, must read identically (`Li_sv, F`). With that fixed the band will sit between the endpoints and give a physical barrier.

### One secondary cleanup (not the cause, but worth fixing)

`EDIFF = 1E-10` with `NELM = 20` is self-defeating: the SCF aborts `EDIFF was not reached (unconverged)` on most steps. It didn't cause this problem (energies converged to ~1e-4–1e-8 anyway), but per the VASP docs the EDIFF default is 1E-4 and the recommended value is **1E-6**, and the NELM default is **60**. Set `EDIFF = 1E-6` and either drop the NELM line or set `NELM = 60` so forces are reliably self-consistent for the production run.

Confidence: very high — the POTCAR-order mismatch is shown directly in the OUTCAR headers. If after the rerun the endpoints still differ by ~5 eV, that's a separate question (is endpoint 0 the perfect crystal or already a defect?), and I'd want your two endpoint POSCARs to confirm the intended reaction — but that won't change this fix.
