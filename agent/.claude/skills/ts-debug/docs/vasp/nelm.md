# NELM

> Source: <https://www.vasp.at/wiki/index.php/NELM>

**Type:** integer · **Default:** `60`

Maximum number of electronic self-consistency (SCF) steps per ionic step.

**Recommendations:** Keep the default unless converging is hard. If the SCF won't converge in ~40 steps, fix the cause (`ALGO`/`IALGO`, `LSUBROT`, mixing `AMIX`/`BMIX`, smearing) rather than just raising `NELM`. Use [`NELMIN`](nelmin.md) to force a minimum number of steps (useful in relaxations/MD where the density changes each ionic step).

**Related:** NELMIN, NELMDL, EDIFF, ALGO.
