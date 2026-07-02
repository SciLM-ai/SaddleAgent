# ISIF

> Source: <https://www.vasp.at/wiki/index.php/ISIF>

**Allowed:** `0–8` · **Default:** `0` (MD or hybrid functionals), else `2`

Controls stress-tensor calculation and which degrees of freedom relax.

| ISIF | Forces | Stress | Positions | Cell shape | Cell volume |
|---|---|---|---|---|---|
| 0 | ✓ | — | — | — | — |
| 1 | ✓ | trace only | — | — | — |
| 2 | ✓ | ✓ | ✓ | — | — |
| 3 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 4 | ✓ | ✓ | ✓ | ✓ | — |
| 5 | ✓ | ✓ | — | ✓ | — |
| 6 | ✓ | ✓ | — | ✓ | ✓ |
| 7 | ✓ | ✓ | — | — | ✓ |
| 8 | ✓ | ✓ | ✓ | — | ✓ |

**Notes:** Stress is time-consuming (off by default for hybrids). For `ISIF=1` only the total pressure is reliable. **Volume/cell relaxation warning:** the PAW basis is not re-adjusted for the changed cell — use a larger cutoff (e.g. `ENCUT = 1.3×ENMAX`) and `PREC = High`. Use POSCAR Selective dynamics for finer control. `ISIF=8` needs VASP ≥6.4.1. **Solid-state NEB uses `ISIF=3` with `LNEBCELL` and `IOPT=3`.**

**Related:** IBRION, ENCUT, PREC, LATTICE_CONSTRAINTS, POSCAR.
