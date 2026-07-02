# ISYM

> Source: <https://www.vasp.at/wiki/index.php/ISYM>

**Allowed:** `-1, 0, 1, 2, 3` · **Default:** `1` (USPP/PAW); `3` (hybrids, `LHFCALC=.TRUE.`)

Controls use of symmetry (charge-density/force/stress symmetrization and k-mesh reduction).

| Value | Behavior |
|---|---|
| `-1` | Symmetry fully **off**. |
| `0` | Off, but still uses Ψ_k = Ψ*₋k (time reversal) to reduce the k-mesh. Common for MD, band structures. |
| `1` | **On**, with charge-density symmetrization. |
| `2` | On, memory-efficient charge-density symmetrization (large cells). |
| `3` | On, symmetry applied to orbitals rather than the charge density (hybrids). |

**Turn off (`ISYM=0` or `-1`)** for: MD (`IBRION=0`), band-structure k-paths, some magnetic cases, and **NEB/dimer** where the path/displacement breaks symmetry. Symmetry tolerance is `SYMPREC`.

**Related:** SYMPREC, LHFCALC, IBRION, MAGMOM.
