# Dynamical Matrix (vibrations & prefactors)

> VTST Tools method page. Converted from VTST `dymmat.html`. See also: [scripts.md](scripts.md) (`dym*` tools), [neb.md](neb.md), [dimer.md](dimer.md).

The dynamical-matrix code computes harmonic vibrational frequencies and the **Vineyard rate prefactor** of a reaction. The potential is assumed harmonic at both the initial state and the transition state; the migration prefactor (attempt frequency × exp(migration entropy / k)) is then the **ratio of the products of the normal-mode frequencies** of the initial state over those of the transition state.

To compute a prefactor you must already know **both** the initial state and the transition state (find the TS with [NEB](neb.md) or the [dimer](dimer.md)). The same calculation also gives the harmonic frequencies/modes of a single optimized molecule (only the initial state needed).

## Required INCAR
| Parameter | Value | Description |
|---|---|---|
| `ICHAIN` | `1` | Use the dynamical-matrix method. |
| `IBRION` | `3` | VASP does MD with a zero time step. |
| `POTIM` | `0` | Zero time step — VASP does not move the ions. |
| [`EDIFF`](../vasp/ediff.md) | `1E-8` | Tight electronic convergence — accurate force differences (curvature). |
| [`EDIFFG`](../vasp/ediffg.md) | `-1E-8` | Set tiny so VASP does not quit early when forces are low. |
| [`NSW`](../vasp/nsw.md) | `DOF+1` | One force call at equilibrium plus one per displaced degree of freedom. |

Also carry over **all** the electronic settings from the geometry optimization (`ISMEAR`, `SIGMA`, `PREC`, …). A small smearing is especially important for molecules with a large HOMO–LUMO gap.

## Setup workflow
1. Use a VASP compiled with the VTST source.
2. **Generate a `DISPLACECAR`** (a 3×N list of finite displacements, typically ~0.001 Å) selecting which atoms/DOF to displace:
   - `dymselsph.pl <POSCAR> <central atom> <radius> <displacement>` — select atoms within a radius of the center atom(s).
   - `dymseldsp.pl <POSCAR 1> <POSCAR 2> <atoms to include> <displacement>` — select the most-displaced atoms between two POSCARs (e.g. minimum vs TS).
3. **(Optional) Parallel mode.** To run multiple displacements at once, choose `M` images that evenly divides the displaced DOF; make subdirs `01..M` (two digits), each with the `POSCAR`. Set `IMAGES=M`.
4. **INCAR.** Set `ICHAIN=1`, `POTIM=0.0`, `IMAGES=M` (parallel only), and `NSW=(DOF/M)+1`.
   - *Why +1:* each calculation first does a force call on the undisplaced structure. Single image → `NSW = DOF+1`. Parallel → `NSW = DOF/M + 1`. (E.g. ethane, 8 atoms × 3 = 24 DOF: single image `NSW=25`; with `M=4`, `IMAGES=4` and `NSW=7`.)
5. **Run VASP** with `POTCAR, POSCAR, INCAR, DISPLACECAR, KPOINTS` all present. The POSCAR geometry should already be optimized.
6. **Extract force constants** with `dymmatrix.pl` (see [scripts.md](scripts.md)):
   - `dymmatrix.pl` or `dymmatrix.pl DISPLACECAR OUTCAR` — single calc, single image.
   - `dymmatrix.pl 1 DISPLACECAR ??/OUTCAR` — single calc, multiple images.
   - `dymmatrix.pl n DISPLACECAR1 … DISPLACECARn OUTCAR1 … OUTCARn` — multiple calcs.

   Output: the dynamical matrix, its eigenvalues (`eigs.dat`, ω²), the normal-mode frequencies (`freq.dat`, cm⁻¹), and eigenvectors (`modes.dat`).
7. **If all frequencies come out zero**, check `EDIFFG` in the INCAR (set it tiny so VASP doesn't stop early). The number of force calls should equal `NSW`.
8. **Check convergence** of the frequencies vs the finite-difference magnitude (`DISPLACECAR`), the force accuracy (`EDIFF`), and the smearing.
9. **Compute the prefactor** (for a rate, not just frequency analysis):
   - `dymprefactor.pl <freq.dat of minimum> <freq.dat of transition state>` — outputs the prefactor (cm⁻¹). The minimum must have 0 imaginary modes; the TS exactly 1.

## Adding more degrees of freedom later
To extend an existing prefactor calculation with more DOF:
1. Save the previous OUTCARs.
2. Create the new `DISPLACECAR`.
3. Diff against the old one with `dymcmpdisp.pl` (run VASP only on the **new** DOF).
4. Update `NSW`.
5. Run VASP.
6. Re-extract with `dymmatrix.pl`, passing the original DISPLACECAR, the new DISPLACECAR (new DOF only), and all corresponding OUTCARs.

## Units
Frequencies are reported in **cm⁻¹** (`dymmatrix` uses the factor `521.47` = √(eV/(Å²·amu))→cm⁻¹). Imaginary modes are flagged; the TS should have exactly one. ZPE/rate post-processing: `dymzpbar.pl`, `dymeffbar.pl`, `dymrate.pl`.
