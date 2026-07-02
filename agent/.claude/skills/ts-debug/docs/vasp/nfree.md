# NFREE

> Source: <https://www.vasp.at/wiki/index.php/NFREE>

**Type:** integer · **Default:** `1` (if `IBRION=2`), else `0`

Meaning depends on `IBRION`:

- **`IBRION=1` (quasi-Newton):** number of ionic steps kept in the Hessian-history (rank of the approximate Hessian). Typical `10–20`; values >20 rarely help and can cause RMM-DIIS divergence. If unset, an eigenvalue criterion prunes old history automatically.
- **`IBRION=5/6` (finite-difference phonons):** number of displacements **per direction** per ion (magnitude set by [`POTIM`](potim.md)):

| Value | Displacements |
|---|---|
| `1` | single displacement (not recommended) |
| `2` | central difference: ±POTIM (recommended) |
| `4` | ±POTIM and ±2·POTIM |

Use small displacements (~0.015 Å) to stay harmonic.

**Related:** IBRION, POTIM.
