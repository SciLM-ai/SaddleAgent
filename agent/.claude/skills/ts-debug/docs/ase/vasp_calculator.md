# ASE — VASP Calculator

> Source: <https://ase-lib.org/ase/calculators/vasp.html>. Use VASP as an ASE calculator and ASE as a post-processor for finished VASP runs.

## Environment variables

**Execution** — set `ASE_VASP_COMMAND` (or legacy `VASP_COMMAND`):
```bash
export ASE_VASP_COMMAND="mpirun vasp_std"
```
Alternatively point `VASP_SCRIPT` at a `run_vasp.py` that does `os.system('vasp')`. The calculator's `command=` keyword overrides the environment.

**Pseudopotentials** — `VASP_PP_PATH` points at the directory holding `potpaw_PBE.64`, `potpaw_LDA.64`, … :
```bash
export VASP_PP_PATH=$HOME/vasp/mypps
export VASP_PP_VERSION=64
```
For vdW functionals, set `ASE_VASP_VDW` to the folder containing `vdw_kernel.bindat`.

## The Vasp class

```python
class ase.calculators.vasp.Vasp(atoms=None, restart=None, directory='.',
                                label='vasp', ignore_bad_restart_file=<obj>,
                                command=None, txt='vasp.out', **kwargs)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `atoms` | Atoms | `None` | Attach an atoms object. |
| `label` | str | `'vasp'` | Prefix for the output file / working directory. |
| `directory` | str | `'.'` | Working directory (prepended to `label`). |
| `restart` | str/bool | `None` | Load files from a restart dir; `True` = use the working directory. |
| `txt` | bool/None/str/obj | `'vasp.out'` | Output redirection: `None` suppress, `'-'` stdout, filename, or file object. |
| `command` | str | `None` | VASP execution command; overrides environment variables. |

**Selected keywords** (most VASP INCAR tags are accepted directly as lowercase keywords):

| Keyword | Type | Default | Description |
|---|---|---|---|
| `xc` | str | `'PW91'` | Exchange-correlation "recipe" (sets related params + `pp`). |
| `setups` | str/dict | `None` | PAW setup selection (see below). |
| `pp` | str | set by `xc`/`gga` | Pseudopotential set (LDA or PBE). |
| `pp_version` | str | `None` | Version suffix (`""`, `"52"`, `"54"`, `"64"`). |
| `kpts` | various | Γ-point | k-point sampling (see below). |
| `gamma` | bool | `None` | Γ-centered k-mesh. |
| `reciprocal` | bool | `None` | Explicit k-points given in reciprocal units. |
| `charge` | int | `None` | Net charge per cell (e); alternative to `nelect`. |
| `prec` | str | — | Accuracy (`prec='Accurate'`, …). |
| `encut` | float | — | Plane-wave cutoff. |
| `ediff` | float | — | SC-loop convergence. |
| `nbands` | int | — | Number of bands. |
| `algo` | str | — | Electronic minimization algorithm. |
| `ismear` | int | — | Smearing type. |
| `sigma` | float | — | Smearing width. |
| `nelm` | int | — | Max SC iterations. |
| `ldau_luj` | dict | — | Convenient LDA+U specification (see below). |

Modify after construction: `calc.set(prec='Accurate', ediff=1E-5)`.

> Input arguments specific to the [VTST add-ons](../vtst/overview.md) are also supported as keywords.

## Exchange-correlation (`xc`)

`xc` is a recipe that sets several related parameters (including `pp`). It is case-insensitive. Override any element with an explicit keyword, e.g. `Vasp(xc='hse06', hfscreen=0.4)`. Default PAW set is `potpaw_PBE` unless `xc`/`pp` is set to `lda`.

| `xc` | Sets |
|---|---|
| `lda`, `pbe` | `pp` (`gga` implicit in POTCAR) |
| `pbesol`, `revpbe`, `rpbe`, `am05` | `gga` |
| `blyp` | `gga`, `aldax`, `aggax`, `aggac`, `aldac` |
| `tpss`, `revtpss`, `m06l` | `metagga` |
| `vdw-df`, `optpbe-vdw` | `gga`, `luse_vdw`, `aggac` |
| `optb88-vdw`, `optb86b-vdw` | `gga`, `luse_vdw`, `aggac`, `param1`, `param2` |
| `beef-vdw` | `gga`, `luse_vdw`, `zab_vdw` |
| `vdw-df2` | `gga`, `luse_vdw`, `aggac`, `zab_vdw` |
| `hf` | `lhfcalc`, `aexx`, `aldac`, `aggac` |
| `pbe0` | `gga`, `lhfcalc` |
| `b3lyp` | `gga`, `lhfcalc`, `aexx`, `aggax`, `aggac`, `aldac` |
| `hse03`, `hse06`, `hsesol` | `gga`, `lhfcalc`, `hfscreen` |

Add a custom recipe: `Vasp.xc_defaults['pw91_0'] = {'gga': '91', 'lhfcalc': True}` (keys lowercase).

## Setups (PAW potentials)

Three base sets: **minimal** (default), **recommended**, **gw**.
```python
calc = Vasp(setups='recommended')
calc = Vasp(xc='PBE', setups={'Li': '_sv'})            # per element
calc = Vasp(xc='PBE', setups={3: 'Ga_d'})              # per atom (0-indexed)
calc = Vasp(xc='PBE', setups={'base': 'recommended', 'Li': '', 4: 'H.5'})
```

## Spin polarization

Automatic when atoms have non-zero magnetic moments; or force with `calc.set(ispin=2)`.
```python
from ase import Atom, Atoms
NaCl = Atoms([Atom('Na', [0,0,0], magmom=1.928),
              Atom('Cl', [0,0,2.3608], magmom=0.75)], cell=[6.5,6.5,7.7])
NaCl.calc = Vasp(prec='Accurate', xc='PBE', lreal=False)
NaCl.get_magnetic_moment()
```

## Brillouin-zone sampling

Controlled by `kpts`, `gamma`, `reciprocal` (and the VASP `kspacing`/`kgamma` tags).
- **Scalar `kpts`** (float/int) → length cutoff for the Γ-centered "Automatic" scheme.
- **`kspacing`/`kgamma`** in the INCAR → no KPOINTS file is written.
- **Three integers** `kpts=[2,2,3]` → Monkhorst-Pack (or Γ-centered if `gamma=True`).
- **n×3 or n×4 array** → explicit k-points (4th column = weights); usually with `reciprocal=True`.
- **Band paths** via `ase.dft.kpoints.bandpath('GXL', cell, npoints=20)`.

## LDA+U

```python
calc = Vasp(ldau_luj={'Si': {'L': 1, 'U': 3, 'J': 0}})
```
The convenient `ldau_luj` dict expands to `ldaul`/`ldauu`/`ldauj`; `ldau=True` is enabled automatically unless set `False`.

## Restart / post-processing

```python
calc = Vasp(restart=True)        # reads CONTCAR, OUTCAR, KPOINTS, INCAR
atoms = calc.get_atoms()
atoms.get_potential_energy()
```
> Only Monkhorst-Pack / Γ-centered sampling is supported for restart; some INCAR tags may be unimplemented. Wavefunctions/charge densities are **not** stored, so restarted results may differ.

## Saving calculator state (JSON)

- `asdict() -> dict` — `ase_version`, `vasp_version`, `inputs`, `results`, `atoms` (no `command`/`txt`/`directory`).
- `fromdict(dct)` — restore from such a dict.
- `write_json(filename)` / `read_json(filename)` — dump/load to JSON.

```python
calc.write_json('mystate.json')
calc = Vasp(); calc.read_json('mystate.json'); atoms = calc.get_atoms()
```

## Vibrational analysis

Use ASE's `Vibrations`, or VASP internals (`IBRION=5–8`):
- `get_vibrations() -> VibrationsData` — mass-weighted Hessian from `vasprun.xml` (POTCAR masses matter; see VASP wiki limitations).
- `read_vib_freq(lines=None) -> (real_freqs, imag_freqs)` — from OUTCAR.

## Examples

**Band structure:**
```python
from ase.build import bulk
from ase.calculators.vasp import Vasp
si = bulk('Si'); mydir = 'bandstructure'
calc = Vasp(kpts=(4,4,4), directory=mydir); si.calc = calc
si.get_potential_energy()                                  # SC ground state
calc.set(isym=0, icharg=11, kpts={'path': 'WGX', 'npoints': 30})
si.get_potential_energy()                                  # non-SC band path
# plot:
bs = Vasp(restart=True, directory=mydir).band_structure(); bs.plot(emin=-13, show=True)
# gap:
from ase.dft.bandgap import bandgap; bandgap(Vasp(restart=True, directory=mydir))
```

**Density of states:** `energies, dos = calc.get_dos()`.
