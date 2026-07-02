# PREC

> Source: <https://www.vasp.at/wiki/index.php/PREC>

**Allowed:** `Normal | Single | SingleN | Accurate | Low | Medium | High` · **Default:** `Normal` (VASP ≥5), `Medium` (4.x)

Precision mode — sets defaults for the cutoff (`ENCUT`), FFT grids (`NGX/Y/Z`, `NGXF/YF/ZF`), and real-space projector accuracy (`ROPT`).

| PREC | NG (coarse) | NGF (fine) | ROPT (LREAL=Auto) |
|---|---|---|---|
| `Normal` | 3/2 × G_cut | 2× NGX | −5×10⁻⁴ |
| `Single` | 3/2 (v5) / 2× (v6) | = NGX (no double grid) | −5×10⁻⁴ |
| `Accurate` | 2× G_cut | 2× NGX | −2.5×10⁻⁴ |

**Recommendations:** Use **`Normal`** for routine work and **`Accurate`** for forces, phonons, stress, and second derivatives (denser grid → fewer egg-box/aliasing errors). Always set `ENCUT` explicitly; `PREC=Accurate` does **not** guarantee convergence. `Low`/`Medium`/`High` are deprecated.

**Related:** ENCUT, NGX/Y/Z, LREAL, ADDGRID, ROPT.
