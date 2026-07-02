**Root cause: the POTCAR for the NEB band is concatenated in the wrong species order, so every interior image ran with Li and F pseudopotentials swapped.** Your endpoints use POTCAR order `Li_sv, F` — matching the POSCAR species line `Li F` (108 108) — but all seven interior images use `F, Li_sv`, reversed. VASP assigns POTCAR blocks to POSCAR blocks strictly by position, so in images 01–07 the 108 Li atoms were computed with the F potential and the 108 F atoms with the Li potential. That puts the whole band on a different total-energy reference (~8–11 eV below the correctly-set-up endpoints), which is precisely the "intermediates ~10 eV lower" you observe. Rebuild the band POTCAR in `Li_sv`-then-`F` order and rerun.

### Evidence
From `grep TITEL */OUTCAR` alongside the final energies (`energy(sigma->0)`):

| run | POTCAR order | VTST linked | E (eV) |
|---|---|---|---|
| OUTCAR00 (endpoint) | **Li_sv, F** ✓ | no | −1048.24 |
| OUTCAR01–07 (band) | **F, Li_sv** ✗ | yes | −1056.68 … −1053.91 |
| OUTCAR08 (endpoint) | **Li_sv, F** ✓ | no | −1043.41 |

The band 01→07 is a smooth, internally consistent curve with its maximum at image 05 — a Li↔F-swapped rocksalt lattice is still a perfect rocksalt lattice, so it relaxes cleanly and even yields a plausible-looking barrier. But there is an ~8 eV cliff from 00→01 and an ~11 eV cliff from 07→08, localized at *both* endpoints. The endpoints are the trustworthy calculations here; the band is the error. This matches the documented failure mode in `reference/neb-diagnostics.md` ("per-element pseudos concatenated in a different order… an ordering mismatch shifts the whole band ~10 eV") and the POTCAR rule in `docs/vasp/potcar.md` ("Order must match POSCAR").

Why your own consistency checks — and the automated precheck — saw nothing: Li_sv carries 3 valence electrons and F carries 7, so swapping them leaves NELECT at 1080 and ENCUT/PREC/ISMEAR/SIGMA/EDIFF all identical. The *only* fingerprint is the `TITEL` ordering.

### Ruling out the binary as the cause
One honest confound: the VTST banner is present in the band and absent in the endpoints, which correlates with the energy split just as well as the POTCAR order does. It is not the cause. All nine runs are the same build (`vasp.6.4.2`), and the VTST patch adds force projection and optimizers — it does not modify the DFT energy functional — so a same-version stock-vs-patched split is energy-neutral. The reversed POTCAR, by contrast, is an unambiguous input error that *must* shift the total energy by many eV. It is the sufficient and necessary cause; the binary split is incidental. The fix below eliminates both confounds at once by recomputing endpoints and band on one binary with one canonical POTCAR.

### Fix
1. Rebuild a single canonical POTCAR in POSCAR order and use it for every directory:
   ```
   cat Li_sv/POTCAR F/POTCAR > POTCAR
   ```
2. The current image geometries relaxed on the wrong PES, so discard their CONTCARs. Re-interpolate fresh images from your two relaxed endpoints. For a point-defect hop use the IDPP builder (`nebmake.py`, `docs/vtst/scripts.md`) rather than linear interpolation, so the migrating F is not dragged straight through an occupied site:
   ```
   nebmake.py 00/CONTCAR 08/CONTCAR 7
   ```
   Then place the endpoint OUTCARs in `00/` and `08/` for post-processing, and rerun the whole band (endpoints included) on the VTST binary.
3. Verify before trusting anything: `grep TITEL */OUTCAR` must read `Li_sv` first in *every* directory, and the new image energies must fall *between* the endpoints.

### Secondary items to clean up
- **Over-tight EDIFF.** You have `EDIFF = 1e-10` with `NELM = 20`, so SCF hits the 20-iteration cap before reaching 1e-10 and prints "EDIFF was not reached" on many steps (this is the flag the precheck raised for all nine runs). The residual there is sub-meV — it is an energy-resolution shortfall, not remotely a 10 eV effect, so it is not your problem here. Still, loosen EDIFF to ~1e-6 (or raise NELM to ~60) so each step fully converges cleanly.
- **Endpoint gap.** After the fix, sanity-check the endpoint-to-endpoint energy, currently ~4.85 eV. That is large for a single F-interstitial hop; confirm both endpoints are the same defect and charge state and that each is a genuine relaxed minimum (both did reach the ionic force criterion, so this is a physics check, not a convergence one).
- **NaN "velocity" blocks** in the image POSCARs are harmless leftovers from image generation; a geometry/NEB run does not read them and they cannot affect the energy. Ignore or strip them.

**Confidence: very high.** The reversed `TITEL` order is an objective input error present in exactly the seven anomalous runs, and it fully and quantitatively explains the symptom.
