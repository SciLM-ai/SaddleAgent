# Example: a CI-NEB that won't launch cleanly

A small, **illustrative** CI-NEB case (a single adatom hopping across a toy
5-atom Cu(100) cell). The geometry is synthetic — it exists only to exercise the
agent and the prechecks, not to represent a real reaction. No `POTCAR` is
included (VASP pseudopotentials are licensed); the agent does not need it to
diagnose the setup.

## Layout
```
INCAR          # CI-NEB deck (IBRION=3, POTIM=0, IOPT=1, LCLIMB, IMAGES=4)
KPOINTS        # Gamma-only
00/POSCAR      # initial endpoint   (H at x=0.25)
01/POSCAR      # image
02/POSCAR      # image  (near the barrier top, z bumped up)
03/POSCAR      # image
04/POSCAR      # final endpoint     (H at x=0.75)
```

## The planted problem
`INCAR` sets `IMAGES = 4`, but the band is built with directories `00`–`04` —
that is **3** intermediate images (`01`, `02`, `03`) between two endpoints
(`00`, `04`). VASP will not agree with itself about how many images exist, so the
band never starts the way you expect. The `neb_dir_layout` precheck surfaces this
mismatch as a raw fact; the agent should read it, confirm it against the
directories, and tell you the fix (set `IMAGES = 3`, or add a fourth image so the
band runs `00`–`05`).

## Try it
```bash
../../saddleagent -d . -q "My CI-NEB won't start correctly. I set up the band and
launched VASP but it complains / behaves as if the image count is wrong. What did
I get wrong?"
```
