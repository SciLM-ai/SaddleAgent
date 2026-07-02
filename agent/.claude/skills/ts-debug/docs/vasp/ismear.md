# ISMEAR

> Source: <https://www.vasp.at/wiki/index.php/ISMEAR>

**Allowed:** `-15, -14, -5, -4, -3, -2, -1, 0, N>0` · **Default:** `1` · works with [SIGMA](sigma.md)

Sets how partial occupancies (electronic smearing) are determined.

| Value | Method | Use |
|---|---|---|
| `-5` | Tetrahedron + Blöchl corrections | Semiconductors/insulators, accurate DOS & energy (needs Γ-centered mesh). |
| `-4` | Tetrahedron (no Blöchl) | Semiconductors/insulators (Γ-centered mesh). |
| `-3` | Loop over `SMEARINGS` | Scan multiple SIGMA values. |
| `-2` | Fixed occupancies | From WAVECAR or `FERWE`/`FERDO`. |
| `-1` | Fermi–Dirac | Metals. |
| `0` | Gaussian | Metals / general / **good default when unsure** and for relaxations. |
| `N>0` | Methfessel–Paxton order N | Metals (accurate forces); ⚠️ **unphysical for insulators**. |

**Recommendations:** Metals → `1` or `2` (MP) with appropriate `SIGMA`, or `0`; final accurate DOS/energy → `-5`. Insulators/semiconductors → `0` or `-5`, never `N>0`. For molecules/large gaps, a small `SIGMA` with `0` is safest.

**Related:** SIGMA, FERWE/FERDO, SMEARINGS, KPOINTS (Γ-centered for tetrahedron).
