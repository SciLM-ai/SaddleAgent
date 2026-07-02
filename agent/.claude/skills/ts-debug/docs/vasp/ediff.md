# EDIFF

> Source: <https://www.vasp.at/wiki/index.php/EDIFF>

**Type:** real · **Default:** `1E-4` eV

Convergence criterion for the **electronic** self-consistent (SCF) loop: the SCF stops when both the total-energy and band-structure-energy changes fall below `EDIFF` (eV).

- `EDIFF = 0` forces exactly `NELM` electronic iterations.
- Recommended: **`1E-6`** for well-converged results (convergence is ~quadratic, so extra iterations are cheap).
- Phonons / finite differences: **`1E-7`** or tighter (VTST dimer/Lanczos curvature needs accurate forces → `1E-7`–`1E-8`). Large systems or METAGGA may struggle to reach `1E-7`/`1E-8`.

**Related:** EDIFFG, NELM, NWRITE, METAGGA.
