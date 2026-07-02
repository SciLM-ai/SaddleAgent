# NPAR

> Source: <https://www.vasp.at/wiki/index.php/NPAR>

**Type:** integer · **Default:** available ranks (i.e. `NCORE=1`)

Number of bands treated in parallel. **Legacy** — [`NCORE`](ncore.md) is the recommended, more intuitive control.

**Relationship:** `NPAR × NCORE = available_ranks` (where available_ranks = total MPI ranks / `KPAR`).

**Recommendations:** Prefer setting `NCORE` instead. Avoid `NPAR=1` (all ranks on one band — almost always very slow). If both `NPAR` and `NCORE` are in the INCAR, `NPAR` takes precedence.

**Related:** NCORE, KPAR, LPLANE, NSIM.
