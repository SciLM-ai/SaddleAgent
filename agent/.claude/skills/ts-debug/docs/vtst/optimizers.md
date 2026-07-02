# Force-Based Optimizers (IOPT)

> VTST Tools method page. Converted from VTST `optimizers.html`. See also: [neb.md](neb.md), [dimer.md](dimer.md), [lanczos.md](lanczos.md).

The NEB and min-mode-following (dimer/Lanczos) methods modify the force (projection), so the energy is no longer consistent with the optimized force. Only **force-based** optimizers can be used. VASP's built-in quasi-Newton (`IBRION=1`) and quick-min (`IBRION=3`) are force-based, but conjugate-gradient (`IBRION=2`) is **not**.

VTST provides its own set of force-based optimizers. To use them, set `IBRION=3` and `POTIM=0` (disabling VASP's optimizer), then pick the method with **`IOPT`**.

> A min-mode-following run with no `IOPT` set will **die** with an error.

**Choosing:** use **CG or LBFGS** when accurate forces are available (essential for evaluating curvatures). For high forces (far from the minimum) or inaccurate forces (close to it), use **quick-min or FIRE** — they don't rely on curvatures and are better-behaved but less efficient. (Sheppard, Terrell, Henkelman, *J. Chem. Phys.* **128**, 134106 (2008).)

## IOPT values
| IOPT | Method |
|---|---|
| `0` | Use VASP's optimizer (from `IBRION`) — **default** |
| `1` | LBFGS — Limited-memory Broyden–Fletcher–Goldfarb–Shanno |
| `2` | CG — Conjugate Gradient (Newton line optimizer, force-based) |
| `3` | QM — Quick-Min |
| `4` | SD — Steepest Descent (mainly for testing) |
| `7` | FIRE — Fast Inertial Relaxation Engine |
| `8` | ML-PYAMFF — machine-learning optimizer (vtstcode6.3 only) |

## Required / recommended INCAR
**Must be set to these values:**

| Parameter | Value | Description |
|---|---|---|
| `IBRION` | `3` | VASP does MD with a zero time step. |
| `POTIM` | `0` | Zero time step — VASP itself does not move the ions. |

**User-chosen (recommended):**

| Parameter | Recommended | Description |
|---|---|---|
| `IOPT` | `3` | Quick-Min is the most beginner-friendly (default is `IOPT=0`). |
| [`NSW`](../vasp/nsw.md) | `100` | Number of ionic relaxation steps. |
| [`EDIFFG`](../vasp/ediffg.md) | `-0.01` | Must be **negative** (force criterion). |

## Per-optimizer parameters

**LBFGS (IOPT = 1):**

| Parameter | Default | Description |
|---|---|---|
| `MAXMOVE` | `0.2` | Maximum step size for translation (Å). |
| `ILBFGSMEM` | `20` | Steps saved when building the inverse Hessian. |
| `LGLOBAL` | `.TRUE.` | Optimize the NEB globally instead of image-by-image. |
| `LAUTOSCALE` | `.TRUE.` | Automatically determine `INVCURV`. |
| `INVCURV` | `0.01` | Initial inverse curvature for the inverse Hessian. |
| `LLINEOPT` | `.FALSE.` | Use a force-based line minimizer for translation. |
| `FDSTEP` | `5E-3` | Finite-difference step for the line optimizer. |

**CG (IOPT = 2):**

| Parameter | Default | Description |
|---|---|---|
| `MAXMOVE` | `0.2` | Maximum step size for translation (Å). |
| `FDSTEP` | `5E-3` | Finite-difference step to calculate curvature. |

**QM — Quick-Min (IOPT = 3):**

| Parameter | Default | Description |
|---|---|---|
| `MAXMOVE` | `0.2` | Maximum step size for translation (Å). |
| `TIMESTEP` | `0.1` | Dynamical time step. |

**SD — Steepest Descent (IOPT = 4):**

| Parameter | Default | Description |
|---|---|---|
| `MAXMOVE` | `0.2` | Maximum step size for translation (Å). |
| `SDALPHA` | `0.01` | Ratio between force and step size. |

**FIRE (IOPT = 7):**

| Parameter | Default | Description |
|---|---|---|
| `MAXMOVE` | `0.2` | Maximum step size for translation (Å). |
| `TIMESTEP` | `0.1` | Dynamical time step. |
| `FTIMEMAX` | `1.0` | Maximum dynamical time step allowed. |
| `FTIMEDEC` | `0.5` | Factor to decrease dt. |
| `FTIMEINC` | `1.1` | Factor to increase dt. |
| `FALPHA` | `0.1` | Velocity-damping parameter. |
| `FNMIN` | `5` | Minimum iterations before adjusting alpha and dt. |

**ML-PYAMFF (IOPT = 8, vtstcode6.3 only).** Trains a Behler-Parrinello neural network and optimizes on the surrogate PES, reducing DFT force calls over cycles. Requires a formatted model file (`PYAMFF_MODEL`, default `mlff.pyamff`).

| Parameter | Default | Description |
|---|---|---|
| `PYAMFF_MODEL` | `mlff.pyamff` | Input file for neural-network parameters. |
| `PYAMFF_CONV` | `GRADNORM` | NN training convergence criterion (`GRADNORM`, `RMSE`). |
| `PYAMFF_ETOL` | `0.001` | Energy RMSE tolerance. |
| `PYAMFF_FTOL` | `0.01` | Force RMSE tolerance. |
| `PYAMFF_TOL` | `0.001` | Gradnorm tolerance. |
| `PYAMFF_FCOEFF` | `1.0` | Force-loss contribution to training. |
| `PYAMFF_MAXEPOCH` | `2000` | Maximum NN training epochs. |
| `PYAMFF_OPT` | `RPROP` | NN training optimizer (`RPROP`, `ADAM`, `LBFGS`). |
| `PYAMFF_SWFTOL` | `0.05` | Criterion to switch ML-optimizer → LBFGS. |
| `PYAMFF_MAXMOVE` | `0.5` | Max total translation step by the ML-optimizer. |
| `PYAMFF_MAXITER` | `30` | Max relaxation steps on the ML PES. |
