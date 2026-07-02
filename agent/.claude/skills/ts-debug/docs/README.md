# VASP / VTST / ASE Reference Docs

Compact, accurate Markdown reference for a domain-specialized computational-chemistry agent doing VASP transition-state searches (NEB, dimer, Lanczos), vibrational/rate analysis, and troubleshooting. Each file is a self-contained quick-reference card; everything is grep-friendly and cross-linked.

## Layout
```
docs/
  README.md            ← this index
  vasp/                ← VASP INCAR-tag / file reference cards (from the VASP Wiki)
  vtst/                ← VTST Tools methods + every helper script (from the VTST docs + source)
  ase/                 ← ASE NEB / Dimer / VASP-calculator reference (from ase-lib.org)
```

## vtst/ — Transition State Tools
Methods are selected by the INCAR tag **`ICHAIN`**; the saddle-search methods run on `IBRION=3`, `POTIM=0` with a VTST force-based optimizer (`IOPT`).

| File | What |
|---|---|
| [vtst/overview.md](vtst/overview.md) | Method selector (`ICHAIN`), workflow, references. |
| [vtst/neb.md](vtst/neb.md) | Nudged elastic band — MEP/saddle between known endpoints. INCAR: `IMAGES`, `SPRING`, `LCLIMB`, `LNEBCELL`. |
| [vtst/dimer.md](vtst/dimer.md) | Dimer min-mode saddle search (one structure + MODECAR). INCAR: `DdR`, `DRotMax`, `DFNMin/Max`; DIMCAR columns. |
| [vtst/lanczos.md](vtst/lanczos.md) | Lanczos min-mode saddle search. INCAR: `SLTOL`, `Sdr`, `SNL`. |
| [vtst/optimizers.md](vtst/optimizers.md) | Force-based optimizers (`IOPT` = LBFGS/CG/QM/SD/FIRE/ML) and their parameters. |
| [vtst/dynmat.md](vtst/dynmat.md) | Dynamical matrix — vibrational frequencies & Vineyard rate prefactor. |
| [vtst/scripts.md](vtst/scripts.md) | **All 128 `.pl`/`.py` helper scripts** documented from source (options, logic, inputs, outputs). |

## vasp/ — INCAR tags & files
- **Electronic:** [encut](vasp/encut.md) · [ediff](vasp/ediff.md) · [algo](vasp/algo.md) · [prec](vasp/prec.md) · [ismear](vasp/ismear.md) · [sigma](vasp/sigma.md) · [nelm](vasp/nelm.md) · [nelmin](vasp/nelmin.md) · [lreal](vasp/lreal.md)
- **Ionic / relaxation:** [ibrion](vasp/ibrion.md) · [nsw](vasp/nsw.md) · [ediffg](vasp/ediffg.md) · [isif](vasp/isif.md) · [potim](vasp/potim.md) · [nfree](vasp/nfree.md)
- **Spin & magnetism:** [ispin](vasp/ispin.md) · [magmom](vasp/magmom.md)
- **Startup / restart / symmetry:** [istart](vasp/istart.md) · [icharg](vasp/icharg.md) · [isym](vasp/isym.md)
- **Output / dispersion / parallel:** [lorbit](vasp/lorbit.md) · [ivdw](vasp/ivdw.md) · [ncore](vasp/ncore.md) · [npar](vasp/npar.md)
- **Files:** [incar](vasp/incar.md) · [potcar](vasp/potcar.md)

## ase/ — Atomic Simulation Environment
- [ase/neb.md](ase/neb.md) — `ase.mep.neb.NEB`, interpolation/IDPP, DyNEB, NEBTools, AutoNEB.
- [ase/dimer.md](ase/dimer.md) — `DimerControl` / `MinModeAtoms` / `MinModeTranslate`.
- [ase/vasp_calculator.md](ase/vasp_calculator.md) — the `Vasp` calculator (keywords, `xc`, setups, k-points, LDA+U, restart).

## Common workflows (quick map)

**NEB saddle search** → build band `nebmake.pl A/POSCAR B/POSCAR n`; INCAR `ICHAIN=0, IMAGES=n, IBRION=3, POTIM=0, IOPT=1/2, LCLIMB=.TRUE., EDIFFG=-0.03`; post-process `nebresults.pl`. See [vtst/neb.md](vtst/neb.md).

**Dimer refine** → from a stopped NEB, `neb2dim.pl`; INCAR `ICHAIN=2, IBRION=3, POTIM=0, IOPT=2, EDIFF=1E-7`; watch `DIMCAR`. See [vtst/dimer.md](vtst/dimer.md).

**Rate prefactor** → `dymseldsp.pl`/`dymselsph.pl` → `DISPLACECAR`; INCAR `ICHAIN=1, IBRION=3, POTIM=0, NSW=DOF+1, EDIFF=1E-8`; `dymmatrix.pl` then `dymprefactor.pl`. See [vtst/dynmat.md](vtst/dynmat.md).

## Provenance
- `vasp/` — converted from the [VASP Wiki](https://www.vasp.at/wiki/) INCAR-tag pages.
- `vtst/` — method pages converted from the VTST Tools HTML docs (`theory.cm.utexas.edu/vtsttools`); `scripts.md` read directly from the `vtstscripts` source (`/opt/ohpc/pub/libs/vtstscripts/1040`).
- `ase/` — converted from [ase-lib.org](https://ase-lib.org/).
