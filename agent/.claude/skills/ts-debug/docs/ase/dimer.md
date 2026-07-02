# ASE — Dimer method

> Source: <https://ase-lib.org/ase/dimer.html>. ASE's own dimer implementation (Python), inspired (with permission) by the Henkelman group code. For VASP's compiled VTST dimer see [../vtst/dimer.md](../vtst/dimer.md).

The dimer method finds a saddle point starting from a **single** point on the PES (unlike NEB, which needs an initial and a final state).

**Reference:** G. Henkelman, H. Jónsson, "A dimer method for finding saddle points on high dimensional potential surfaces using only first derivatives," *J. Chem. Phys.* **111**, 7010 (1999).

## Example

```python
from ase.build import add_adsorbate, fcc100
from ase.calculators.emt import EMT
from ase.constraints import FixAtoms
from ase.mep import DimerControl, MinModeAtoms, MinModeTranslate

# Pt(100) slab with a Pt adatom
atoms = fcc100('Pt', size=(2, 2, 1), vacuum=10.0)
add_adsorbate(atoms, 'Pt', 1.611, 'hollow')

# Freeze the slab
mask = [atom.tag > 0 for atom in atoms]
atoms.set_constraint(FixAtoms(mask=mask))

atoms.calc = EMT()
atoms.get_potential_energy()

# Set up the dimer
with DimerControl(initial_eigenmode_method='displacement',
                  displacement_method='vector', logfile=None,
                  mask=[0, 0, 0, 0, 1]) as d_control:
    d_atoms = MinModeAtoms(atoms, d_control)

    # Displace the atoms
    displacement_vector = [[0.0] * 3] * 5
    displacement_vector[-1][1] = -0.1
    d_atoms.displace(displacement_vector=displacement_vector)

    # Converge to a saddle point
    with MinModeTranslate(d_atoms, trajectory='dimer_method.traj',
                          logfile=None) as dim_rlx:
        dim_rlx.run(fmax=0.001)
```

## DimerControl

```python
class ase.mep.dimer.DimerControl(logfile='-', eigenmode_logfile=None,
                                 comm=<MPI>, **kwargs)
```
Holds the parameters for a dimer search.

| Name | Type | Description |
|---|---|---|
| `eigenmode_method` | str | Name of the eigenmode-search method. |
| `f_rot_min` | float | Rotational-force size below which **no** rotation is performed. |
| `f_rot_max` | float | Rotational-force size below which **only one** rotation is performed. |
| `max_num_rot` | int | Maximum rotations per optimizer step. |
| `trial_angle` | float | Trial angle (radians) for the finite-difference rotational-angle estimate. |
| `trial_trans_step` | float | Trial step size for `MinModeTranslate`. |
| `maximum_translation` | float | Max (and forced, when curvature is still positive) step for `MinModeTranslate`. |
| `cg_translation` | bool | Conjugate-gradient translation. |
| `use_central_forces` | bool | Compute forces at one dimer end and extrapolate to the other. |
| `dimer_separation` | float | Separation of the dimer's two images. |
| `initial_eigenmode_method` | str | How to build the initial eigenmode: `'gauss'` or `'displacement'`. |
| `extrapolate_forces` | bool | Extrapolation to reduce force calls when >1 rotation is done. |
| `displacement_method` | str | How to displace the atoms: `'gauss'` or `'vector'`. |
| `gauss_std` | float | Std of the Gaussian for random displacement. |
| `order` | int | How many lowest eigenmodes to invert. |
| `mask` | list of bool | Which atoms move during displacement. |
| `displacement_center` | int or [float×3] | Center of displacement (nearby atoms are displaced). |
| `displacement_radius` | float | How far around `displacement_center` to displace. |
| `number_of_displacement_atoms` | int | How many atoms near the center to displace. |

## MinModeAtoms

```python
class ase.mep.dimer.MinModeAtoms(atoms, control=None, eigenmodes=None,
                                 random_seed=None, comm=<MPI>, **kwargs)
```
Wraps an `Atoms` object with min-mode-search info: the lowest-eigenvalue estimate (`curvature`) and its eigenmode (`eigenmode`). The forces are modified by inverting the component along the eigenmode estimate, driving the system to a saddle.

| Name | Type | Description |
|---|---|---|
| `atoms` | Atoms | A regular Atoms object. |
| `control` | MinModeControl | Eigenmode-search parameters (a default `DimerControl` is created if omitted). |
| `mask` | list of bool | Which atoms move when calling `displace()`. |
| `random_seed` | int | Seed for the RNG (defaults to a time-based value). |

## MinModeTranslate

```python
class ase.mep.dimer.MinModeTranslate(dimeratoms, logfile='-', trajectory=None)
```
An optimizer tailored to minimum-mode following.

| Name | Type | Description |
|---|---|---|
| `atoms` | Atoms | The object to relax. |
| `restart` | str/Path/None | Restart filename (default `None`). |
| `logfile` | file/Path/str | `'-'` for stdout. |
| `trajectory` | Trajectory/Path/str | Trajectory to attach (`None` = none). |
| `append_trajectory` | bool | Append instead of overwrite. |

## DimerEigenmodeSearch

```python
class ase.mep.dimer.DimerEigenmodeSearch(dimeratoms, control=None,
                                         eigenmode=None, basis=None, **kwargs)
```
Implements the rotational (eigenmode-search) part of the dimer method.

| Name | Type | Description |
|---|---|---|
| `atoms` | MinModeAtoms | Includes the lowest-eigenvalue-mode info. |
| `control` | DimerControl | Eigenmode-search parameters. |
| `basis` | list of xyz | An (n,3) eigenmode; the searched modes can be constrained orthogonal to it. |

**References:** Henkelman & Jónsson, *JCP* **111**, 7010 (1999); Olsen et al., *JCP* **121**, 9776 (2004); Heyden, Bell, Keil, *JCP* **123**, 224101 (2005); Kästner & Sherwood, *JCP* **128**, 014106 (2008).
