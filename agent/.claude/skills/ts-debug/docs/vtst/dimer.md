# The Dimer Method

> VTST Tools method page. Converted from VTST `dimer.html`. See also: [optimizers.md](optimizers.md), [lanczos.md](lanczos.md), [scripts.md](scripts.md).

The dimer method is a **min-mode following** saddle search: starting from any single configuration, it climbs to a *nearby* saddle point without knowing the product state. It works by estimating the lowest-curvature mode of the Hessian (via a finite "dimer" of two images separated by a small distance) and inverting the force component along that mode, so the system moves uphill along the softest direction and downhill in all others. This is the tool of choice when reaction mechanisms are unknown (where guessing endpoints for an [NEB](neb.md) is not possible).

> VASP also has a native *improved dimer* (`IBRION = 44`), which does not need VTST. The page below documents the **VTST external dimer** (`ICHAIN = 2`). See [../vasp/ibrion.md](../vasp/ibrion.md).

## Calculation setup
Like a normal VASP run, plus a mode vector. Required input files:

1. **POTCAR**, **KPOINTS** — prepared as usual.
2. **INCAR** — all the usual tags, plus: `IBRION=3`, `POTIM=0`, and some `IOPT` (`IOPT=2` recommended). See [optimizers.md](optimizers.md).
3. **POSCAR** — the starting configuration (a point near a known saddle, or far away such as near a minimum).
4. **MODECAR** — the initial dimer direction, a Cartesian **unit vector** estimating the lowest-curvature mode. If absent, a **random** direction is used. Creating a MODECAR is strongly recommended: the important thing is that its largest components lie in the coordinates likely involved in the reaction. Generate it automatically from an NEB with `neb2dim.pl`, or as the vector between two configurations with `modemake.pl` (see [scripts.md](scripts.md)).

A common use is to converge a saddle accurately starting from an NEB: the dimer needs fewer images than the NEB, so it is cheaper for tightening convergence at higher `ENCUT` or finer k-points. `neb2dim.pl` builds the initial `POSCAR` (interpolated saddle) and `MODECAR` (NEB tangent at that point).

## INCAR parameters
**Required:**

| Parameter | Value | Description |
|---|---|---|
| `ICHAIN` | `2` | Use the dimer method (required for the current code). |
| `IBRION` | `3` | VASP does MD with a zero time step. |
| `POTIM` | `0` | Zero time step — VASP itself does not move the ions. |

**Standard (dimer-specific, prefix `D`):**

| Parameter | Default | Description |
|---|---|---|
| `DdR` | `5E-3` | Dimer separation (twice the distance between the two images), in Å. |
| `DRotMax` | `1` | Maximum number of rotation steps per translation step. |
| `DFNMin` | `0.01` | Rotational-force magnitude **below which the dimer is not rotated**. |
| `DFNMax` | `1.0` | Rotational-force magnitude below which dimer rotation stops; between `DFNMin` and `DFNMax`, at least one rotation iteration is done. |

You must also set [optimizer](optimizers.md) parameters (an `IOPT`); a dimer run with no `IOPT` dies with an error.

## Output — the DIMCAR file
A summary line per iteration is written to **DIMCAR** (full detail, prefixed `Dimer`, is in OUTCAR). The six columns:

1. **Step** — number of translation steps (there can be several rotations per step).
2. **Force** — max force on any degree of freedom. Converged when this is below `-EDIFFG` **and** the curvature is negative.
3. **Torque** — rotational force on the dimer; indicates accuracy of the lowest mode.
4. **Energy** — energy of the dimer centre. *Not* the extrapolated (sigma→0) energy; do **not** read the saddle energy from here — take it from OUTCAR.
5. **Curvature** — curvature along the dimer (best estimate of the lowest mode). A **negative** curvature with a **decreasing** force signals convergence toward a saddle; a positive curvature means the run must continue.
6. **Angle** — angle the dimer rotated through. May start high but should drop and stay low; a persistently high value (~1) signals a problem.

**Diagnostics:** Force, Torque and Curvature matter most. The Torque should drop systematically as the dimer rotates — if it doesn't, the forces are not accurate enough: lower `EDIFF` to ~`1E-7`–`1E-8`, and/or raise the finite-difference distance `DdR` up to ~0.01 Å. Converging means Force dropping and Curvature consistently negative; a large force or positive curvature just means you are not yet near a saddle.

## References
- G. Henkelman, H. Jónsson, *J. Chem. Phys.* **111**, 7010 (1999) — dimer method.
- J. Kästner, P. Sherwood, *J. Chem. Phys.* **128**, 014106 (2008) — superlinearly converging dimer.
- P. Xiao, D. Sheppard, J. Rogal, G. Henkelman, *J. Chem. Phys.* **140**, 174104 (2014) — solid-state dimer.
