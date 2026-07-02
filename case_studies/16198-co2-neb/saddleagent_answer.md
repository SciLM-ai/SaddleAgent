# SaddleAgent answer — forum topic 16198

*Recorded production run · model: SaddleAgent (with Opus 4.8) · ts-debug@f66ba1d*

## Bottom line

**The "multiple barriers" come from two problems, and the climbing image is not one of them. (1) The band never converged — not one of the 8 images met the force criterion `EDIFFG = −0.026 eV/Å`; several still carry 0.15–0.20 eV/Å, so the images are not sitting on the minimum-energy path and the plotted energies are not path energies. (2) Your endpoints bundle two distinct reactions — CO₂ *formation* and then CO₂ *desorption into the gas phase* (your product is CO₂ ~4.5 Å above the slab). Roughly the back half of the band is spent lifting a finished CO₂ off the surface, which stretches the path and adds a long downhill tail with its own structure.** Starting straight into CI‑NEB is correct and is *not* your problem.

## What the files show

Profile on a consistent **E₀ (σ→0)** basis — I had to use E₀, not `TOTEN`/`F`, because of the smearing issue below — referenced to the initial state (00):

| img | role | rel. E₀ (eV) | max force (eV/Å) | C height z (Å) |
| --- | --- | --- | --- | --- |
| 00 | IS (CO+O) | 0.00 | — | 8.5 |
| 01–02 |  | −0.10 / −0.15 | 0.15 / 0.20 ✗ | 8.6 |
| 03 | formation TS (2nd C–O at 1.79 Å) | +1.12 | 0.045 | 8.9 |
| 04 |  | −0.07 | 0.058 | 9.1 |
| 05–08 | CO₂ lifting off | −0.24 → −0.46 | up to 0.15 ✗ | 9.9 → 11.5 |
| 09 | FS (CO₂ gas) | −0.46 | — | 12.0 |

There is really **one** physical barrier — image 03, where the second C–O bond is half-formed (1.79 Å, vs 1.17 Å for the existing C=O). It survives in both the E₀ and the free-energy columns, so it is a genuine high-energy geometry, not an artifact. Everything after it (04→09) is a smooth downhill desorption slide. The "extra humps" are the shallow 01–02 dip plus the unconverged wobble on images whose geometries are still 6–8× over the force tolerance. The run stopped at NEB step 396 of `NSW=1000`, with QuickMin (`IOPT=3`) at `TIMESTEP=0.05` crawling (Δenergy already ~1e-4/step) rather than converged.

## Your three questions

1. **CI directly, no plain NEB first — a problem?** No. `LCLIMB=.TRUE.` is the VTST code default and is meant to be on from the start; the climbing image aids convergence with no downside, and a plain-NEB warm-up is optional economy, never a prerequisite. The only cosmetic effect of CI-from-start is slightly uneven image spacing across the saddle. Keep it on.

2. **Final CO₂ gas too far above the surface?** **Yes — this is a real contributor.** Your FS (image 09) is desorbed CO₂ at z≈12 Å (slab top ≈7.5 Å). The band therefore encodes formation *and* desorption at once — the "path bundling two processes" failure. Desorption of a stable, closed-shell CO₂ is essentially barrierless (just an endothermic pull-off); it does not belong in the reaction NEB.

3. **Too few images?** 8 is plenty for a single elementary step — not your problem. If anything you're *under*-resolving the formation chemistry because most images are stuck on desorption.

## Fixes (specific)

**A. Isolate one process — rebuild the final endpoint.** You want the initial-phase formation barrier, so make image 09 the **just-formed CO₂ still on/just above the surface** (C ~1–2 Å above Pd, physisorbed/chemisorbed), *not* gas-phase CO₂. Re-relax that FS, then rebuild a fresh band with `nebmake.pl 00/POSCAR 09/POSCAR 8` (IDPP interpolation is its default) and **play the movie** (`nebmovie.pl`, view in VESTA/OVITO) before submitting — every atom should move smoothly and sub-Å between images. Element blocks already match (Pd 36 / C 1 / O 2) and the XC functional is consistent (PBE, `GGA=PE`, both endpoints and band), but the movie is the check that per-atom correspondence is right. Handle desorption, if you need it at all, as a separate constrained/relaxed-scan step (and with more vacuum — you currently leave only ~4.5 Å above the gas-phase CO₂).

**B. Fix the smearing.** `SIGMA = 0.41 eV` (used on *both* endpoints and band) gives an entropy term T·S ≈ 5 eV ≈ 130 meV/atom — the guidance is ≲1 meV/atom, so this is ~100× too large and is exactly why your `F`/`TOTEN` column wobbles. For a Pd metal slab use `ISMEAR = 1` (Methfessel–Paxton) with `SIGMA = 0.1–0.2` (or `ISMEAR = 0` with `SIGMA ≤ 0.1`), and report the σ→0 energy.

**C. Make endpoints and band identical — this applies to the `e0` run specifically.** Your `e0` endpoints (00, 09) were run with **vasp.5.4.4, ISYM=2, EDIFF=1e-6** while the band (01–08) used **vasp.6.5.1, ISYM=0, EDIFF=1e-5**. Re-run the endpoints with the *same binary* and the *same* INCAR as the band (`ISYM=0`, identical EDIFF/ENCUT/PREC/LREAL/SIGMA). Endpoint and band energies must be on the same footing or the barrier is meaningless.

**D. Then converge.** Keep CI on. Raise the QuickMin step: `IOPT=3`, `TIMESTEP=0.1`, `IBRION=3`, `POTIM=0`; confirm the max force is *descending* (not flat) over the last steps, and run until OUTCAR `FORCES: max atom` is below |EDIFFG| on **every** image. `EDIFFG=−0.026` is fine for the band; tighten the criterion toward `−0.01` to seat the climbing image at the true saddle. Check with `nebef.pl`/`nebresults.pl`.

## Two more things from your files

- **Don't restart from your current CONTCARs.** Every band `CONTCAR`/`POSCAR` has an all-`NaN` trailing velocity block (I confirmed it). The energies/forces themselves are finite, so the NaN is a harmless write artifact *in those files* — but if you copy them as restart `POSCAR`s, VASP can read the NaN velocities into the QuickMin optimizer and poison the run. Your `run1/` restart was seeded from these (and has no OUTCAR yet, i.e. it hasn't actually continued). Rebuild clean with `nebmake.pl` (per A) instead of restarting `run1`.

- **`u0/` has the same disease.** It's the same Pd(111)/CO₂ system as a coarser 4-image run, internally version-consistent (all vasp.5.4.4) but with the same `SIGMA=0.41`, the same gas-phase-CO₂ endpoint bundling, and an unconverged band (01–04). The same fixes A, B, D apply.

## Confidence & next step

High confidence that non-convergence plus the formation+desorption bundle produce the apparent multiple barriers; the single sharp feature at image 03 is consistent with a genuine CO₂-formation TS. Send me the rebuilt near-surface CO₂ final-state POSCAR and I'll sanity-check the geometry and the interpolated band before you launch.
