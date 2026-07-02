# ALGO

> Source: <https://www.vasp.at/wiki/index.php/ALGO>

**Default:** `Normal`

Selects the electronic minimization algorithm (or the GW/response calculation type). The first letter selects the algorithm (except `None`, `Nothing`, `Exact`, `Eigenval`).

## Electronic minimization
| Value | Implementation | Use case |
|---|---|---|
| `Normal` | Blocked Davidson (IALGO=38) | Default, reliable. |
| `VeryFast` | RMM-DIIS (IALGO=48) | Speed; **no hybrids**. |
| `Fast` | Davidson → RMM-DIIS | Robust mixed approach. |
| `Conjugate`/`All` | All-bands simultaneous (IALGO=58) | Pair with `ISMEAR`-care; insulators/GW init. |
| `Damped` | Damped friction (IALGO=53) | Difficult cases (e.g. metals/hybrids). |
| `Exact` | Exact diagonalization (IALGO=90) | Full eigendecomposition (GW/BSE init). |
| `Subrot` | Subspace rotation (IALGO=4) | Orbital subspace only. |
| `Eigenval` | Recompute energies (IALGO=3) | From an existing WAVECAR. |
| `None`/`Nothing` | No update (IALGO=2) | DOS / post-processing, reuse orbitals. |

## GW & response (selection)
`CHI` (response only), `G0W0`/`EVGW0` (single-shot), `GW0`/`EVGW` (partial sc), `GW`/`QPGW` (full sc), `ACFDT`/`RPA` (RPA total energy), `*R` variants (low-scaling, VASP ≥6), `BSE`, `TDHF`.

**Notes:** Set `LMAXMIX` appropriately for fast convergence (e.g. `LMAXMIX=4` for d-, `6` for f-electron systems). `VeryFast` was hardened in VASP 6 (use `Old VeryFast` for the 5.x behavior). `NELMGW` replaces `NELM` in self-consistent GW (≥6.3).

**Related:** IALGO, LDIAG, LMAXMIX, NELM, NELMGW.
