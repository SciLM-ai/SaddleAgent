# ASE — Nudged Elastic Band

> Source: <https://ase-lib.org/ase/neb.html>. ASE's own NEB implementation (Python). For VASP's compiled VTST NEB see [../vtst/neb.md](../vtst/neb.md).

## The NEB class

```python
class ase.mep.neb.NEB(images, k=0.1, climb=False, parallel=False,
                      remove_rotation_and_translation=False, world=None,
                      method=None, allow_shared_calculator=False, precon=None,
                      **kwargs)
```

Nudged elastic band method for finding transition paths and energy barriers between initial and final states.

| Parameter | Type | Description | Default |
|---|---|---|---|
| `images` | list of Atoms | Images defining the path from initial to final state | required |
| `k` | float or list | Spring constant(s) in eV/Å | `0.1` |
| `climb` | bool | Use a climbing image | `False` |
| `parallel` | bool | Distribute images over processors | `False` |
| `remove_rotation_and_translation` | bool | Activate NEB-TR (remove translation/rotation) | `False` |
| `world` | MPI communicator | MPI world object | `None` |
| `method` | str | `'aseneb'`, `'improvedtangent'`, `'eb'`, `'spline'`, `'string'` | `'improvedtangent'` |
| `allow_shared_calculator` | bool | Allow images to share one calculator | `False` |
| `precon` | str or Precon | Preconditioning for `'spline'`/`'string'` | `None` |

```python
from ase import io
from ase.mep import NEB
from ase.optimize import MDMin

initial = io.read('A.traj')
final = io.read('B.traj')

images = [initial]
images += [initial.copy() for i in range(3)]
images += [final]

neb = NEB(images)
neb.interpolate()                 # linear interpolation of the 3 middle images

for image in images[1:4]:
    image.calc = MyCalculator(...)

optimizer = MDMin(neb, trajectory='A2B.traj')
optimizer.run(fmax=0.04)
```

## Interpolation

```python
NEB.interpolate()                 # linear
NEB.interpolate(method='idpp')    # improved (image-dependent pair potential)
```

```python
ase.mep.neb.interpolate(images, mic=False, interpolate_cell=False,
                        use_scaled_coord=False, apply_constraint=None)
```
Linearly interpolate the interior images of a list.

| Parameter | Description | Default |
|---|---|---|
| `mic` | Map movement into the cell via minimum image convention | `False` |
| `interpolate_cell` | Interpolate the three cell vectors linearly | `False` |
| `use_scaled_coord` | Interpolate in scaled/fractional coordinates | `False` |
| `apply_constraint` | Apply constraints when setting positions | `None` |

```python
ase.mep.neb.idpp_interpolate(images, traj='idpp.traj', log='idpp.log',
                             fmax=0.1, optimizer=MDMin, mic=False, steps=100)
```
Interpolate with the IDPP method (`images` may be a list or an `NEB`).

## Climbing image

The climbing image feels no spring forces, and the potential force component parallel to the chain is reversed, driving it to the saddle.

```python
neb = NEB(images, climb=True)
```
> Quasi-Newton methods (BFGS) are not well suited to climbing-image NEB; FIRE works well.

## Scaled / dynamic optimization — DyNEB

```python
class ase.mep.dyneb.DyNEB(images, k=0.1, fmax=0.05, climb=False, parallel=False,
                          remove_rotation_and_translation=False, world=None,
                          dynamic_relaxation=True, scale_fmax=0.0, method=None,
                          allow_shared_calculator=False, precon=None)
```
Does not perform force calls on images already below the convergence criterion.

| Parameter | Description | Default |
|---|---|---|
| `fmax` | Convergence criterion (must match the optimizer) | `0.05` |
| `dynamic_relaxation` | Skip converged images | `True` |
| `scale_fmax` | Scale convergence by distance to the peak | `0.0` |

```python
neb = DyNEB(images, fmax=0.05, dynamic_relaxation=True, scale_fmax=1.)
```
> A low scaling factor (`scale_fmax = 1–3`) significantly reduces force calls.

## Parallelization over images

For an MPI-enabled interpreter (e.g. GPAW's `gpaw-python`):

```python
from ase.parallel import world
from ase.calculators.emt import EMT

n = len(images) - 2
j = world.rank * n // world.size
for i, image in enumerate(images[1:-1]):
    if i == j:
        image.calc = EMT()

neb = NEB(images, parallel=True)
```

Shared calculators: `NEB(images, allow_shared_calculator=True)`.

## Analysis — NEBTools

```python
class ase.mep.neb.NEBTools(images)
```

- `get_barrier(fit=True, raw=False)` — barrier estimate and ΔE of the elementary reaction. `fit` = interpolated-fit vs max-energy image; `raw` = raw TS energy instead of forward barrier.
- `get_fmax(**kwargs)` — fmax as used by optimizers with NEB.
- `plot_band(ax=None)` — plot the band on a matplotlib axes (new figure if `ax=None`).
- `plot_bands(constant_x=False, constant_y=False, nimages=None, label='nebplots')` — plot each band of a multi-step NEB trajectory into one PDF.
- `get_fit()` — *deprecated (3.23.0)*; use `ase.utils.forcecurve.fit_images(images)`.

Command line: `ase nebplot neb.traj` (`ase nebplot -h` for help).

## AutoNEB

```python
class ase.mep.autoneb.AutoNEB(attach_calculators, prefix, n_simul, n_max,
                              iter_folder='AutoNEB_iter', fmax=0.025, maxsteps=10000,
                              k=0.1, climb=True, method='eb', optimizer=FIRE,
                              remove_rotation_and_translation=False,
                              space_energy_ratio=0.5, world=None, parallel=True,
                              smooth_curve=False, interpolate_method='idpp')
```
Streamlines NEB/CI-NEB (Kolsbjerg et al., *J. Chem. Phys.* **145**, 094107 (2016)).

| Parameter | Description | Default |
|---|---|---|
| `attach_calculators` | Function adding calculators to images | required |
| `prefix` | Prefix for read/written files | required |
| `n_simul` | Relaxations run in parallel | required |
| `n_max` | Final number of images (incl. endpoints) | required |
| `fmax` | Max force along the path | `0.025` |
| `k` | Spring constant | `0.1` |
| `climb` | CI-NEB at the top point | `True` |
| `method` | `'aseneb'`, `'improvedtangent'`, `'eb'` | `'eb'` |
| `space_energy_ratio` | New-image placement (0=energy, 1=geometry) | `0.5` |
| `interpolate_method` | Interpolation method | `'idpp'` |

File naming: initial `prefix000.traj … prefix00N.traj`; during the i-th optimization `prefixXXXiter00i.traj`.

## References
1. Jónsson, Mills, Jacobsen, in *Classical and Quantum Dynamics in Condensed Phase Systems* (World Scientific, 1998).
2. Henkelman, Jónsson, *J. Chem. Phys.* **113**, 9978 (2000).
3. Henkelman, Uberuaga, Jónsson, *J. Chem. Phys.* **113**, 9901 (2000).
4. Smidstrup, Pedersen, Stokbro, Jónsson, *J. Chem. Phys.* **140**, 214106 (2014).
5. Lindgren, Kastlunger, Peterson, *J. Chem. Theory Comput.* **15**, 5787 (2019).
6. Kolsbjerg, Groves, Hammer, *J. Chem. Phys.* **145**, 094107 (2016).
7. Makri, Ortner, Kermode, *J. Chem. Phys.* **150**, 094109 (2019).
