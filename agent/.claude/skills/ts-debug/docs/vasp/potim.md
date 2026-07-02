# POTIM

> Source: <https://www.vasp.at/wiki/index.php/POTIM>

**Type:** real · **Default:** none for `IBRION=0` (must be set); `0.5` for `IBRION=1,2,3` (VASP ≤4.6); `0.015` for `IBRION=5,6` (VASP ≥5.1)

Sets the time step (MD) or the step-width scaling (relaxation / phonons).

- **`IBRION = 0` (MD):** time step in **fs** — required, the run crashes without it.
- **`IBRION = 1,2,3` (relaxation):** scaling constant for the step width (quasi-Newton is especially sensitive).
- **`IBRION = 5,6` (phonons):** finite-difference displacement (Å); must stay within the harmonic limit. VASP ≥5.1 resets excessively large values to `0.015`.
- **VTST NEB / dimer / Lanczos:** set **`POTIM = 0`** (with `IBRION = 3`) so VASP itself does not move the ions — the VTST `IOPT` optimizer does.

**Related:** IBRION, NFREE, POTIM=0 for VTST methods.
