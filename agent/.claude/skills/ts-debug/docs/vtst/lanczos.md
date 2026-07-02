# Lanczos (Min-Mode Following)

> VTST Tools method page. Converted from VTST `lanczos.html`. See also: [dimer.md](dimer.md), [optimizers.md](optimizers.md).

The Lanczos method is a min-mode following saddle search, like the [dimer](dimer.md): from a minimum (or any starting configuration) it climbs to a nearby saddle. The **only** difference from the dimer is *how the lowest-curvature mode is found*: the dimer rotates a finite dimer; Lanczos approximates the lowest Hessian eigenvector by expansion in a growing Krylov subspace (the scheme used by Mousseau's ARTn). Once the lowest mode is found, the two methods proceed **identically**. Convergence properties of the two are comparable (Olsen et al., *J. Chem. Phys.* **121**, 9776 (2004)).

## INCAR parameters
All Lanczos-specific parameters use the prefix **`S`**.

**Required:**

| Parameter | Value | Description |
|---|---|---|
| `ICHAIN` | `3` | Use the Lanczos method. |
| `IBRION` | `3` | VASP does MD with a zero time step. |
| `POTIM` | `0` | Zero time step — VASP does not move the ions. |
| `EDIFF` | `1E-8` | Tight electronic convergence, needed for accurate force differences (the curvature). |

**Standard (defaults shown):**

| Parameter | Default | Meaning |
|---|---|---|
| `SLTOL` | `0.01` | Convergence tolerance for the Lanczos lowest eigenvalue (iterate until the eigenvalue change is below this). |
| `Sdr` | `0.001` | Finite-difference step (Å) used to probe the curvature along Lanczos vectors. |
| `SNL` | `20` | Maximum number of Lanczos iterations / maximum size of the Lanczos matrix per step. |

> **Accuracy note:** the descriptions for `SLTOL`, `Sdr`, `SNL` are **garbled in the source HTML** (the description cells contain placeholder text copied from the required-parameters table). The **names and default values above are taken verbatim from the source**; the meanings are the conventional Lanczos interpretations following the `S`-prefix convention and the method (eigenvalue tolerance / finite-difference step / subspace size). Treat the *meanings* as conventional, not source-verified — confirm against the running OUTCAR/LANCAR if a value is critical.

You must also set [optimizer](optimizers.md) parameters (an `IOPT`).

## Output — the LANCAR file
All Lanczos output goes to **LANCAR**; extract results with `grep`/`cut`/`head`/`tail`. Keywords to grep for:

| Keyword | Description |
|---|---|
| `For` | Force components at each central point (after translating the system). |
| `Coo` | Coordinate components at each central point. |
| `Low` | The lowest mode at each central point. |
| `eig` | The lowest-eigenvalue convergence sequence at each central point. |
| `conv` | Size of the Lanczos matrix, energy, maximum force, and lowest eigenvalue at each central point. |

## References
- R. A. Olsen, G. J. Kroes, G. Henkelman, A. Arnaldsson, H. Jónsson, *J. Chem. Phys.* **121**, 9776 (2004) — comparison of saddle-finding methods.
