# ISPIN

> Source: <https://www.vasp.at/wiki/index.php/ISPIN>

**Allowed:** `1 | 2` · **Default:** `1`

Whether the calculation is spin-polarized.

- **`1`** — non-spin-polarized (one shared charge density).
- **`2`** — spin-polarized, collinear (spin-up/down treated separately).

**Notes:** Required for magnetic systems (Fe, Co, Ni, magnetic oxides); initialize moments with [MAGMOM](magmom.md). For non-collinear magnetism use `LNONCOLLINEAR=.TRUE.` instead. (VASP ≥6.5.0 disallows combining `ISPIN=2` + `MAGMOM` + `LNONCOLLINEAR=.TRUE.` at once.)

```
ISPIN = 2
MAGMOM = 2*5.0 2*-5.0
```

**Related:** MAGMOM, LNONCOLLINEAR, NUPDOWN.
