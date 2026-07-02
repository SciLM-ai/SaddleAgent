# ISTART

> Source: <https://www.vasp.at/wiki/index.php/ISTART>

**Default:** `1` if a `WAVECAR` exists, else `0`

Whether/how to read `WAVECAR` and restart.

| Value | Behavior |
|---|---|
| `0` | From scratch; initialize orbitals per `INIWAV`. |
| `1` | Restart, **constant energy cutoff** — plane waves redefined for the new cell/`ENCUT` (use for convergence tests, volume relaxation / Pulay-stress concerns). |
| `2` | Restart, **constant basis set** — plane waves unchanged regardless of new parameters. |
| `3` | Full restart with orbital/charge prediction from `TMPCAR` (MD only). |

**Notes:** If `WAVECAR` is missing/invalid, `ISTART` reverts to `0`. Pairs with [`ICHARG`](icharg.md).

**Related:** INIWAV, WAVECAR, TMPCAR, ENCUT, ICHARG.
