# SaddleAgent answer — forum topic 16199

*Recorded production run · model: SaddleAgent (with Opus 4.8) · ts-debug@f66ba1d*

## Bottom line

**The interior images and the endpoints were run with *different* Hf pseudopotentials, so their total energies sit on different absolute scales — the ~90 eV "drop" into the band is a POTCAR mismatch, not a physical well.** Your relaxed endpoints (00, 05) used a 10‑valence Hf potential (ZVAL = 10, a `Hf_pv`‑type), while the band images (01–04) used `Hf_sv` (ZVAL = 12). The extra 2 semi‑core electrons per Hf × 32 Hf = 64 extra electrons drive each interior image's TOTEN ~90 eV more negative. Standardize on **one** Hf POTCAR — the `Hf_sv` your band already uses — re‑relax both endpoints with it, drop the new OUTCARs into 00/ and 05/, and continue.

## Evidence

All six POSCARs are the identical system — `Hf 32  C 32  O 1` (65 atoms, 9.295 × 9.295 × 21.971 Å slab) — yet:

| dir | role | Hf ZVAL | NELECT | final TOTEN (eV) |
| --- | --- | --- | --- | --- |
| 00 | endpoint | 10 | 454 | −661.54 |
| 01 | image | 12 | 518 | −751.02 |
| 02 | image | 12 | 518 | −750.12 |
| 03 | image | 12 | 518 | −749.10 |
| 04 | image | 12 | 518 | −748.43 |
| 05 | endpoint | 10 | 454 | −658.60 |

- `00/OUTCAR`: `ZVAL = 10.00 4.00 6.00`; `01/OUTCAR`: `ZVAL = 12.00 4.00 6.00` — C (4) and O (6) match; only **Hf differs**.

- Band `POTCAR` = `PAW_PBE Hf_sv 10Jan2008 GW suitable` (12 e). Per the POTCAR reference, the `_sv` suffix means semi‑core s+p are carried in valence (vs `_pv`, only p) — that is precisely the 2‑electron‑per‑Hf difference. Two pseudopotentials with different core treatments have different total‑energy zeros, so their TOTEN values are **not comparable**: the interior images land ~90 eV below the endpoints, and any barrier read off this band (E_image − E_endpoint) is meaningless.

I checked the things that would otherwise mimic this and they're **clean**: XC is consistent (`LEXCH = 8`, PBE, in endpoints and images), and VTST is genuinely linked (`VTST: version 3.2` in every OUTCAR), so running plain NEB (`LCLIMB = .FALSE.`) is doing what you intended — the problem is purely the pseudopotential, upstream of the band physics.

## Fix

1. **Pick one Hf POTCAR and use it everywhere.** Use the `Hf_sv` already in your band directory — it includes the Hf 5p semi‑core states, is the more accurate/transferable choice for an early transition metal, and is what your interior images already ran with. Don't downgrade the band to the 10‑electron potential.

2. **Re‑relax both endpoints with that same `Hf_sv` POTCAR** and the band's electronic deck (`ENCUT = 520`, `PREC = Normal`, `GGA = PE`, `ISMEAR = 0`, `SIGMA = 0.05`, and tighten `EDIFFG` to ≤ −0.02). Start from your existing `00/POSCAR` and `05/POSCAR`, but you must re‑optimize, not single‑point: the relaxed geometry shifts slightly under a different pseudopotential. This step also erases the minor endpoint/band deck differences the precheck flagged (endpoints were run at `EDIFF = 1E‑8`, `ISYM = 2`; band at `1E‑5`, `ISYM = 0`).

3. **Copy the new endpoint OUTCARs into 00/ and 05/** — these are what `nebbarrier.pl`/`nebresults.pl` read for the endpoint energies. Now all six directories live on one consistent `Hf_sv` scale and the interior images will sit *above* the endpoints.

4. **Continue the band** by restarting images 01–04 from freshly rebuilt geometries, and play the band movie before resubmitting to confirm only the reacting atoms move (the CO‑forming O/C and their neighbors) with sub‑Å steps between images.

## Secondary issues — don't lose them

- **The band never converged.** Images 01–04 stopped at exactly `NSW = 50` with `reached required accuracy` absent — they hit the step cap, not a convergence failure. NEB needs hundreds of ionic steps; raise `NSW` to ~300–500 on the restart. (Moot until the POTCAR is fixed — there's no point converging a band whose energies are meaningless.)

- **Every interior `CONTCAR` has an all‑`NaN` velocity block** (lines 76–140). It doesn't affect the static energies, but don't restart from these velocities — rebuild the interior images cleanly (e.g. re‑interpolate with `nebmake.py` between the new endpoints, or strip the velocity block) so QuickMin starts from rest rather than integrating NaN.

- Once the scale is fixed and the band converges, if the profile looks barrier‑less or implausibly low, turn on `LCLIMB = .TRUE.` — per the VTST parameter reference it's the code default for a saddle search, purely geometric, and a low/narrow saddle can fall *between* plain‑NEB images. There's no need to run plain NEB first as a "warm‑up."

## Confidence

**High.** The ZVAL/NELECT split and the ~90 eV offset are direct, unambiguous reads from your OUTCARs, and the magnitude matches the 64‑electron semi‑core difference exactly. The one thing I can't see is the **endpoint relaxation INCAR/POTCAR** themselves (only the 00/05 OUTCARs are on disk) — if you share them I can confirm the endpoints were `Hf_pv` specifically and verify nothing else drifted between those runs and the band.
