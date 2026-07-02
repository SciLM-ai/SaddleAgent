# SIGMA

> Source: <https://www.vasp.at/wiki/index.php/SIGMA>

**Type:** real (eV) · **Default:** `0.2`

Width of the electronic smearing (see [ISMEAR](ismear.md)).

**Recommendations:**
- Check the entropy term **`T*S` per atom** in the OUTCAR — it should be small (≲ 1 meV/atom); if large, `SIGMA` is too big.
- Typical range **0.05–0.2 eV**. Metals tolerate 0.1–0.2; insulators/semiconductors use 0.05–0.1 (or a tetrahedron method).
- Excessive smearing degrades both convergence and physical accuracy.

**Related:** ISMEAR, EFERMI.
