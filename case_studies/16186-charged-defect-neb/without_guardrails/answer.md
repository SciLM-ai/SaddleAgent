I have everything I need. Let me confirm the electron bookkeeping: Li `ZVAL=3.0`×108 + F `ZVAL=7.0`×107 = 324 + 749 = **1073** (neutral). So NELECT=1072 is the +1 charge state, and the "old 1073" in the BRMIX line is exactly this neutral reference.

## Bottom line

**VASP *is* reading NELECT — your OUTCARs show `NELECT = 1072.0000 total number of electrons` and the SCF running at `1071.9999974` electrons. The `BRMIX … old 1073 / new 1072` line is not a NELECT failure; it's the normal one-time start-up transient where VASP renormalizes its neutral atomic-superposition starting density (1073 e⁻) down to your NELECT (1072). It's harmless and appears *only* for the charged cell, which is why your neutral run never showed it.** Your band isn't stalling on that message — it's stalling because **EDIFF=1E-10 with NELM=20 can never self-consistate**, and because **three interior images have atoms collided to 0.65 Å** from linear interpolation of the vacancy hop.

## Evidence

- **NELECT is applied.** `grep NELECT 02/OUTCAR` → `NELECT = 1072.0000 total number of electrons`; the SCF trace prints `number of electron 1071.9999974`. Definitive — the premise that VASP "isn't reading NELECT" is wrong.
- **Where "1073" comes from.** `ICHARG=2` (the from-scratch default; `docs/vasp/icharg.md`) builds the initial density as a *superposition of neutral atoms*, which integrates to your neutral count = 108·Li(ZVAL 3) + 107·F(ZVAL 7) = **1073**. At the first mixing step VASP rescales that to NELECT=1072 → BRMIX prints `old 1073 / new 1072`, difference = exactly your 1‑electron charge. One-time, benign. (This is likely the "at step 5" timing too: the default `NELMDL=-5` delay runs 5 non-self-consistent steps, then the first *mixed* step triggers the renormalization print.)
- **SCF is actually converging, not sloshing.** In `02/OUTCAR` the per-step energy change is `-2.7e4 → -1.6e4 → -7.7e3 → -3.0e3` eV — halving each step, the normal pattern from a superposition start. The OUTCAR is truncated at a 4096-byte block (4 iterations, empty OSZICAR/WAVECAR/CHGCAR) → the process was killed mid-first-ionic-step, not a clean stop.
- **The band is broken.** The "distance between some ions is very small" warning appears in `02/03/04` only (endpoints `00`/`06` and `01`/`05` are clean). Image 02's nearest-neighbor table has ion 4 at **0.65 Å**, plus 1.15/1.19 Å pairs — LiF bonds are ~2.0 Å. Linear interpolation dragged the migrating atom through an occupied site (`reference/neb-diagnostics.md`, the vacancy-hop row).
- Build is fine: `vasp.6.4.2`, `VTST: version 4.1` linked. Your on-disk INCAR is actually the `ICHARG=0`, `System=Si` attempt (cosmetic leftover) — not a factor.

## Fixes (in order)

1. **Stop chasing the BRMIX line** — it's a warning, not the stop. Expect it on every charged (`NELECT`≠neutral) start.
2. **Loosen EDIFF and raise NELM.** `EDIFF=1E-10` is meaningless for NEB forces and, at ~half-decade convergence per step, needs ~45 SCF steps to reach — impossible under `NELM=20`. Set **`EDIFF=1E-6`** (1E-7 at most) and **`NELM=60`** (or 200, matching your endpoints). That alone lets each image self-consistate.
3. **Rebuild the band with IDPP so no image has collided atoms.** From your relaxed endpoints:
   `nebmake.pl 00/POSCAR 06/POSCAR 5 idpp` (or ASE/pymatgen IDPP). Then check every image's min nearest-neighbor distance (>~1.5 Å) and play the movie before resubmitting. If the hop is long/curved, add images. Without this, even a converged run gives a physically meaningless barrier.

## Secondary (worth doing, not the bug)

- **ISPIN:** 1072 is *even* (closed-shell V_F⁺), so `ISPIN=1` is fine and halves cost. The *neutral* case (1073, odd) genuinely needs `ISPIN=2` — that asymmetry is expected, not a symptom.
- **LCLIMB:** turn it on from the start (`LCLIMB=.TRUE.`) — climbing image is the VTST default; no plain-NEB "warm-up" is needed.
- **IOPT:** on a fresh, high-force band, QuickMin (`IOPT=3`, `TIMESTEP=0.1`) is more robust than LBFGS (`IOPT=1`); switch to LBFGS once forces are under ~0.3 eV/Å.

**Confidence:** high on all four points — each is backed directly by your OUTCARs. If after fixing EDIFF/NELM and rebuilding the band a specific image still won't converge, send me that image's OSZICAR and I'll look at the mixing (AMIX/BMIX) for the charged cell.
