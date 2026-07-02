# VTST Tools — Overview & method selector

> Converted from VTST `vtsttools.html` + `references.html`, plus a synthesis of the `ICHAIN` selector shared across the method pages.

**VTST Tools** are a set of methods (compiled into VASP via the vtstcode patch) and helper scripts (`vtstscripts`) for finding transition states, reaction paths, and rates with VASP. The method is selected in the INCAR by **`ICHAIN`**, and all of the saddle-search/path methods run on top of VASP's MD machinery (`IBRION=3`, `POTIM=0`) with a VTST force-based [optimizer](optimizers.md) (`IOPT`).

## Method selector (`ICHAIN`)
| `ICHAIN` | Method | Needs | Page |
|---|---|---|---|
| `0` | **NEB** — minimum energy path between known endpoints | reactant + product | [neb.md](neb.md) |
| `1` | **Dynamical matrix** — harmonic frequencies & rate prefactor | optimized state(s) | [dynmat.md](dynmat.md) |
| `2` | **Dimer** — min-mode-following saddle search | one structure + initial mode | [dimer.md](dimer.md) |
| `3` | **Lanczos** — min-mode-following saddle search | one structure + initial mode | [lanczos.md](lanczos.md) |

Shared requirements for NEB / dimer / Lanczos: `IBRION=3`, `POTIM=0`, and an `IOPT` choice (see [optimizers.md](optimizers.md)). The dynamical matrix uses `ICHAIN=1` with `NSW=DOF+1`.

## Typical TS-search workflow
1. **NEB** between a known reactant and product (`nebmake.pl` to build the band) → approximate saddle + MEP.
2. **Hand off to a dimer** (`neb2dim.pl`) or **Lanczos** (`neb2lan.pl`) to converge the saddle precisely (cheaper than NEB at higher `ENCUT`/finer k-points).
3. **Dynamical matrix** at the minimum and the saddle → vibrational frequencies; `dymprefactor.pl` → Vineyard rate prefactor.
4. Above is also the per-state engine of **Adaptive Kinetic Monte Carlo** (`akmc.pl`), which repeatedly searches for saddles and hops between states.

See [scripts.md](scripts.md) for every helper script.

## References

**Nudged elastic band:**
- D. Sheppard, P. Xiao, W. Chemelewski, D. D. Johnson, G. Henkelman, "A generalized solid-state nudged elastic band method," *J. Chem. Phys.* **136**, 074103 (2012).
- D. Sheppard, G. Henkelman, "Paths to which the nudged elastic band converges," *J. Comp. Chem.* **32**, 1769–1771 (2011).
- D. Sheppard, R. Terrell, G. Henkelman, "Optimization methods for finding minimum energy paths," *J. Chem. Phys.* **128**, 134106 (2008).
- G. Henkelman, B. P. Uberuaga, H. Jónsson, "A climbing image nudged elastic band method for finding saddle points and minimum energy paths," *J. Chem. Phys.* **113**, 9901 (2000).
- G. Henkelman, H. Jónsson, "Improved tangent estimate in the nudged elastic band method…," *J. Chem. Phys.* **113**, 9978 (2000).
- H. Jónsson, G. Mills, K. W. Jacobsen, "Nudged Elastic Band Method for Finding Minimum Energy Paths of Transitions," in *Classical and Quantum Dynamics in Condensed Phase Simulations* (World Scientific, 1998), p. 385.

**Dimer method:**
- P. Xiao, D. Sheppard, J. Rogal, G. Henkelman, "Solid-state dimer method for calculating solid-solid phase transitions," *J. Chem. Phys.* **140**, 174104 (2014).
- J. Kästner, P. Sherwood, "Superlinearly converging dimer method for transition state search," *J. Chem. Phys.* **128**, 014106 (2008).
- A. Heyden, A. T. Bell, F. J. Keil, "Efficient methods for finding transition states in chemical reactions…," *J. Chem. Phys.* **123**, 224101 (2005).
- G. Henkelman, H. Jónsson, "A dimer method for finding saddle points on high dimensional potential surfaces using only first derivatives," *J. Chem. Phys.* **111**, 7010 (1999).

**Adaptive kinetic Monte Carlo:**
- L. Xu, G. Henkelman, "Adaptive kinetic Monte Carlo for first-principles accelerated dynamics," *J. Chem. Phys.* **129**, 114104 (2008).
- G. Henkelman, H. Jónsson, "Long time scale kinetic Monte Carlo simulations without lattice approximation and predefined event table," *J. Chem. Phys.* **115**, 9657 (2001).

**Comparison of saddle-point-finding methods:**
- R. A. Olsen, G. J. Kroes, G. Henkelman, A. Arnaldsson, H. Jónsson, "Comparison of methods for finding saddle points without knowledge of the final states," *J. Chem. Phys.* **121**, 9776 (2004).
- G. Henkelman, G. Jóhannesson, H. Jónsson, "Methods for Finding Saddle Points and Minimum Energy Paths," in *Progress on Theoretical Chemistry and Physics* (Kluwer, 2000), pp. 269–300.
