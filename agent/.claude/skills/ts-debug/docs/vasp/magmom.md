# MAGMOM

> Source: <https://www.vasp.at/wiki/index.php/MAGMOM>

**Type:** real array · **Default:** `NIONS*1.0` (ISPIN=2) or `3*NIONS*1.0` (LNONCOLLINEAR)

Initial on-site magnetic moments per atom (for a from-scratch magnetic calculation). Also lowers symmetry — breaking symmetry with MAGMOM removes the corresponding operations.

**Syntax:**
- Collinear (`ISPIN=2`): one value per ion — `MAGMOM = m1 m2 m3 …`
- Non-collinear (`LNONCOLLINEAR=.TRUE.`): three Cartesian components per ion — `MAGMOM = mx1 my1 mz1  mx2 my2 mz2 …` (with `LSORBIT`, in the `SAXIS` basis).
- Shorthand `n*value` repeats: e.g. `MAGMOM = 8*0.0`.

**Notes:**
- From scratch (`ISTART=0`): sets the initial moments and lowers symmetry.
- On restart: only sets symmetry — the magnetization comes from WAVECAR/CHGCAR.
- **Convergence tip:** set moments slightly larger than expected (e.g. experimental × 1.2–1.5). The final magnetic state depends strongly on the initial MAGMOM.

**Related:** ISPIN, LNONCOLLINEAR, LSORBIT, SAXIS, NUPDOWN, I_CONSTRAINED_M.
