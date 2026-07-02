# NELMIN

> Source: <https://www.vasp.at/wiki/index.php/NELMIN>

**Type:** integer · **Default:** `2`

Minimum number of electronic SCF steps per ionic step.

**Recommendation:** For MD or ionic relaxation, increase to **4–8** so the density keeps up with the moving ions each step (improves stability/accuracy of forces).

**Related:** NELM, NELMDL.
