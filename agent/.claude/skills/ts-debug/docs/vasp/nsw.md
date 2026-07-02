# NSW

> Source: <https://www.vasp.at/wiki/index.php/NSW>

**Type:** integer · **Default:** `0`

Maximum number of **ionic** steps (structure optimization or MD).

- **`IBRION = 0` (MD):** number of MD steps (required). Split very long runs into jobs of `NSW ≤ 20000`.
- **`IBRION ≠ 0` (relaxation):** maximum ionic steps for the minimizer. Each ionic step runs up to `NELM` electronic steps unless `EDIFF` is met first; ionic convergence is judged by `EDIFFG`.

Forces/stresses are computed each ionic step per `ISIF`.

**Related:** IBRION, NELM, EDIFF, EDIFFG, ISIF.
