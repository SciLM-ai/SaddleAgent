# ICHARG

> Source: <https://www.vasp.at/wiki/index.php/ICHARG>

**Default:** `2` (if `ISTART=0`), else `0`

How the **initial charge density** is constructed.

| Value | Behavior |
|---|---|
| `0` | From the initial wavefunctions. |
| `1` | Read `CHGCAR` and extrapolate to the new positions (good for restarts with small changes). |
| `2` | Superposition of atomic charge densities (typical from-scratch default). |
| `4` | Read the potential from a `POT` file (OEP; VASP ≥5.1). |
| `+10` (e.g. `11`, `12`) | **Keep the charge density fixed** (non-self-consistent) — for band structures / DOS. `11` from `CHGCAR`, `12` from atomic superposition. |

**Notes:** For non-SCF band structures use `ICHARG=11` (read a converged `CHGCAR`, often with `ISYM=0` and an explicit k-path). With DFT+U or `ICHARG=11`, set `LMAXMIX` appropriately (4 for d-, 6 for f-electrons; or 2×max l for 11/12).

**Related:** ISTART, CHGCAR, LMAXMIX, ISYM.
