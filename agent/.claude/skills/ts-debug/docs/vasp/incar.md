# INCAR

> Source: <https://www.vasp.at/wiki/index.php/INCAR>

The central VASP input file — "determines **what to do and how to do it**." A list of `TAG = value` lines. Every tag has a default; only non-defaults need to be set.

**Syntax:**
- `TAG = value`, one per line (tags are **case-insensitive**).
- Comments: text after `#` or `!` is ignored.
- Multiple statements on a line separated by `;`; line continuation with `\`.
- Booleans are `.TRUE.` / `.FALSE.`.
- Nested/grouped tags: `PREFIX/TAG = value` or `{ … }`.
- **Always check the OUTCAR** to confirm how VASP interpreted the INCAR.

**Key tag categories** (cards in this directory):
- **Electronic:** [ENCUT](encut.md), [EDIFF](ediff.md), [ALGO](algo.md), [PREC](prec.md), [ISMEAR](ismear.md), [SIGMA](sigma.md), [NELM](nelm.md)/[NELMIN](nelmin.md), [LREAL](lreal.md)
- **Ionic / relaxation:** [IBRION](ibrion.md), [NSW](nsw.md), [EDIFFG](ediffg.md), [ISIF](isif.md), [POTIM](potim.md), [NFREE](nfree.md)
- **Spin & magnetism:** [ISPIN](ispin.md), [MAGMOM](magmom.md)
- **Startup / restart:** [ISTART](istart.md), [ICHARG](icharg.md), [ISYM](isym.md)
- **Output / analysis:** [LORBIT](lorbit.md)
- **Dispersion:** [IVDW](ivdw.md)
- **Parallelization:** [NCORE](ncore.md), [NPAR](npar.md)

For transition-state work, the VTST method tags (`ICHAIN`, `IMAGES`, `IOPT`, `SPRING`, `LCLIMB`, `DdR`, …) are documented under [../vtst/](../vtst/overview.md).

**Related files:** POSCAR, [POTCAR](potcar.md), KPOINTS, OUTCAR/CONTCAR.
