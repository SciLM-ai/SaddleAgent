# ENCUT

> Source: <https://www.vasp.at/wiki/index.php/ENCUT>

**Type:** real (eV) · **Default:** largest `ENMAX` in the POTCAR

Plane-wave kinetic-energy cutoff: all plane waves below `ENCUT` are in the basis.

**Recommendations:**
- Always converge `ENCUT` for the quantity of interest.
- **Set `ENCUT` explicitly** in the INCAR for consistency across compared calculations (differing defaults cause cohesive-energy errors).
- For cell/volume relaxation, use ~**1.3×ENMAX** (the basis is not re-adjusted as the cell changes — see [isif.md](isif.md)).

**Related:** ENMAX, ENAUG, PREC, NGX/Y/Z, POTCAR.
