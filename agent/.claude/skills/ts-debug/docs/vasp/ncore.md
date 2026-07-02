# NCORE

> Source: <https://www.vasp.at/wiki/index.php/NCORE> (VASP ≥5.2.13)

**Type:** integer · **Default:** `1`

Number of MPI ranks that collaborate on a **single band** (parallelizes the FFTs of that band). Larger `NCORE` → fewer bands in parallel, lower memory and orthogonalization cost.

**Relationship:** `NPAR = available_ranks / NCORE`. Do **not** set both `NCORE` and `NPAR` (`NPAR` wins if both are present).

**Recommendations:**
- `NCORE ≈ √(available_ranks)` is a good general choice on multi-core machines.
- Set `NCORE` to cores-per-node (or per NUMA domain): e.g. `NCORE=4` for ~100 atoms, `NCORE=12–16` for >400 atoms. Small systems on slow networks → `NCORE=1`.
- With OpenMP/GPU builds, `NCORE` is reset to `1` automatically (use thread count for FFT control).

**Related:** NPAR, KPAR, LPLANE.
