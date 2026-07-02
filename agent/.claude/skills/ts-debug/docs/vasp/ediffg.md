# EDIFFG

> Source: <https://www.vasp.at/wiki/index.php/EDIFFG>

**Type:** real · **Default:** `EDIFF × 10`

Break condition for the **ionic** relaxation loop. The sign chooses the criterion:

- **Positive:** stop when the total-energy change between ionic steps is below `EDIFFG` (eV).
- **Negative:** stop when **all** force norms are below `|EDIFFG|` (eV/Å). Usually more convenient — and **required (negative) by the VTST NEB/dimer/Lanczos methods** (e.g. `-0.01` to `-0.03`).
- **Zero:** stop only after `NSW` steps.

Does **not** apply to molecular dynamics.

**Related:** EDIFF, NSW, NWRITE; see [../vtst/optimizers.md](../vtst/optimizers.md).
