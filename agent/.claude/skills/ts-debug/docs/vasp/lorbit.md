# LORBIT

> Source: <https://www.vasp.at/wiki/index.php/LORBIT>

**Default:** `0`

Controls projected-DOS / site-and-lm decomposition output (`DOSCAR`, `PROCAR`) and on-site magnetic moments.

| Value | RWIGS | Output | Phase factors |
|---|---|---|---|
| `0` | required | DOSCAR, PROCAR | no |
| `1` | required | DOSCAR, lm-decomposed PROCAR | no |
| `2` | required | DOSCAR, lm-decomposed PROCAR | yes |
| `5` | required | DOSCAR, PROOUT | no |
| `10` | ignored | DOSCAR, PROCAR | no |
| `11` | ignored | DOSCAR, lm-decomposed PROCAR | no |
| `12` | ignored | DOSCAR, lm-decomposed PROCAR | yes (not recommended) |
| `13` | ignored | DOSCAR, lm-decomposed PROCAR | yes (not recommended) |
| `14` | ignored | DOSCAR, lm-decomposed PROCAR | yes (best phase handling, VASP ≥5.4.4) |

**Notes:** Values `≥10` use the PAW projectors and **ignore `RWIGS`** (preferred); `0–5` need `RWIGS`. For `≥10` the written phase factors are usually only qualitative; use `14` for the best handling. Can be added on a non-SCF restart with `ALGO=None`. The VTST `split_dos.py`/`dosanalyze.pl`/`doslplot.pl` scripts post-process the resulting `DOSCAR` (10/19-column = `LORBIT=11`-style data).

**Related:** RWIGS, NEDOS, EMIN/EMAX, ISPIN, LNONCOLLINEAR.
