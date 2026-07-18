# Topic 16199 — NEB does not converge...

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> The AI response is accurate.  Both the description of the problem and the explanation are spot on.

## Original question

**shkwon** (2025-12-25 20:07):

I simulated the activation barrier of CO gas formation on the surface without climbing image.

However, the energy of intermediate images shows drastically low energy,

which is a total error.

It would be appreciated if you let me know the possible reasons that show the error.

I have attached the calculation files.

Thank you for reading!

## Expert answer (forum ground truth)

**graeme** (2025-12-27 12:01):

You have to have the same settings in your endpoints as your band.  You are using Hf_pv with your endpoints and Hf_sv with the band.  The k-point mesh is also different.  DFT calculations rely on cancelation of error; you need the same settings to compare energies.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Root cause: your endpoints and your interior images were run with two different Hf pseudopotentials, so their total energies are on incompatible reference scales — the ~90 eV "drop" is a POTCAR mismatch, not physics.** The band (images 01–04) uses `Hf_sv` (12 valence e⁻), while the endpoint OUTCARs in `00/` and `05/` were computed earlier with the standard `Hf` potential (10 valence e⁻). nebresults/`neb.dat` subtracts the standard-Hf endpoint energy from the Hf_sv interior energies and you get a nonsensical ~90 eV well. Fix it by recomputing both endpoints with the *same* POTCAR as the band and re-running.

### The evidence (from your own files)

| dir | role | POTCAR Hf (ZVAL) | NELECT | TOTEN (eV) | converged? |
| --- | --- | --- | --- | --- | --- |
| 00 | initial state | Hf, 10 e⁻ | 454 | −661.5 | yes |
| 01 | image 1 | Hf_sv, 12 e⁻ | 518 | −751.0 | no (NSW cap) |
| 02 | image 2 | Hf_sv, 12 e⁻ | 518 | −750.1 | no |
| 03 | image 3 | Hf_sv, 12 e⁻ | 518 | −749.1 | no |
| 04 | image 4 | Hf_sv, 12 e⁻ | 518 | −748.4 | no |
| 05 | final state | Hf, 10 e⁻ | 454 | −658.6 | yes |

- Your top-level `POTCAR` is `PAW_PBE Hf_sv 10Jan2008 GW` (ZVAL = 12) → this is what the interior images used.

- The endpoint OUTCARs report **ZVAL = 10** and **NELECT = 454**; the interior images report **ZVAL = 12** and **NELECT = 518**. The difference is exactly 32 Hf × 2 e⁻ = 64 electrons. Same 65 atoms, same ENCUT (520), same cell — only the Hf potential differs.

- A semi-core potential like `Hf_sv` includes the Hf 5p electrons, so its **absolute** total energy is far more negative than standard `Hf`. That offset (~90 eV here) is precisely why images 1–4 sit ~89 eV "below" the endpoints in `neb.dat`. Total energies from different PAW potentials are **never** directly comparable — this is a pure reference-scale artifact.

This matches the classic "energies blow up, interior images tens of eV above/below endpoints → endpoints↔band inconsistent → check POTCAR variant" failure. It also corrupts the improved-tangent estimate at images 1 and 4 (they border the mis-referenced endpoints), so it's not only a plotting problem.

### Fix (pick ONE potential, use it everywhere)

You clearly intend `Hf_sv` for the production run (it's the band POTCAR, and it's the higher-quality/GW-suitable choice), so the cleanest path is:

1. **Re-relax both endpoints (IS and FS) with `Hf_sv`** — i.e. the identical POTCAR (`Hf_sv` + `C` + `O`), ENCUT=520, KPOINTS (3×3×1), GGA=PE, ISMEAR/SIGMA as in your INCAR.

2. Copy each new endpoint OUTCAR into `00/OUTCAR` and `05/OUTCAR` (also update `00/POSCAR`, `05/POSCAR` to the relaxed geometries if they changed).

3. Re-run `nebresults.pl` / `nebbarrier.pl`. The interior images will now share the ~−750 eV reference and the barrier will be sane.

4. If you also use a **gas-phase CO** energy anywhere in this barrier, recompute that with `Hf_sv`/`C`/`O` too — same rule.

(If you'd rather use standard `Hf` for cost, do the mirror: rebuild the top-level `POTCAR` with standard `Hf` and re-run the whole band so it matches the existing endpoints. Either way, one consistent potential for endpoints + band + any gas reference.)

### Secondary issue to fix at the same time

`NSW = 50` is far too small for NEB — images 01–04 all hit the step cap without reaching `EDIFFG = −0.01` ("reached required accuracy" = 0). NEB typically needs hundreds of steps. Once the POTCAR is consistent, raise NSW (e.g. 300–500) and continue from the CONTCARs. Don't bother interpreting the current forces/barrier — they're computed against a corrupted reference.

**Confidence: very high** on the POTCAR mismatch — the ZVAL/NELECT split is unambiguous and self-consistent (exactly 64 electrons, 32 Hf × 2). What I'd check next after re-running: that the relaxed endpoint energies now bracket the interior images (interior should lie *between* or modestly above them), giving a physical, positive barrier. If you want a true saddle energy afterward, you'll need to switch climbing image on (`LCLIMB = .TRUE.`) for the final stage.
