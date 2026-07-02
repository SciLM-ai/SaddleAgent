# IBRION

> Source: <https://www.vasp.at/wiki/index.php/IBRION>

**Allowed:** `-1, 0, 1, 2, 3, 5, 6, 7, 8, 11, 12, 40, 44` · **Default:** `-1` (if `NSW ≤ 0`), else `0`

Determines how the ions/cell are updated during the calculation.

| Value | Method | Use case |
|---|---|---|
| **-1** | No update | Static/single-point (avoid with `NSW > 0`). |
| **0** | Molecular dynamics | MD via classical equations of motion. |
| **1** | RMM-DIIS | Relaxation; best for >20 DOF near the ground state. |
| **2** | Conjugate gradient | Relaxation; robust default, may need more steps. |
| **3** | Damped MD | Relaxation; large systems far from the minimum. **VTST NEB/dimer/Lanczos require `IBRION=3` + `POTIM=0`.** |
| **5** | Finite differences (no symmetry) | Phonon modes. |
| **6** | Finite differences (with symmetry) | Phonon modes (fewer displacements). |
| **7** | DFPT (no symmetry) | Phonon modes. |
| **8** | DFPT (with symmetry) | Phonon modes. |
| **40** | IRC | Intrinsic-reaction-coordinate from a TS. |
| **44** | Improved dimer | VASP-native TS search from an arbitrary structure. |
| **11** | Interactive | New structures via standard input. |
| **12** | Python plugin | Structure modification via a Python plugin. |

**Notes:** For phonons set `EDIFF ≤ 1E-6` (the `1E-4` default gives large errors). Use the symmetry variants (6/8) to cut cost. Limit MD output via `NWRITE`/`NBLOCK`/`KBLOCK`.

**Related:** NSW, POTIM, MDALGO, SMASS, NFREE, ISIF, LEPSILON, LCALCEPS.
