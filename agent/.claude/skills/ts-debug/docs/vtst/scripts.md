# VTST Scripts Reference

Source-verified documentation of every Perl (`.pl`) and Python (`.py`) script in the VTST Tools script bundle (`vtstscripts/1040`). Each entry was read from the actual source. Use this as the lookup table when an agent needs to set up or post-process a VASP transition-state calculation.

> Companion method pages: [neb.md](neb.md) · [dimer.md](dimer.md) · [lanczos.md](lanczos.md) · [optimizers.md](optimizers.md) · [dynmat.md](dynmat.md) · [overview.md](overview.md)

## Conventions shared across scripts

**Run layout.** NEB and dynamical-matrix runs use two-digit image directories `00, 01, … NN`. For NEB, `00` and `NN` are the fixed endpoints and the interior dirs are the moving images. Most analysis scripts auto-discover these by globbing `[0-9][0-9]`.

**Shared Perl modules** (used, not documented separately):
- `Vasp.pm` — the workhorse: `read_poscar`/`write_poscar`, `read_othercar`/`write_othercar` (MODECAR/DISPLACECAR-style files), `dirkar`/`kardir` (fractional↔Cartesian), `set_bc` (periodic wrap, governed by env `VTST_BC`), `pbc`/`pbc_difference`/`pbc_difference_ws` (minimum image; the `_ws` variant is a more accurate Wigner–Seitz search), `dist`, `magnitude`, `volume`, `inverse`, `dot_product`.
- `Options.pm` — command-line option parsing (e.g. `-h` help).
- `Math::Matrix`, `Math::MatrixReal`, `Math::Approx` — linear algebra (eigen-decomposition, pseudo-inverse) and least-squares fitting.
- `Fortran::Format` — Fortran-style fixed-width output (used by `chgsumf.pl`).
- `kdbutil.pm` — kinetic-database helpers (`kdbHome`, `getProcessDirs`, `loadXYZ2CAR`, `stdatStatus`, …).

**Python scripts** import the bundled **`aselite.py`** (a minimal, self-contained ASE: `read_vasp`/`write_vasp`, `read_con`/`write_con`, `read_xyz`/`write_xyz`, `read_any`, `read_vasp_out`, plus a small `NEB`/`interpolate`). A few scripts (`kdbquery.py`, `kdbinsert.py`, `nebag.py`, `nebconstrain.py`, `nebinterp.py`, `kdbquerymovie` movie I/O) require the **full ASE** (and `nebinterp.py` also SciPy/NumPy).

**Environment variables.** `VTST_BC` selects the boundary-condition mode used by `set_bc`. `VTST_ZIP` is the (de)compressor for `OUTCAR`/`XDATCAR` (default `gzip`); many analysis scripts transparently gunzip `OUTCAR.gz`/`.bz2` and re-zip afterward.

**Units.** Energy = eV, distance/displacement = Å, force = eV/Å, frequency = cm⁻¹ (conversion factor `521.47` = √(eV/(Å²·amu))→cm⁻¹), angle = degrees. **Atom indices are 1-based in the Perl scripts and 0-based in the Python (ASE) scripts.**

---

## NEB — setup & analysis

Build a band with `nebmake.pl` (linear) or `nebmake.py` (IDPP), run VASP in the image dirs, then post-process the whole run at once with `nebresults.pl`. To converge a saddle further, hand off to a dimer/Lanczos run with `neb2dim.pl`/`neb2lan.pl`.

### nebmake.pl
- **Purpose:** Core NEB band builder — creates numbered image directories with a linear interpolation between two endpoint POSCARs.
- **Usage:** `nebmake.pl <POSCAR_initial> <POSCAR_final> <num_intermediate_images>`
- **Arguments:**
  - `POSCAR_initial`, `POSCAR_final` — the two endpoint structures.
  - `num_intermediate_images` — images between the endpoints; total = this + 2, capped at <100.
- **Reads:** the two endpoint POSCAR/CONTCAR files (via `read_poscar`, which also returns vasp4/vasp5 type).
- **Writes:** image dirs `00, 01, …, NN`, each with an interpolated `POSCAR` (endpoints in `00` and the last dir). Prints a reminder to put the endpoint OUTCARs in `00` and the last dir.
- **Logic:** Checks both files share atom counts/types, computes the PBC-aware difference (`pbc_difference`), and steps linearly in Cartesian space by `diff/(nim-1)` per image. If the lattice constant or basis vectors differ it warns and switches to a `dyn_cell` mode that also interpolates the lattice. Pure linear (no IDPP).
- **Notes:** The interpolation engine invoked by `nebdouble.py`/`nebinsert.py`. For IDPP use `nebmake.py`. Minor variable-name typos in the atom-count checks, but the per-type check is enforced.

### nebmake.py
- **Purpose:** Python/ASE NEB band builder using IDPP (image-dependent pair potential) interpolation by default.
- **Usage:** `nebmake.py POSCAR1 POSCAR2 num_images [-NOIDPP]`
- **Arguments:**
  - `POSCAR1`, `POSCAR2` — endpoint structures.
  - `num_images` — number of intermediate images.
  - `-NOIDPP` — use plain linear interpolation (with minimum image) instead of IDPP.
- **Reads:** the two endpoint POSCARs via bundled `aselite.read_vasp`.
- **Writes:** image dirs `00..NN` each with a `POSCAR`; prints a reminder about endpoint OUTCARs.
- **Logic:** Builds an ASE `NEB` from initial + copies + final, then `neb.interpolate('idpp', mic=True)` (or `interpolate(mic=True)` with `-NOIDPP`) and writes each image. IDPP refines the linear guess to keep pairwise distances physical.
- **Notes:** Differs from `nebmake.pl` chiefly by offering IDPP; `.pl` is linear-only. Accepts 3 or 4 args.

### nebbarrier.pl
- **Purpose:** Builds the NEB minimum-energy-path data file (energy and parallel force vs reaction coordinate) from each image's OUTCAR, with handling for solid-state NEB and endpoint tangents.
- **Usage:** `nebbarrier.pl [-alt_dist] [dir1 dir2 ...]` (run in NEB root; auto-discovers dirs if none listed)
- **Arguments:**
  - `-alt_dist` — compute inter-image distance by projecting displacement onto the average force direction (via `diffcon.pl`+`nebforces.pl`) instead of plain RMS distance.
  - `dir...` — explicit image dirs; else globs/sorts two-digit dirs.
- **Reads:** `OUTCAR` from each image dir (greps `energy  w`, `NEB:`/`NEBCELL: projections`, `LNEBCELL`, `NIONS`, `TOTAL-FORCE`, `NEBCELL: distance`); `CONTCAR`/`POSCAR` from adjacent dirs for distances/tangents.
- **Writes:** `neb.dat` (`index cum_dist rel_energy force dirname`); also `nebss.dat` (per-atom-normalized) when solid-state NEB is detected. Prints raw per-image distances.
- **Logic:** Energies referenced to image-00. Distances default to `dist.pl` RMS (or force-projected with `-alt_dist`); ssNEB uses VASP's `NEBCELL: distance`. Endpoint forces are computed as a local tangent force via `nebforces.pl`; interior forces come from the OUTCAR projections.
- **Notes:** Detects ssNEB via `LNEBCELL` in `01/OUTCAR`. The core engine behind `nebspline.pl`/`nebresults.pl`.

### nebbarrierdist.pl
- **Purpose:** Extracts the energy-vs-cumulative-distance profile (with parallel force) using VASP's own reported NEB distances.
- **Usage:** `nebbarrierdist.pl [dir1 dir2 ...]` (run in NEB root; auto-discovers if no args)
- **Arguments:** `dir...` — explicit image dirs, else globs/sorts two-digit dirs.
- **Reads:** `OUTCAR` in each image dir; greps `energy  w`, `NEB: distance`, `NEB: projections`.
- **Writes:** stdout only — `index  cumulative_distance  rel_energy  force  dirname` per image.
- **Logic:** Last energy per image minus image-00; accumulates VASP-reported `NEB: distance` into the reaction coordinate; force = last `NEB: projections`. eV, Å.
- **Notes:** Unlike `nebbarrier.pl`, writes no file, has no spline/ssNEB/`-alt_dist` handling, and trusts VASP's printed distances. Dies if an OUTCAR is missing.

### nebef.pl
- **Purpose:** Prints a quick per-image force/energy summary table.
- **Usage:** `nebef.pl` (no args; scans `NN/OUTCAR`)
- **Arguments:** None.
- **Reads:** `OUTCAR` in each two-digit image dir (last `energy  without` and last `max at` lines).
- **Writes:** stdout — `index  force  energy  rel_energy` per image.
- **Logic:** Final total energy + final max force per image, energies referenced to the first image. eV, eV/Å.
- **Notes:** Pure text parser. Used by `nebresults.pl` (→ `nebef.dat`). `nebefs.pl` is the solid-state/extended variant.

### nebefs.pl
- **Purpose:** Per-image table of force, stress, volume, magnetization, and relative energy (for cell-relaxing/ssNEB jobs).
- **Usage:** `nebefs.pl` (no args; scans `NN/OUTCAR`)
- **Arguments:** None.
- **Reads:** `OUTCAR` per image — last `energy  without`, `max at` (force), `Stress total and`, `volume`, `number of electron` (magnetization).
- **Writes:** stdout — header + `Image Force Stress Volume Magnet RelEnergy` per image.
- **Logic:** Like `nebef.pl` plus stress, cell volume, and total magnetization.
- **Notes:** Fixed-column text parser (relies on OUTCAR column positions). Used by `nebresults.pl` (→ `nebefs.dat`) when `nebss.dat` exists.

### nebforces.pl
- **Purpose:** Computes the force projected onto the local tangent between two configurations — the parallel (NEB) force for one image; used for endpoint tangents.
- **Usage:** `nebforces.pl <file1> <file2> <OUTCAR>`
- **Arguments:**
  - `file1`, `file2` — the two structures whose difference (file1−file2) defines the tangent.
  - `OUTCAR` — whose final-step forces are projected.
- **Reads:** the two POSCAR/CONTCAR files and the OUTCAR (`TOTAL-FORCE` block of the last step).
- **Writes:** stdout — a single number, the tangent-projected force (eV/Å).
- **Logic:** Builds the PBC-aware difference (`pbc_difference`), normalizes to the unit tangent, reads last-step forces, zeroes non-`T` selective-dynamics components, returns force·tangent.
- **Notes:** Called by `nebbarrier.pl` for endpoint forces and `-alt_dist` averaging.

### nebresults.pl
- **Purpose:** One-shot post-processing driver for a finished NEB — unzips OUTCARs and runs the full analysis chain (barrier, spline, force/energy table, movies, convergence plots).
- **Usage:** `nebresults.pl [-alt_dist]` (run in NEB root after `vfin.pl`)
- **Arguments:** `-alt_dist` — passed through to `nebbarrier.pl` (force-projected distance).
- **Reads:** `OUTCAR`(.gz/.bz2) in image dirs `00..NN`; later the files produced by sub-scripts (`nebss.dat`, `nebef.dat`, `exts.dat`).
- **Writes:** orchestrates `neb.dat`, `spline.dat`, `exts.dat`, `nebef.dat` (+ ssNEB `nebss.dat`/`nebspliness.dat`/`nebefs.dat`), `movie*` files, `vaspgr/` plots. Prints `nebef.dat` and `exts.dat`.
- **Logic:** Decompresses OUTCARs, then calls `nebbarrier.pl` (+`nebspline.pl`, +`nebspliness.pl` for ssNEB), `nebef.pl` (+`nebefs.pl`), `nebmovie.pl CONTCAR`, `nebjmovie.pl CONTCAR`, `nebconverge.pl`; re-zips afterward.
- **Notes:** The convenience wrapper tying the NEB-analysis scripts together. Honors `VTST_ZIP`.

### nebspline.pl
- **Purpose:** Fits a cubic spline through the NEB energy/force-vs-distance data to get a smooth MEP and locate its extrema (the barrier).
- **Usage:** `nebspline.pl [input_file] [points_per_interval]` (defaults `neb.dat`, `20`)
- **Arguments:**
  - `input_file` — MEP data `index distance energy force` (default `neb.dat`).
  - `points_per_interval` — sub-samples per image interval (default 20).
- **Reads:** `neb.dat` (or named file) from `nebbarrier.pl`.
- **Writes:** `spline.dat` (finely sampled spline) and `exts.dat` (`Extremum N found at image X with energy: Y`); renders `nebplot.gnu` via gnuplot.
- **Logic:** Per interval builds a cubic Hermite spline from endpoint energies and forces (force = −dE/dx), samples it, and solves dE/dx=0 for extrema. eV, Å, eV/Å.
- **Notes:** Pure Perl; needs gnuplot + `nebplot.gnu`. `exts.dat` is what `neb2dim.pl`/`neb2lan.pl`/`nebresults.pl` consume.

### nebspliness.pl
- **Purpose:** Solid-state-NEB variant of `nebspline.pl` — same cubic-spline MEP fit/extrema on per-atom-normalized ssNEB data.
- **Usage:** `nebspliness.pl [input_file] [points_per_interval]` (defaults `nebss.dat`, `20`)
- **Arguments:** `input_file` (default `nebss.dat`), `points_per_interval` (default 20).
- **Reads:** `nebss.dat` (or named).
- **Writes:** `spliness.dat` and `extsss.dat`; renders `nebplotss.gnu`.
- **Logic:** Identical math to `nebspline.pl` on the solid-state (per-atom-scaled) data.
- **Notes:** Invoked by `nebresults.pl` only when `nebss.dat` exists. Differs only in filenames and the gnuplot template.

### nebconverge.pl
- **Purpose:** Per-image force/energy convergence plots (EPS) across a NEB run.
- **Usage:** `nebconverge.pl [dir1 dir2 ...]` (run in NEB root; auto-discovers if no args)
- **Arguments:** `dir...` — explicit dirs, else globs two-digit dirs.
- **Reads:** `OUTCAR`(.gz/.bz2) in each interior image dir (`energy  w` and `FORCES: m` per ionic step).
- **Writes:** `vaspgr/` with `vaspoutN.eps` per interior image; a temporary `fe.dat` in each dir.
- **Logic:** Pairs each step's max force with its energy (referenced to step-0), renders with gnuplot (`vef.gnu`). Re-zips OUTCARs it decompressed.
- **Notes:** Source comment says it may be retired. Called by `nebresults.pl`. Needs gnuplot + `vef.gnu`; honors `VTST_ZIP`.

### nebavoid.pl
- **Purpose:** Pushes apart atom pairs that ended up too close after NEB interpolation, relaxing each interior image under a pairwise repulsive potential.
- **Usage:** `nebavoid.pl <distance> [orthogonal_flag]`
- **Arguments:**
  - `distance` — minimum allowed interatomic distance in Å (recommended ~0.1); dies if absent.
  - `orthogonal_flag` (default 0) — nonzero uses the fast orthogonal-box minimum-image path.
- **Reads:** `POSCAR` in each interior two-digit image dir (endpoints skipped).
- **Writes:** per interior image, renames the original to `POSCAR_orig` and writes a new relaxed `POSCAR`; prints per-step progress.
- **Logic:** Capped steepest descent (ε=0.1, max step 0.2 Å, ≤100000 steps): for every pair within cutoff applies a linear repulsive force (slope −0.3), respecting frozen (`F`) flags. Å.
- **Notes:** May disturb equal image spacing (by design). Uses `Vasp.pm`.

### nebfreeze.pl
- **Purpose:** Freezes one chosen atom (selective-dynamics `F F F`) across a set of POSCARs and shifts each structure so that atom sits at a common reference position.
- **Usage:** `nebfreeze.pl <atom_index> <POSCAR1> [POSCAR2 ...]`
- **Arguments:**
  - `atom_index` (1-based) — the atom to freeze and use as the alignment reference.
  - `POSCAR...` — files modified in place; the first also provides the reference coords/header.
- **Reads:** each listed POSCAR.
- **Writes:** overwrites each POSCAR with all atoms rigidly shifted by the chosen atom's displacement and that atom set to `F F F`. Prints reference coords and per-file displacement.
- **Logic:** Computes the PBC-wrapped displacement of the reference atom in each file relative to the first file and subtracts it from every atom, pinning that atom across the band. Fractional coords.
- **Notes:** Operates on POSCARs given as args (not by image-dir discovery). Uses `Vasp.pm`.

### nebconstrain.py
- **Purpose:** Copies selective-dynamics constraints from a reference POSCAR onto a contiguous range of NEB image POSCARs.
- **Usage:** `nebconstrain.py <reference_POSCAR> <startimg> <endimg>`
- **Arguments:**
  - `reference_POSCAR` — POSCAR whose ASE constraints are the template.
  - `startimg`, `endimg` — inclusive image-index range (single digits auto-zero-padded).
- **Reads:** the reference POSCAR and `NN/POSCAR` for each image in range.
- **Writes:** overwrites `NN/POSCAR` for each image with the applied constraints.
- **Logic:** Reads the reference constraints via ASE and `set_constraint` on each image before re-writing. 0-based atom indices.
- **Notes:** Requires ASE. The header advertises richer modes (unconstrain/exclusive) but that parsing is commented out; as-written it only *adds* constraints over `POSCAR startimg endimg`.

### nebdouble.py
- **Purpose:** Doubles the number of images by inserting an interpolated midpoint between every existing adjacent pair.
- **Usage:** `nebdouble.py` (no args; operates on two-digit image dirs)
- **Arguments:** None.
- **Reads:** `POSCAR` from each two-digit image dir; invokes `nebmake.pl` for interpolation.
- **Writes:** renames existing dirs to even indices and creates new odd-index dirs with interpolated `POSCAR` midpoints.
- **Logic:** Renames each dir to `2*index` (reverse order to avoid clobbering), then runs `nebmake.pl <left> <right> 1` per gap and moves the result into the odd midpoint dir.
- **Notes:** Needs `nebmake.pl` in PATH. Aborts on >44 input images or if a target dir exists; warns on non-contiguous input.

### nebinsert.py
- **Purpose:** Inserts one new interpolated image at a given position, renumbering higher images upward.
- **Usage:** `nebinsert.py <img>` (e.g. `nebinsert.py 04`)
- **Arguments:** `img` — insertion index; dirs ≥ this are bumped +1 and a midpoint is created between `img-1` and the old `img`.
- **Reads:** `POSCAR` from the flanking dirs; runs `nebmake.pl`.
- **Writes:** renames higher dirs (+1) and creates the new midpoint dir with an interpolated `POSCAR`.
- **Logic:** Renames in reverse those ≥ insertion point, then `nebmake.pl <left> <right> 1` for the midpoint.
- **Notes:** Needs `nebmake.pl`. Counterpart to `nebdouble.py` (single insertion vs global doubling).

### nebinterp.py
- **Purpose:** Python/ASE library (plus a runnable `__main__` demo) for spline-interpolating a NEB band — including magnetic moments — onto a new number of images.
- **Usage:** `nebinterp.py` (no CLI args; the `__main__` block hard-codes parameters). Primarily intended to be imported.
- **Arguments:** None on the CLI. In `__main__`: `num_new_images=5`, `use_image_distance_in_spline=True`, spline `kind='cubic'`.
- **Reads:** `NN/CONTCAR` (geometry) and `NN/OUTCAR` (magnetic moments) for each image; auto-detects image count.
- **Writes:** `interpolated_images/NN/POSCAR` plus per-image `NN/MAGMOM` (a `MAGMOM = …` INCAR line).
- **Logic:** Accumulates minimum-image (`find_mic`) displacements into continuous per-atom paths, parameterizes by index or cumulative RMS distance, builds per-coordinate `scipy.interp1d` splines (+ a MAGMOM spline), and evaluates at the new image count.
- **Notes:** Requires ASE + SciPy + NumPy. Has a latent bug (references undefined `atoms` for `natoms` in `interpolate_images`), so the bare demo would fail at that line.

### nebrestore.py
- **Purpose:** Restores image POSCARs from a previous run directory (`rundir/NN/POSCAR` → `NN/POSCAR`).
- **Usage:** `nebrestore.py <rundirectory> <imgstart> <imgend>`
- **Arguments:** `rundirectory` — source run dir; `imgstart`,`imgend` — inclusive range (auto-zero-padded).
- **Reads:** `rundir/NN/POSCAR` for each image in range.
- **Writes:** copies each into the current `NN/`, overwriting; prints a status line.
- **Logic:** Validates the dirs exist, then `shutil.copy`s each POSCAR. No interpolation.
- **Notes:** The two `isinstance(...,int)` checks are no-ops (CLI args are strings). Pure file-copy restart helper.

### nebag.py
- **Purpose:** Builds an ASE trajectory of all NEB images and opens it in the interactive ASE viewer.
- **Usage:** `nebag.py <mode>` — `0` = visualize POSCARs, `1` = visualize CONTCARs for interior images.
- **Arguments:** `mode` (int) — `0` reads `POSCAR`, `1` reads `CONTCAR` from interior images; endpoints always from `POSCAR`.
- **Reads:** two-digit image dirs (`^\d\d$`); `POSCAR`/`CONTCAR` per mode.
- **Writes:** `neb.traj`, then opens the ASE GUI via `view`.
- **Logic:** Discovers/sorts numeric image dirs, reads each with `ase.io.read`, appends to a Trajectory, re-reads, and launches the viewer.
- **Notes:** Requires ASE and a display. Calls an undefined `die()` on the no-dirs branch (raises `NameError`).

### neb2dim.pl
- **Purpose:** Sets up a **dimer** saddle search from a stopped NEB by building a POSCAR + MODECAR at the highest-energy region of the band.
- **Usage:** `neb2dim.pl [image_number]` (run in NEB root; if no arg, reads `exts.dat`)
- **Arguments:** `image_number` (optional) — integer image `i` to build between images `i` and `i+1` (fraction `f=0`). If omitted, picks the max-energy extremum from `exts.dat`, splitting into integer `i` and fraction `f`.
- **Reads:** `exts.dat` (no-arg case); `CONTCAR` (preferred) else `POSCAR` from dirs `i-1..i+2`; `INCAR`, `KPOINTS`, `POTCAR` (or `../POTCAR`).
- **Writes:** a `dim/` dir with `POSCAR` (interpolated to fraction `f`), `MODECAR` (dimer mode), and copied INCAR/KPOINTS/POTCAR. Prints recommended INCAR (`ICHAIN=2, IOPT=2, IBRION=3, POTIM=0.0, EDIFF=1E-7`, plus `DdR`/`DRotMax`/`DFNMax`/`DFNMin`).
- **Logic:** `posinterp.pl` interpolates the dimer center; the mode is built by `modemake.pl` (two normalized difference modes 02 and 13), blended `m=(1-f)*mode02+f*mode13` and renormalized. Distances via `dist.pl`.
- **Notes:** Depends on `posinterp.pl`, `modemake.pl`, `dist.pl`, `Vasp.pm`. <99 images. Companion: `neb2lan.pl`.

### neb2lan.pl
- **Purpose:** Sets up a **Lanczos** saddle search from a stopped NEB, producing POSCAR + MODECAR at the highest-energy region.
- **Usage:** `neb2lan.pl [image_number]` (run in NEB root; if no arg, reads `exts.dat`)
- **Arguments:** `image_number` (optional) — integer image `i` (`f=0`); else picks the max-energy extremum from `exts.dat`.
- **Reads:** `exts.dat` (no-arg case); `POSCAR` from dirs `i` and `i+1`; `INCAR`, `KPOINTS`, `POTCAR` (or `../POTCAR`).
- **Writes:** a `lan/` dir with `POSCAR`, `MODECAR`, and copied INCAR/KPOINTS/POTCAR. Prints recommended INCAR (`ICHAIN=3, IBRION=3, POTIM=0.0, EDIFF=1E-8`, plus `SIFCG/SMAXMOVE/STOL/SDR/SDT/SNL`).
- **Logic:** `dist.pl` gives the `i→i+1` distance; two flanking configs at `f±NdR/d12` (with `NdR=5e-3` Å) are made by `posinterp.pl`, and `modemake.pl` turns their difference into the normalized initial Lanczos mode.
- **Notes:** Unlike `neb2dim.pl`, reads only `POSCAR` and uses only images `i`/`i+1`. <99 images.

### nebjmovie.pl
- **Purpose:** Builds a single jmol-style `.vasp` movie concatenating all images, annotating each frame with its force and relative energy.
- **Usage:** `nebjmovie.pl [anything]` (no arg → POSCARs; any first arg → CONTCARs)
- **Arguments:** first arg (optional) — if present, use `CONTCAR` instead of `POSCAR`.
- **Reads:** two-digit image dirs from `00` up; `POSCAR`/`CONTCAR` plus `OUTCAR`(.gz/.bz2) for force/energy.
- **Writes:** `movie.vasp` (concatenated jvasp frames); temporary frames cleaned up.
- **Logic:** Per image, runs `pos2jvasp.pl` and `sed`-substitutes the comment with `F:<force> …E:<rel_energy>` (energy referenced to image-00).
- **Notes:** Depends on `pos2jvasp.pl`, `Vasp.pm`, `VTST_ZIP`. Called by `nebresults.pl`. Counterpart `nebmovie.pl` makes xyz/con/XDATCAR movies.

### nebmovie.pl
- **Purpose:** Builds NEB movie files (xyz and a `.con`-derived format, plus an XDATCAR movie) over all images, annotating frames with force and relative energy.
- **Usage:** `nebmovie.pl [anything]` (no arg → POSCARs; any first arg → CONTCARs)
- **Arguments:** first arg (optional) — if present, use `CONTCAR`.
- **Reads:** two-digit image dirs from `00` up; `POSCAR`/`CONTCAR` plus `OUTCAR`(.gz/.bz2).
- **Writes:** `movie` (con-format) and `movie.xyz`, plus `movie.XDATCAR`/`movie.POSCAR` — but with the default flags (`xyzflag=0`, `xdatflag=0`) the final movies are deleted (see Notes).
- **Logic:** Per image converts to `.con` (`pos2con.pl`) then xyz (`con2xyz.pl`), annotating the xyz comment with `F:<force> … E:<rel_energy>`; also assembles an XDATCAR-style movie.
- **Notes:** Both output flags default to 0, so the xyz/XDATCAR movies are unlinked at the end ("not currently using them"). Depends on `pos2con.pl`, `con2xyz.pl`, `Vasp.pm`, `VTST_ZIP`. Called by `nebresults.pl`.

---

## INS (immersed-saddle band) & solid-state NEB

The `ins*` scripts set up and analyze an **INS** run — a symmetric band of images displaced along an unstable mode away from a saddle, logged to `insout.dat`. The `ssneb*` scripts post-process a generalized **solid-state NEB** (variable cell: lattice deformation tracked alongside atomic motion).

### insmake.pl
- **Purpose:** Builds the initial symmetric set of INS image directories by stepping a saddle geometry in pairs along a normalized unstable mode.
- **Usage:** `insmake.pl <POSCAR> <MODECAR> <nim> <l>`
- **Arguments:**
  - `POSCAR` — saddle geometry to displace.
  - `MODECAR` — mode/eigenvector (one component per free DOF).
  - `nim` — number of images; must be even (else dies).
  - `l` — displacement length (Å) of the outermost image from the saddle.
- **Reads:** the POSCAR (coords, lattice, selective-dynamics flags) and MODECAR.
- **Writes:** dirs `01…nim/2`, each with a displaced `POSCAR`.
- **Logic:** Maps MODECAR components onto the free (`T`) DOF, normalizes the mode, and for `n=nim/2` steps displaces by `l*mask`, decrementing `l` each step. Coordinates wrapped by PBC.
- **Notes:** Uses `Vasp.pm`. Source caveats: it builds only the positive half-set (`nim/2` dirs), and a normalization line computes but never assigns the rescaled mask (harmless when the mode is already unit-normalized). ≤99 dirs.

### insaddimages.pl
- **Purpose:** Doubles the resolution of an existing INS image set by inserting an interpolated image between every adjacent pair and rebuilding the MODECAR.
- **Usage:** `insaddimages.pl` (no args; acts on numbered dirs `01, 02, …`)
- **Arguments:** None.
- **Reads:** `NN/POSCAR` and `NN/MODECAR`; `01/MODECAR` for the full mode.
- **Writes:** renames old `NN`→`NN_prev`; creates new `01…2*nim-1` dirs (POSCAR + MODECAR); writes `NEWMODECAR`; prints a count.
- **Logic:** Copies originals into odd slots, fills even slots by `posinterp.pl … 0.5` (midpoint), and builds a new combined MODECAR (inserted rows = 0.5 average of neighbors), renormalized by √2, written forward then mirrored.
- **Notes:** Uses `read_othercar`/`magnitude` and `posinterp.pl`. Source bug: the `$bin` path for `posinterp.pl` is unset (FindBin var is `$Bin`) and the rename line is mis-indented — both may fail at runtime. ≤99 images.

### insenergy.pl
- **Purpose:** Reports the average image potential energy plus the spring energy, the `So` value, and the lowest eigenvalue for a converged INS run.
- **Usage:** `insenergy.pl` (no args; acts on numbered dirs `01, 02, …`)
- **Arguments:** None.
- **Reads:** `01/insout.dat`(.gz) for spring/So/eigenvalue; each `NN/OUTCAR`(.gz) via `vef.pl` → `fe.dat` for image energy.
- **Writes:** stdout — per-image progress and the four summary values. Side effect: `vef.pl` creates `fe.dat` in each dir.
- **Logic:** Runs `vef.pl` per image to get the final force-extrapolated energy, averages them, and prints the average alongside spring energy, So, and lowest eigenvalue from `insout.dat`. eV.
- **Notes:** Depends on `vef.pl` and the `insout.dat` log. Dies on >99 images.

### insmovie.pl
- **Purpose:** Generates an animated `.xyz` trajectory of an INS run by assembling per-image geometries at each logged update step.
- **Usage:** `insmovie.pl` (no args; acts on numbered dirs `01, 02, …`)
- **Arguments:** None.
- **Reads:** each `NN/POSCAR` (first frame) and `NN/XDATCAR` via `xdat2pos.pl` (later frames); `01/insout.dat` for update-step indices; optional `mep.xyz` overlay.
- **Writes:** per-image/temp `.xyz`/`.con`; per-frame `timeframe_K.xyz`; final concatenated `ins_series.xyz`.
- **Logic:** Builds the first frame from each image's POSCAR (`pos2con.pl`+`con2xyz.pl`), then for each update step extracts the matching XDATCAR snapshot in every image and concatenates; `writeout` fixes the atom-count header (optionally adding `mep.xyz`).
- **Notes:** Depends on `pos2con.pl`, `con2xyz.pl`, `xdat2pos.pl`. ≤99 images, ≤999 timeframes.

### insplot.pl
- **Purpose:** Plots INS convergence diagnostics (energies, max force, imaginary mode, So vs force calls) from `insout.dat` via gnuplot.
- **Usage:** `insplot.pl` (no args; reads `insout.dat`)
- **Arguments:** None.
- **Reads:** `insout.dat` (greps `ut`, excludes `itr`).
- **Writes:** temporary table file (deleted); `res_ins.eps` (multi-page PostScript via `insplot.gnu`).
- **Logic:** Filters `insout.dat` into a temp table and runs `gnuplot insplot.gnu`, which plots force calls (col 2) against potential energy, spring energy, |Fmax|, imaginary mode, and So (cols 3–7).
- **Notes:** Needs gnuplot + sibling `insplot.gnu`. `insplot.py` is the Python equivalent.

### insplot.py
- **Purpose:** Python equivalent of `insplot.pl` — same INS convergence plots from `insout.dat` via gnuplot.
- **Usage:** `insplot.py` (no args; reads `insout.dat`)
- **Arguments:** None.
- **Reads:** `insout.dat` (same filtering as the `.pl`).
- **Writes:** temporary table (deleted); `res_ins.eps` via `insplot.gnu`.
- **Logic:** Locates its own dir, shells out to build the filtered table, runs `gnuplot <vtst>/insplot.gnu`, removes the temp. Plot content defined by `insplot.gnu`.
- **Notes:** Pure shell-out wrapper (no Python plotting libs); identical behavior to the Perl version.

### ssnebpp.pl
- **Purpose:** Solid-state NEB post-processor — projects each image's atomic-basis and cell-deformation DOF onto user-defined reaction coordinates and writes normalized coordinate values per image.
- **Usage:** `ssnebpp.pl [PPinput.txt]`
- **Arguments:** `[filename]` — projection-definition file; defaults to `PPinput.txt`.
- **Reads:** the input file (`basis:`/`cell:` sections defining projection directions); first/last image `POSCAR` for the baseline; every `NN/CONTCAR` (preferred) or `NN/POSCAR` for per-image lattice + coords.
- **Writes:** `ssnebproj.dat` — CSV `image,<basisvars…>,<cellvars…>` with begin-to-end normalized values per image.
- **Logic:** Computes each image's deformation gradient `F` (xx,yy,zz,xy,yz,xz) vs the initial cell; de-wraps PBC jumps (>0.5 shifted by ±1); uses `Math::Matrix` pseudo-inverses to project basis and `F` onto the chosen variables, rescaled so image-0 = 0 and the last = 1.
- **Notes:** Requires `Math::Matrix`; handles VASP6 two-line element headers. Variable-cell aware (lattice tracked alongside atoms). Coordinates dimensionless. Companion: `ssnebsugproj.pl`.

### ssnebsugproj.pl
- **Purpose:** Suggests solid-state NEB projection (collective-variable) vectors by detecting where the path changes direction and averaging per-segment displacements.
- **Usage:** `ssnebsugproj.pl [angle_threshold]`
- **Arguments:** `[angle_threshold]` — degrees above which consecutive segments count as a direction change (default `45`).
- **Reads:** each `NN/CONTCAR` (preferred) or `NN/POSCAR` for atomic basis coords (handles VASP6 element line).
- **Writes:** opens `ssneb.sproj` but only prints to stdout — per-segment cosines, change-point indices, suggested-variable count, and the averaged vectors. (Nothing is written into `ssneb.sproj`.)
- **Logic:** Builds per-image basis lists, de-wraps PBC jumps, forms consecutive displacement vectors, marks a change point wherever the cosine between successive displacements drops below threshold, and averages displacements within each segment into one suggested vector.
- **Notes:** Self-contained vector helpers (no `Math::Matrix`). Output is meant to seed `ssnebpp.pl`'s `basis:`/`cell:` definitions. Fractional units. Note: results go to stdout, not the opened file.

### splitmovie.pl
- **Purpose:** Splits a concatenated `movie.xyz` trajectory into several smaller `.xyz` files (a workaround for viewers like Jmol).
- **Usage:** `splitmovie.pl` (no CLI args; prompts on stdin for the number of pieces; acts on `movie.xyz`/`XDATCAR`)
- **Arguments:** None on the CLI; reads the piece count from stdin.
- **Reads:** `movie.xyz` (regenerated from `XDATCAR` via `xdat2xyz.pl` if missing/older); `head -1` for the atom count.
- **Writes:** `csplit` output files (`xx00`, `xx01`, …); prints per-file step counts.
- **Logic:** Computes step count from line count, divides into `np` pieces (`base=int(nsteps/np)`, last piece absorbs the remainder), builds frame-boundary offsets, and calls `csplit`.
- **Notes:** Depends on `xdat2xyz.pl` and system `csplit`. Source caveat: uses `$Bin` without `use FindBin`, so regeneration only works if `movie.xyz` already exists.

---

## Dimer & mode-vector tools

A dimer run needs a `POSCAR` (center) and a `MODECAR` (initial lowest-curvature mode, a Cartesian unit vector). `diminit.pl` builds them by random displacement; `modemake.pl` builds a MODECAR from two structures; `dimmins.pl` steps off a converged saddle to the two connected minima. See [dimer.md](dimer.md).

### diminit.pl
- **Purpose:** Generates one or many single-image dimer starting points (POSCAR center + MODECAR mode) by applying Gaussian random displacements to selected (typically under-coordinated) atoms of an input POSCAR.
- **Usage:** `diminit.pl DIRECTORY|NUMBER [DisplaceAlgo DisplaceRange Rcut MaxCord POSCAR DISPLACECAR_sp ORTHOGONAL]`
- **Arguments:**
  - `DIRECTORY|NUMBER` — a pure integer N creates N dimers in `pr0001…prNNNN`; otherwise a single output directory name.
  - `DisplaceAlgo` (default `0`) — atom selection: `0` lowest-coordinated atom(s), `1` atoms with coordination < `MaxCord`, `2` most-undercoordinated per surface island, `3` atoms < `MaxCord` per island; anything else → random.
  - `DisplaceRange` (default `0.01` Å) — neighbor cutoff for grouping co-displaced atoms around the center.
  - `Rcut` (default `0.01` Å) — coordination-counting cutoff for the neighbor list.
  - `MaxCord` (default `8`) — coordination threshold for algos 1 and 3.
  - `POSCAR` (default `POSCAR`) — input center geometry.
  - `DISPLACECAR_sp` (default `DISPLACECAR_sp`) — per-atom Gaussian-width file selecting which atoms may move.
  - `ORTHOGONAL` (default `0`) — true uses the fast orthogonal-cell minimum image (read from `$ARGV[7]`; a likely off-by-one in the guard).
- **Reads:** `POSCAR`, `DISPLACECAR_sp` (3 sigmas + atom index per line), cached `neighborlist.dat`/`islands.dat` if the stored `Rcut` matches; also `KPOINTS`/`POTCAR`/optional `INCAR`/`akmc.sub` for copying.
- **Writes:** per dimer, a folder with `POSCAR` (displaced center) and `MODECAR` (normalized displacement direction), plus copied KPOINTS/POTCAR/INCAR. Caches `neighborlist.dat`/`islands.dat`; prints neighbor info.
- **Logic:** Builds coordination/neighbor lists (minimum image), selects a center atom by the chosen algorithm, perturbs it and close neighbors with per-component Gaussian noise (`sigma*gauss`), then a steepest-descent `spring_relaxation` (linear repulsion, 0.1 Å cutoff) pushes apart atoms that ended too close. MODECAR = normalized (perturbed − original) minimum-image displacement.
- **Notes:** Uses `Vasp.pm` (`gauss`, `dirkar`/`kardir`, `set_bc`); self-contained neighbor/island helpers. Dimer separation `DdR` is an INCAR tag, not set here. Companions: `dimmins.pl`, `dimmode.pl`.

### dimmins.pl
- **Purpose:** From a converged dimer (POSCAR center + MODECAR axis), generates the two minimization starting images displaced ±`distance` along the mode axis to find the two connected minima.
- **Usage:** `dimmins.pl [POSCAR MODECAR distance replace]`
- **Arguments:**
  - `POSCAR` (default `POSCAR`), `MODECAR` (default `MODECAR`) — read only when ≥2 args are given.
  - `distance` (default `0.1` Å) — displacement magnitude along the mode for each image.
  - `replace` (default empty) — `min1`/`min2` rewrites only that one image in-place; otherwise builds the full `mins/` tree.
- **Reads:** `POSCAR`, `MODECAR` (equal atom counts); for copying: `KPOINTS`, `POTCAR`, `INCAR_min` (preferred) or `INCAR`, optional `akmc_min.sub`.
- **Writes:** `mins/min1/POSCAR` and `mins/min2/POSCAR` (the two displaced images) with copied KPOINTS/POTCAR/INCAR. Replace mode overwrites only the named one.
- **Logic:** `partial = distance/|mode|`; `image1 = center + partial*mode`, `image2 = center − partial*mode`; both wrapped by PBC. The two images sit `distance` Å either side of the saddle so relaxations roll to the adjacent minima.
- **Notes:** Uses `Vasp.pm`. Aborts if `mins/` exists (full mode). Passing only `distance` is not honored unless the two filenames are also given.

### dimmode.pl
- **Purpose:** Builds an `.xyz` movie visualizing the dimer's lowest (imaginary) mode by oscillating the center geometry along the mode over one period. (Self-identifies internally as `dimcheck.pl`.)
- **Usage:** `dimmode.pl [CENTCAR NEWMODECAR numimages dist]` (or `--help`)
- **Arguments:**
  - `CENTCAR` (default `CENTCAR`) — geometry to animate.
  - `NEWMODECAR` (default `NEWMODECAR`) — mode vector.
  - `numimages` (default `32`) — frames over one full sine period.
  - `dist` (default `0.5` Å) — peak displacement amplitude.
- **Reads:** `CENTCAR` and `NEWMODECAR` (equal atom counts); `head -1` of the geometry file for element symbols.
- **Writes:** `dimmode.xyz` — a multi-frame XYZ trajectory.
- **Logic:** Per frame applies `image = center + dist*sin(2π·n/numimages)*mode`, wrapped by PBC; warns if the mode norm deviates from 1 by >0.001 (dies on a zero mode).
- **Notes:** Uses `Vasp.pm`. Element symbols come from the geometry file's first line, so that line must list atom types in order.

### dimplot.pl
- **Purpose:** Extracts one final data point per ionic step from a dimer run's `DIMCAR` and plots force and energy convergence via gnuplot.
- **Usage:** `dimplot.pl` (no args; acts on `DIMCAR`)
- **Arguments:** None.
- **Reads:** `DIMCAR` (first line is the header; remaining are per-rotation records, first field = ionic step).
- **Writes:** `dimer.dat` (last record per step) and `dimer.eps` (via the bundled gnuplot script).
- **Logic:** Keeps the last line per step number (steps must start at 1 and increase), then runs `gnuplot dimplot.gnu` to plot max force (col 2, log y) and energy (col 4) vs step (col 1).
- **Notes:** Needs sibling `dimplot.gnu` and gnuplot. DIMCAR columns: 1=step, 2=max force, 4=energy, 5=curvature.

### modemake.pl
- **Purpose:** Builds a normalized MODECAR (initial lowest-mode guess) as the PBC-corrected Cartesian difference between two POSCAR geometries.
- **Usage:** `modemake.pl POSCAR1 POSCAR2`
- **Arguments:** `POSCAR1` (also supplies lattice/layout), `POSCAR2` — same total atom count.
- **Reads:** the two POSCAR-type files (parses scale, lattice, VASP4/5, selective-dynamics to find the coord offset).
- **Writes:** `MODECAR` — the normalized Cartesian difference, one `%20.10E` triplet per atom.
- **Logic:** Per atom: fractional difference `POSCAR1 − POSCAR2`, minimum-image-wrapped into [−0.5, 0.5], transformed to Cartesian via the (scaled) lattice; the full vector is normalized to unit length, pointing from POSCAR2 toward POSCAR1.
- **Notes:** Parses POSCARs by hand (no `Vasp.pm`). Assumes both share POSCAR1's lattice/ordering. Companions: `modemag.pl` (check norm), `modedot.pl` (compare modes).

### modedot.pl
- **Purpose:** Reports the dot-product overlap (cosine, in [−1, 1]) of two MODECAR vectors after individually normalizing each. (Self-identifies as `dotmode.pl`.)
- **Usage:** `modedot.pl MODECAR1 MODECAR2`
- **Arguments:** `MODECAR1`, `MODECAR2` — the two mode files.
- **Reads:** the two files; numeric tokens are those containing a decimal point.
- **Writes:** stdout — the overlap value.
- **Logic:** Loads each file's decimals into a flat vector, normalizes each to unit length, prints `Σ a[i]*b[i]` (the cosine overlap; dimensionless).
- **Notes:** No `Vasp.pm`. Integer-only entries are ignored by the decimal filter. Length mismatch only warns.

### modemag.pl
- **Purpose:** Reports the Euclidean magnitude (L2 norm) of a single MODECAR vector.
- **Usage:** `modemag.pl MODECAR`
- **Arguments:** `MODECAR` — the mode file to measure.
- **Reads:** the file; decimal-valued tokens across all lines.
- **Writes:** stdout — the magnitude.
- **Logic:** Prints `sqrt(Σ x²)` over the full Cartesian mode; should be ≈1 for a normalized MODECAR.
- **Notes:** No `Vasp.pm`. Integer-only tokens are skipped. Companion to `modedot.pl`/`modemake.pl`.

---

## Dynamical matrix & vibrations

Workflow (see [dynmat.md](dynmat.md)): build a `DISPLACECAR` (which atoms/DOF to displace, ~0.001 Å) with `dymselsph.pl`/`dymseldsp.pl`; run VASP (`ICHAIN=1`, `NSW=DOF+1`); build and diagonalize the mass-weighted Hessian with **`dymmatrix.pl`/`.py`** → frequencies (cm⁻¹) + modes; then get the Vineyard rate prefactor with `dymprefactor.pl`. `vef.pl`/`vef.py` extract per-step force/energy convergence; `vfin.pl` finalizes a run directory.

### dymanalyze.pl
- **Purpose:** Diagnose finite-difference convergence of dynamical-matrix elements by fitting a linear force-constant across several displacement magnitudes and reporting per-displacement fitting error.
- **Usage:** `dymanalyze.pl <flag> <modevalue> <displacement 1> <matrix 1> <displacement 2> <matrix 2> ...` (≥6 args)
- **Arguments:**
  - `flag` — if >0, fit a line through the first `flag` (displacement, matrix) pairs and compare to every point; if `0`, fit each single point and track how the force constant changes.
  - `modevalue` — only elements whose fitted slope magnitude exceeds this are printed/tallied.
  - repeated `displacement matrix` pairs — a displacement magnitude and its matrix file (each element ×displacement on read).
- **Reads:** each `matrix N` file (whitespace rows). No OUTCAR.
- **Writes:** stdout — fitted slope per (row,col), fitted/data values with percent error per displacement, then average error/std/point count for elements above `modevalue`.
- **Logic:** Per element, fits a degree-1 polynomial through the origin and the displacement points (`Math::Approx`), taking the slope as the force constant; percent error vs data (or vs the multi-point fit when `flag==0`). Units inherited from the input matrices.
- **Notes:** Depends on `Math::Approx`. Order hard-coded to 1. Companion to `dymfit.pl`.

### dymcmpdisp.pl
- **Purpose:** Compare two DISPLACECARs and emit a third containing only the DOF that are NOT common to both.
- **Usage:** `dymcmpdisp.pl <DISPLACECAR 1> <DISPLACECAR 2>` (exactly 2 args)
- **Arguments:** `DISPLACECAR 1`, `DISPLACECAR 2`.
- **Reads:** both via `read_othercar` (matching atom counts).
- **Writes:** stdout — one line per atom: three displacement components + 1-based atom index.
- **Logic:** Per atom/component, outputs the differing nonzero value (preferring file 1, falling back to file 2) where the two differ, else 0 — the set-symmetric difference of displaced DOF.
- **Notes:** Output is stdout (redirect to capture). Used when extending a dynmat calc with additional DOF.

### dymeffbar.pl
- **Purpose:** Over a temperature range, compute the classical, zero-point-corrected, and quasi-quantum (Wigner) effective activation energies from minimum- and saddle-point frequency files.
- **Usage:** `dymeffbar.pl <Ti> <Tf> <dV> <minimum freq file> <saddle freq file>` (≥5 args)
- **Arguments:**
  - `Ti`, `Tf` — initial/final temperatures (used as `1/T`; 100 points).
  - `dV` — classical barrier (eV).
  - `f1`, `f2` — frequency files (ω² per line) for minimum (no negative modes) and saddle (≤1 negative mode).
- **Reads:** the two ω² files (`sqrt` → ω).
- **Writes:** `eff_ea.dat` — columns `1/T`, `T*1000`, `dV`, `dVz` (ZPE), `dVwig` (quasi-quantum).
- **Logic:** ZPE offset `0.5·ħ·(Σω_saddle − Σω_min)` gives `dVz`. The quasi-quantum barrier uses the quantum partition-function ratio `dVwig = dV − kB·T·ln(a/b)`, products of `sinh(ħω/(2kB)·T)/(ħω/(2kB)·T)`. `kB=8.61738573e-5`, `ħ=6.46538e-2`; eV.
- **Notes:** Saddle imaginary mode assumed first and skipped. Companion to `dymrate.pl` (adds rates + tunneling). Input ω² matches `eigs.dat`.

### dymextract.pl
- **Purpose:** Extract from a force-vs-displacement matrix only the rows/cols whose displacements are in DISPLACECAR 1 but not DISPLACECAR 2. (Author flags it as of uncertain use.)
- **Usage:** `dymextract.pl <DISPLACECAR 1> <DISPLACECAR 2> <matrix for 1>` (exactly 3 args)
- **Arguments:** `DISPLACECAR 1` (reference), `DISPLACECAR 2` (DOF to remove), `matrix for 1`.
- **Reads:** both DISPLACECARs (`read_othercar`); the matrix file.
- **Writes:** stdout — the reduced matrix (`%9.4f`), skipping erased rows/cols.
- **Logic:** Where DISPLACECAR 2 is zero at a DOF that DISPLACECAR 1 displaces, that row/col is marked with sentinel `9999` and suppressed on output, yielding the submatrix of DOF unique to DISPLACECAR 1.
- **Notes:** Sentinel `9999` could collide with large legitimate values. Uses `Vasp.pm`.

### dymfit.pl
- **Purpose:** Fit two or more force-vs-displacement matrices together with a linear least-squares polynomial to produce a single force-constant (Hessian) matrix.
- **Usage:** `dymfit.pl <order> <displacement 1> <matrix 1> <displacement 2> <matrix 2> ...` (≥5 args)
- **Arguments:** `order` (polynomial degree), repeated `displacement matrix` pairs.
- **Reads:** each matrix file (each element ×displacement on read).
- **Writes:** stdout — the fitted matrix (`%18.10f`), each element the first-order coefficient.
- **Logic:** Per element, fits `{0→0, disp_i→value_i}` with `Math::Approx` of the given order and extracts the slope through the origin as the force constant.
- **Notes:** Depends on `Math::Approx`/`Vasp.pm`. `dymanalyze.pl` is the diagnostic counterpart.

### dymgetfreq.pl
- **Purpose:** Extract vibrational frequencies (cm⁻¹) from a VASP OUTCAR's `THz` eigenfrequency lines (e.g. an `IBRION=5/6` run) into `freq.dat`.
- **Usage:** `dymgetfreq.pl <OUTCAR>` (0 or 1 arg; defaults `OUTCAR`)
- **Arguments:** `OUTCAR` (optional; default `OUTCAR`).
- **Reads:** OUTCAR (`grep THz`).
- **Writes:** `freq.dat` — `%12.6f cm^{-1} … <flag>` per mode (flag `0`=real, `1`=imaginary); prints the count.
- **Logic:** Splits each `THz` line; if the second token is `f` (real) takes cm⁻¹ from field 7 (flag 0); else (imaginary `f/i`) field 6 (flag 1). Already cm⁻¹ (no conversion).
- **Notes:** Field offsets depend on VASP's OUTCAR layout. Produces the `freq.dat` consumed by `dymprefactor.pl`/`dymspect.pl`.

### dymmatrix.pl
- **Purpose:** Build the mass-weighted Hessian (dynamical matrix) from OUTCAR force differences against DISPLACECAR displacements, diagonalize it, and write eigenvalues, frequencies (cm⁻¹), and eigenvectors.
- **Usage:** `dymmatrix.pl` (uses `DISPLACECAR`+`OUTCAR`) | `dymmatrix.pl <DISPLACECAR> <OUTCAR>` | `dymmatrix.pl <num DISPLACECARS> <DISPLACECAR 1>… <OUTCAR 1>…`
- **Arguments:** no args → `DISPLACECAR`+`OUTCAR`; 2 args → those files; ≥3 → a count then that many DISPLACECARs then the OUTCAR list (multi-directory mode).
- **Reads:** OUTCAR(s) — masses (`POMASS`/`ZVAL`), `ions per type`, and per-step force blocks split on `HIPREC TOTAL-FORCE (eV/A)`; DISPLACECAR(s) via `read_othercar`.
- **Writes:** `freq.mat` (symmetrized mass-weighted matrix), `eigs.dat` (ω² eigenvalues), `freq.dat` (frequencies + 0/1 flag), `modes.dat` (eigenvectors as columns); echoes frequencies.
- **Logic:** Hessian element = −(force difference)/displacement, mass-weighted by `1/√(mass_k·mass_i)`, symmetrized, diagonalized (`Math::MatrixReal->sym_diagonalize`). ω² sorted ascending; frequency = `√(|ω²|)*521.47` cm⁻¹ (flag 1 for negative/imaginary). Factor `521.47` = √(eV/(Å²·amu))→cm⁻¹.
- **Notes:** Reads the **VTST high-precision** `HIPREC TOTAL-FORCE` lines, not the standard `TOTAL-FORCE (eV/Angst)`. Requires `Math::MatrixReal`/`Vasp.pm`. Perl counterpart of `dymmatrix.py`.

### dymmatrix.py
- **Purpose:** Python/NumPy equivalent of `dymmatrix.pl`, additionally emitting force constants, effective masses, and amu-scaled modes.
- **Usage:** `dymmatrix.py` (defaults `DISPLACECAR`+`OUTCAR`) | `dymmatrix.py [DISPLACECAR] [OUTCAR]` | `dymmatrix.py #DISPLACECAR D1 … O1 …` | `dymmatrix.py -h`
- **Arguments:** as `.pl`; `-h` prints usage.
- **Reads:** DISPLACECAR(s) via `numpy.loadtxt` (first 3 cols); OUTCAR(s) via `aselite.read_vasp_out` (image 0 = reference). Masses from the ASE atoms.
- **Writes:** `freq.mat`, `eigs.dat`, `freq.dat`, `modes.dat`, `modes_sqrt_amu.dat` (eigenvectors ÷√mass), `force_constants.dat`, `effective_masses.dat` (= force_constant/ω²); echoes frequencies.
- **Logic:** `dymmat[i] = −(f1−f0)/displacement` over nonzero-displacement indices, mass-weighted, symmetrized, diagonalized with `numpy.linalg.eigh`. Frequencies `√(|ω²|)*521.47` cm⁻¹. An unweighted Hessian gives force constants; effective mass = force_constant/ω².
- **Notes:** Requires NumPy + `aselite.py`; `numpy.seterr(all='raise')`. Errors if (#OUTCAR images − 1) ≠ #nonzero displacements. Adds force-constant/effective-mass outputs vs the `.pl`.

### dymmodes2xyz.pl
- **Purpose:** Generate per-mode `.xyz` movies animating each normal mode along its eigenvector over one period.
- **Usage:** `dymmodes2xyz.pl [POSCAR] [DISPLACECAR] [modes.dat] [moviedir] [freq.dat] [numimages] [dist]` (all optional)
- **Arguments:** `POSCAR` (default `CONTCAR`), `DISPLACECAR` (default `DISPLACECAR`), `modes.dat` (default `modes.dat`), `moviedir` (default `.`), `freq.dat` (default `freq.dat`), `numimages` (default `32`), `dist` (default `0.5` Å).
- **Reads:** POSCAR/CONTCAR; `DISPLACECAR` (maps nonzero DOF to atom/component); `modes.dat` (column eigenvectors); `freq.dat` (title text).
- **Writes:** `mode001.xyz`, `mode002.xyz`, … in `moviedir`; per-mode progress.
- **Logic:** Frame `n` displaces by `dist*sin(2π·n/numimages)` along the eigenvector mapped onto its atoms, PBC-applied; checks each eigenvector norm ≈1. `dist` in Å.
- **Notes:** Uses `Vasp.pm`. Consumes `modes.dat`/`freq.dat` from `dymmatrix.pl`/`.py`.

### dymprefactor.pl
- **Purpose:** Compute the harmonic (Vineyard) rate prefactor from minimum- and saddle-point frequency files.
- **Usage:** `dymprefactor.pl <minimum freq.dat> <transition freq.dat>` (exactly 2 args)
- **Arguments:** `minimum freq.dat` (0 imaginary modes), `transition freq.dat` (exactly 1 imaginary mode).
- **Reads:** two `freq.dat` files (field 0 = frequency, field 3 = imaginary flag); equal line counts.
- **Writes:** stdout — the prefactor in cm⁻¹ and THz.
- **Logic:** Vineyard formula `prefactor = (∏ ω_min,i / ω_saddle,i) × ω_imag_saddle`, product over all listed frequencies; converted to THz via `×c/1e12` (`c=2.99792458e10 cm/s`).
- **Notes:** Dies unless the minimum has 0 and the saddle has exactly 1 imaginary mode. Consumes `dymmatrix`/`dymgetfreq` output.

### dymrate.pl
- **Purpose:** Over a temperature range, compute classical / ZPE / quasi-quantum (Wigner) / tunneling-corrected effective barriers AND the corresponding rate constants.
- **Usage:** `dymrate.pl <Ti> <Tf> <dV(eV)> <minimum freq file> <saddle freq file>` (≥5 args)
- **Arguments:** `Ti`,`Tf` (over `1/T`, 100 points), `dV` (eV), `f1` (minimum ω², no negatives), `f2` (saddle ω², ≤1 negative).
- **Reads:** two ω² files (`sqrt` → ω).
- **Writes:** `eff_ea.dat` (`1/T,T*1000,dV,dVz,dVwig,dVtun`) and `rate.dat` (`1/T,T*1000,k_cl,k_clz,k_wig,k_tun`).
- **Logic:** Classical prefactor `vcl = ∏(ω_min/ω_saddle)·ω_min·w2v` (`w2v=15633304363477.891` converts √(eV/Å²amu)→s⁻¹). `dVz=dV+0.5·ħ·(Σω_saddle−Σω_min)`; Wigner barrier from the quantum partition ratio; tunneling adds `ln(xtun/sin(xtun))` with `xtun=|ħ·√|ω₀²|/(2kB)·T|`. Rates `vcl·exp(−barrier·T/kB)`.
- **Notes:** Above the crossover temperature the tunneling rate is disabled via a huge sentinel. Superset of `dymeffbar.pl`.

### dymreorder.pl
- **Purpose:** Reorder the rows/cols of a force-vs-displacement matrix so its DOF ordering matches a second (target) DISPLACECAR set.
- **Usage:** `dymreorder.pl <num ref DISPLACECARS> <ref DISPLACECARs…> <num new DISPLACECARS> <new DISPLACECARs…> <matrix>` (≥4 args)
- **Arguments:** a count + that many reference DISPLACECARs, a count + that many new DISPLACECARs, then the `matrix` (in reference order).
- **Reads:** both DISPLACECAR sets (`read_othercar`); the matrix file. Counts and matrix dimension must agree.
- **Writes:** stdout — the reordered matrix (`%9.4f`).
- **Logic:** Builds both orderings; for each new DOF pair locates the matching reference indices (by atom + component) and copies `newmatrix[b1][b2]=matrix[a1][a2]` — a permutation of the Hessian.
- **Notes:** Uses `Vasp.pm`. Useful when combining matrices computed with differently ordered DISPLACECARs.

### dymseldisp.pl
- **Purpose:** Build a DISPLACECAR selecting the N atoms that moved most between two POSCARs (minimum vs transition state).
- **Usage:** `dymseldisp.pl <POSCAR 1> <POSCAR 2> <number of atoms to include> <displacement>` (exactly 4 args)
- **Arguments:** `POSCAR 1`, `POSCAR 2`; `number of atoms` (DOF = 3×this); `displacement` (Å step written into each selected component).
- **Reads:** both POSCARs (`read_poscar`).
- **Writes:** `DISPLACECAR` — per-atom line: three components (displacement for selected, else 0), 1-based index, displacement magnitude; selected atoms echoed.
- **Logic:** Per-atom minimum-image displacement (`pbc`→`dirkar`→`magnitude`) between the two POSCARs, sorted descending; top N marked in all three directions. Å.
- **Notes:** Functionally identical to `dymseldsp.pl` (only the die-message name differs). Complements `dymselsph.pl`.

### dymseldsp.pl
- **Purpose:** Build a DISPLACECAR selecting the N most-displaced atoms between two POSCARs.
- **Usage:** `dymseldsp.pl <POSCAR 1> <POSCAR 2> <number of atoms to include> <displacement>` (exactly 4 args)
- **Arguments:** as `dymseldisp.pl`.
- **Reads:** both POSCARs.
- **Writes:** `DISPLACECAR` (same format as `dymseldisp.pl`).
- **Logic:** Byte-for-byte the same algorithm as `dymseldisp.pl` — a duplicate/alias.
- **Notes:** Uses `Vasp.pm`.

### dymselsph.pl
- **Purpose:** Build a DISPLACECAR selecting all atoms within a radius of one or two central atoms (localized dynamical matrix).
- **Usage:** `dymselsph.pl <POSCAR> <central atom> <radius> <displacement>` or `dymselsph.pl <POSCAR> <central atom1> <central atom2> <radius> <displacement>` (4 or 5 args)
- **Arguments:** `POSCAR`; one center (`central atom`) or two (midpoint); `radius` (Å); `displacement` (Å).
- **Reads:** POSCAR (`read_poscar`).
- **Writes:** `DISPLACECAR` — per-atom: three components (displacement if within radius, else 0), 1-based index, distance to center; prints center + selected count.
- **Logic:** Minimum-image distance (`pbc`→`dirkar`) to the center (a single atom's position, or the PBC-wrapped midpoint of two), selecting atoms within `radius` and displacing them in all three directions.
- **Notes:** Distance-based alternative to the displacement-difference selectors.

### dymspect_ir.pl
- **Purpose:** Produce an intensity-weighted (IR) vibrational spectrum by Gaussian-broadening frequency/intensity pairs.
- **Usage:** `dymspect_ir.pl <results.txt> <sigma> <minimum frequency> <maximum frequency>` (all optional)
- **Arguments:** `results.txt` (default `results.txt`), `sigma` (default `5` cm⁻¹), `x_min` (default `0`), `x_max` (default `3500`).
- **Reads:** the results file (field 1 = frequency, field 2 = intensity).
- **Writes:** `spect.dat` — integer frequency + summed broadened amplitude.
- **Logic:** Adds `intensity·exp(−0.5·((j−freq)/sigma)²)` to every integer grid point from `x_min` to `x_max`. cm⁻¹.
- **Notes:** `if/elsif` parsing means only one optional override applies per run. Differs from `dymspect.pl` by weighting each Gaussian by an intensity column.

### dymspect.pl
- **Purpose:** Produce an (unweighted) vibrational density-of-modes spectrum by Gaussian-broadening the real frequencies in a `freq.dat`.
- **Usage:** `dymspect.pl <freq.dat> <sigma> <minimum frequency> <maximum frequency>` (all optional)
- **Arguments:** `freq.dat` (default `freq.dat`), `sigma` (default `5`), `x_min` (default `0`), `x_max` (default `3500`).
- **Reads:** `freq.dat` (field 0 = frequency, field 3 = imaginary flag; flagged lines skipped).
- **Writes:** `spect.dat` — integer frequency + summed amplitude; prints the imaginary-mode count.
- **Logic:** Each real frequency contributes a unit-height Gaussian summed across the grid; imaginary modes excluded. cm⁻¹.
- **Notes:** Same `if/elsif` quirk as `dymspect_ir.pl`. Uniform weights (no intensity column).

### dymzpbar.pl
- **Purpose:** Compute the zero-point energy from the positive-curvature (real) modes given an ω² eigenvalue file.
- **Usage:** `dymzpbar.pl <omega^2 file>` (exactly 1 arg)
- **Arguments:** `omega^2 file` — one ω² per line (e.g. `eigs.dat`).
- **Reads:** the ω² file.
- **Writes:** stdout — the negative-eigenvalue count and the ZPE (eV).
- **Logic:** ZPE = `0.5·ħ·Σ√(ω²)` over positive eigenvalues; negatives counted and excluded. `ħ=6.46538e-2`.
- **Notes:** Input is ω² (matches `eigs.dat`), not cm⁻¹ `freq.dat`.

### vef.pl
- **Purpose:** Extract the max-atom force and energy at each ionic step from an OUTCAR into `fe.dat` and optionally plot the convergence.
- **Usage:** `vef.pl [plotflag]` (acts on `OUTCAR`)
- **Arguments:** `plotflag` (default `1`) — nonzero with >1 step runs gnuplot on `vef.gnu`.
- **Reads:** `OUTCAR` (auto-gunzips `.gz`/`.bz2`) — `FORCES: max atom, RMS` (force) and `energy without entropy` (energy).
- **Writes:** `fe.dat` — `step, max force, energy, energy−energy₀`; echoes to stdout; optional gnuplot figure.
- **Logic:** Pairs each step's max force with its energy (relative to step 0). eV, eV/Å. Re-zips the OUTCAR afterward using `VTST_ZIP` (default gzip).
- **Notes:** "vef" = VASP energy/force per step — a general convergence tool used across the NEB/dynmat workflows. Python counterpart `vef.py`.

### vef.py
- **Purpose:** Python/ASE equivalent of `vef.pl`.
- **Usage:** `vef.py` (acts on `OUTCAR`; `-h` prints usage)
- **Arguments:** `-h` (no plotflag).
- **Reads:** `OUTCAR` via `aselite.read_vasp_out` (each image = one step).
- **Writes:** `fe.dat` (step, max force, energy, energy−energy₀); echoes; runs `gnuplot vef.gnu` when >1 step.
- **Logic:** Per step takes `get_potential_energy()` and `get_max_atom_force()`, energy relative to the first step. eV, eV/Å.
- **Notes:** Requires `aselite.py` (+ gnuplot/`vef.gnu` for the plot). No plot toggle; does not handle gzipped OUTCARs.

### vfin.pl
- **Purpose:** Finalize/clean a VASP run directory — detect the method from the OUTCAR's `ICHAIN` and dispatch to the right clean-up script, copy outputs to a new dir, and stage CONTCAR→POSCAR for a restart.
- **Usage:** `vfin.pl [Output Directory]` (`-h` for help; the output dir must not already exist)
- **Arguments:** `[Output Directory]` — destination for copied results; `-h` help.
- **Reads:** `OUTCAR` (or `01/OUTCAR`) — `head -1000 | grep -i ICHAIN`; checks for `00/`, `MODECAR`, `01/`, `02/` to disambiguate.
- **Writes:** creates the output dir and delegates copying to the chosen `*clean.sh`; those scripts also move CONTCAR over POSCAR in the run dir.
- **Logic:** Maps `ICHAIN`: `0`→`nebclean.sh` (if `00/` exists) else `vclean.sh`; `1`→`dymclean.sh`; `2`→`dimclean.sh`/`dimclean2.sh`; `3`→`lanclean.sh`; `4`→`insclean.sh`. The cleaners copy POSCAR/CONTCAR/OUTCAR/INCAR/KPOINTS/XDATCAR/CHGCAR/WAVECAR (OUTCAR/XDATCAR zipped).
- **Notes:** Depends on `Options.pm` and the `*clean.sh` scripts. Dies if the output dir exists or no OUTCAR is found. Run before `nebresults.pl`.

---

## Charge density & electronic structure

CHGCAR/CHG/PARCHG/LOCPOT files store a 3-D grid after a POSCAR-style header. These scripts do grid arithmetic (sum/diff/split/average), interpolate the grid value at ion positions, convert to Gaussian `.cube`, and pull electronic-structure quantities (gap, HOMO/LUMO, ESP) from OUTCAR/EIGENVAL.

> **Shared latent bug** in `chg2cube.pl`, `chgvalue.pl`, `cubevalue.pl`: the cell-volume "expansion by minors" uses an out-of-range index `$basis->[0][3]` (should be `[0][2]`). The volume is only actually used for output in `chg2cube.pl` (CHGCAR/PARCHG density normalization), where it is a real concern.

### chgsum.pl
- **Purpose:** Add two CHGCAR files with optional scaling factors (lightweight version, no Fortran::Format dependency).
- **Usage:** `chgsum.pl <CHGCAR1> <CHGCAR2> [fact1] [fact2]`
- **Arguments:** `CHGCAR1`, `CHGCAR2` (≥2 args); `fact1` (default `1.0`), `fact2` (default `1.0`).
- **Reads:** two CHGCARs (vasp4/vasp5 auto-detected); dies if grid-point counts differ.
- **Writes:** `CHGCAR_sum` — file1's header + `fact1*rho1 + fact2*rho2`, 5 values/line.
- **Logic:** Density read 5 values/line and combined linearly. Header from file1; trailing augmentation data NOT copied.
- **Notes:** For subtraction use `fact2 = -1`. See `chgsumf.pl` (Fortran-formatted, preserves augmentation charges), `chgdiff.pl`.

### chgsumf.pl
- **Purpose:** Add two CHGCARs with optional scaling factors, with strict Fortran-formatted output and preserved trailing augmentation data.
- **Usage:** `chgsumf.pl <CHGCAR1> <CHGCAR2> [fact1] [fact2]`
- **Arguments:** as `chgsum.pl`.
- **Reads:** two CHGCARs (vasp4/vasp5 auto-detected); dies on grid mismatch.
- **Writes:** `CHGCAR_sum` — header + `fact1*rho1+fact2*rho2` formatted `5(1X,E17.11)` via `Fortran::Format`, then file1's trailing lines (augmentation charges) verbatim.
- **Logic:** Linear combine, 5 values/line; progress in 10% steps. Augmentation data after the grid survives.
- **Notes:** Requires the `Fortran::Format` module (the plain `5E18.11` form mishandled negative densities). Use `fact2=-1` to subtract.

### chgdiff.pl
- **Purpose:** Subtract one CHGCAR's density from another, grid-point by grid-point.
- **Usage:** `chgdiff.pl <reference CHGCAR> <CHGCAR2>`
- **Arguments:** reference (file1) and CHGCAR2 (file2); exactly 2 args.
- **Reads:** two CHGCARs (copies file1's header; vasp4/vasp5 detected); dies on grid mismatch.
- **Writes:** `CHGCAR_diff` — file1's header + `file2 − file1` per point, 5 values/line.
- **Logic:** Reads 5 values/line from both and writes the difference. **Note the stored difference is (second − first)** despite the "reference" label. Augmentation data not copied.

### chgsplit.pl
- **Purpose:** Split a spin-polarized CHGCAR into its total-density and magnetization-density components.
- **Usage:** `chgsplit.pl <CHGCAR>`
- **Arguments:** `CHGCAR` — spin-polarized (contains total up+down and magnetization up−down blocks); ≥1 arg.
- **Reads:** one CHGCAR (fixed 6-line header assumed).
- **Writes:** `CHGCAR_tot` (up+down) and `CHGCAR_mag` (up−down), both reusing file1's header.
- **Logic:** Writes the first block as `CHGCAR_tot`, scans to the repeated grid line marking the second block, verifies the point count, and writes it as `CHGCAR_mag`. 5 values/line.
- **Notes:** Assumes a standard 6-line POSCAR header (no vasp4/vasp5 auto-detect). Relies on the magnetization grid line being textually identical to the total one.

### chgparavg.pl
- **Purpose:** Average two CHGCAR/PARCHG files — both the grid data and the ionic coordinates — for periodic, orthogonal cells.
- **Usage:** `chgparavg.pl <reference CHGCAR> <CHGCAR2>`
- **Arguments:** reference (file1), CHGCAR2 (file2); exactly 2 args.
- **Reads:** two CHGCAR/PARCHG files (cell lengths from the basis diagonal); dies on grid mismatch.
- **Writes:** `PARCHG_avg` — averaged header (averaged coords) + averaged density, 10 values/line.
- **Logic:** Coordinates averaged with minimum image (`delta=r2−r1` wrapped to (−0.5,0.5], take `r1+delta/2`). Density read 10 values/line and averaged. Prints per-atom `delta`.
- **Notes:** Warns that periodic coordinate averaging assumes an orthogonal cell. Reads 10 values/line (PARCHG layout), unlike chgsum/chgdiff (5/line).

### chg2cube.pl
- **Purpose:** Convert a CHGCAR/LOCPOT/PARCHG into a Gaussian `.cube` in atomic (Bohr/Hartree) units.
- **Usage:** `chg2cube.pl <CHGCAR|LOCPOT|PARCHG> [output.cube]` (then answers interactive prompts)
- **Arguments:** input file (required); output (default `<input>.cube`). Interactive stdin: file format (`1`=CHGCAR,`2`=LOCPOT,`3`=PARCHG); then element atomic numbers (one Z per species).
- **Reads:** the chosen volumetric file (POSCAR header + FFT grid + density; comment line and vasp4/vasp5 auto-detected).
- **Writes:** a `.cube` (2 comment lines, atom count + origin, three grid-vector lines with X negated to flag Bohr, atom records in Bohr, then density in z-inner/y-middle/x-outer order, 6/line).
- **Logic:** Lengths Å→Bohr (`×1.889725992`), energies eV→Hartree (`×0.036749309`). CHGCAR/PARCHG density ÷ cell volume (VASP stores charge×volume); LOCPOT not scaled. Grid re-emitted in cube order. PARCHG read 10/line, CHGCAR/LOCPOT 5/line.
- **Notes:** Output hardcoded to Bohr/Hartree. Carries the shared `$basis->[0][3]` volume bug (real impact here).

### chgvalue.pl
- **Purpose:** Interpolate the value of a CHGCAR/LOCPOT grid at each ion position.
- **Usage:** `chgvalue.pl <LOCPOT|CHGCAR> [method]` (a 3rd arg, if present, is the output filename)
- **Arguments:** input file (required); `method` (default `1`): `1` linear, `2` quadratic, `3` cubic, `4` min-of-8; output (default `out.chempot`, only when 3+ args).
- **Reads:** one CHGCAR/LOCPOT (POSCAR header + grid + density into `rho[x][y][z]`).
- **Writes:** the output file — per-ion Cartesian coords (Å) + interpolated value (eV); echoes to stdout.
- **Logic:** Maps each ion to fractional grid indices (`xyz2grid` via inverse basis) and interpolates by the chosen method: trilinear (8 pts), quadratic (27), cubic (48), or min-of-8. No unit scaling (so raw charge×volume for a CHGCAR).
- **Notes:** Uses `Vasp.pm` `inverse`. Edge handling relies on implicit periodic wrap. Passing a `method` also requires a 3rd arg to set the output name. Carries the shared volume bug (volume unused for output here).

### cubevalue.pl
- **Purpose:** Interpolate the value of a Gaussian `.cube` grid (e.g. ESP) at each ion position, reported in Hartree/Bohr and eV/Å.
- **Usage:** `cubevalue.pl <cube file> [method]` (a 2nd arg doubles as method index AND output filename)
- **Arguments:** cube file (required); `method` (default `1`): `1` linear, `2` quadratic, `3` cubic, `4` min-of-8; if ≥2 args, `$args[1]` is also the output filename (else `out.chempot`).
- **Reads:** a `.cube` (voxel counts + basis, atom records in Bohr, density 6/line into `rho[x][y][z]`).
- **Writes:** the output file — each ion in Bohr/Hartree and in Å/eV (`×0.529177248`, `×27.2116248`); echoes to stdout.
- **Logic:** `xyz2grid` maps ion Cartesian (Bohr) to fractional voxel indices; interpolation as in `chgvalue.pl`.
- **Notes:** Uses `Vasp.pm` `inverse`. Method 4 references undefined `$fft_grid` (won't bound-check). The method value also names the output file (arg aliasing). Carries the shared volume bug (unused here).

### bandgap.pl
- **Purpose:** Compute the band gap (and direct/indirect) from OUTCAR eigenvalues/occupations, for non-spin and spin-polarized cases.
- **Usage:** `bandgap.pl cut=<occupancy>` (acts on `OUTCAR`)
- **Arguments:** `cut=<value>` (positional) — max occupancy below which a band is unoccupied (default `0.01`; `0.0` is treated as `1e-9`).
- **Reads:** `OUTCAR` (filename hardcoded) — `ISPIN`, `NBANDS`, `NKPTS`, the last `Iteration`, and the per-k eigenvalue/occupation table.
- **Writes:** stdout — ISPIN, band/k counts, the ionic step used, VBM (HOMO) and CBM (LUMO) with k-points, and the direct/indirect gap (eV).
- **Logic:** For the last step, per k-point the highest band with occupation ≥ cutoff is the HOMO, the first below is the LUMO; VBM = max HOMO over k, CBM = min LUMO over k; gap = CBM−VBM. Same k → "direct", else "indirect". ISPIN=2 processes both spin components.
- **Notes:** No `Vasp.pm`. The k-point direct/indirect comparison reuses a variable that looks like a typo (documented as-is). Usage text says default 0.1 but the code default is 0.01.

### homolumo.pl
- **Purpose:** Print, per k-point, the HOMO band/energy, LUMO band/energy, and HOMO–LUMO gap from the last spin-component-1 eigenvalue block of an OUTCAR.
- **Usage:** `homolumo.pl [OUTCAR or path]` (defaults to `OUTCAR`)
- **Arguments:** `OUTCAR` (optional positional) — file to open; defaults to `OUTCAR`.
- **Reads:** OUTCAR — `NBANDS`, the line range between the last `spin component 1` and the `soft charge-density along one line, spin component 1` markers, and each k-point's band table.
- **Writes:** stdout — `Number of Bands`, then per k-point a line with `HOMO`, its `E`, `LUMO`, its `E`, and `BandGap` (eV).
- **Logic:** Within the eigenvalue block, for each `k-point` it walks bands tracking the highest occupied band (occupation == 1.0 or > 0.5); when occupation drops it records that band as HOMO and the next as LUMO and prints `BandGap = E(HOMO) − E(LUMO_line)`. Occupation is field 3, energy field 2, band index field 1.
- **Notes:** Pure-Perl, no `Vasp.pm`. The `grep` lines hardcode the filename `OUTCAR` (only the `open` honors the argument), so run it where `OUTCAR` exists. Reports a per-k-point gap, not a single global gap (cf. `bandgap.pl`). Occupancy threshold 0.5.

### onsite.pl
- **Purpose:** Extract the per-atom, per-spin **onsite occupancy/density-matrix** diagonal (LDA+U onsite occupation matrices) from the last SCF iteration of an OUTCAR, with the sum of squares of the diagonal.
- **Usage:** `onsite.pl [OUTCAR or path]` (defaults to `OUTCAR`)
- **Arguments:** `OUTCAR` (optional positional) — file to open; defaults to `OUTCAR`.
- **Reads:** OUTCAR — the line range from the last `Iteration` to `Free energy of the ion-electron system (eV)`; within it, `atom` lines (excluding `atomic`) and `spin` blocks.
- **Writes:** stdout — per atom, its index + a field; per spin block, the spin label followed by the 5 diagonal occupation values and `total=Σ value²`.
- **Logic:** Inside the last iteration's onsite-matrix section it prints each atom header, then for each `spin` line reads the following 5 lines and emits the diagonal occupancies (`spindens[1..5]`) and their summed squares (a magnitude/polarization measure of the onsite matrix).
- **Notes:** Pure-Perl, no `Vasp.pm`. Like `homolumo.pl`, the `grep` lines hardcode `OUTCAR`. Intended for runs that print onsite occupancy matrices (LDA+U / `LORBIT` + `LDAUTYPE`). Reads only the **last** iteration's matrices.

### alcesp.pl
- **Purpose:** Extract the electrostatic potential at each ion (the "norm of the test charge") from an OUTCAR.
- **Usage:** `alcesp.pl [OUTCAR] [output]`
- **Arguments:** `OUTCAR` (default `OUTCAR`), `output` (default `esp.out`).
- **Reads:** OUTCAR — `NIONS` (to size the table) and the block after `the norm of the test charge is`.
- **Writes:** `esp.out` (or named) with per-ion potential values; echoes to stdout.
- **Logic:** Shells `grep … -A | tail | awk` to pull the potential table, reformatting every other field (the numeric potentials, dropping ion-index labels) one per line. eV (VASP convention; not converted).
- **Notes:** Relies on `grep`/`awk`/`tail` and a specific OUTCAR layout (`NIONS` field index, the marker string).

### alchardness.pl
- **Purpose:** Build and print the "alchemical hardness" matrix (symmetrized inverse interatomic-distance matrix) from a structure.
- **Usage:** `alchardness.pl [CONTCAR] [output]`
- **Arguments:** `CONTCAR` (default `CONTCAR`), `output` (default `hardness.out`).
- **Reads:** a POSCAR/CONTCAR (`read_poscar`).
- **Writes:** `hardness.out` (or named) with the N×N matrix; also to stdout.
- **Logic:** For each atom pair forms `1/√(dR²)` (inverse distance, Å⁻¹) using the minimum image (`pbc`→`dirkar`); diagonal zeroed; symmetrized `0.5*(H_ij+H_ji)` in a `Math::MatrixReal` object.
- **Notes:** Requires `Math::MatrixReal`. Off-diagonal = inverse distance between atoms; self-term zeroed.

---

## Density of states

First run `split_dos.py` to split a `DOSCAR` into a total (`DOS0`) and Fermi-shifted per-atom files (`DOS1…DOSN`); the other scripts analyze/plot those.

### split_dos.py
- **Purpose:** Split a VASP `DOSCAR` into a total-DOS file `DOS0` and one Fermi-shifted per-atom file `DOS1…DOSN`.
- **Usage:** `split_dos.py` (no args; reads `DOSCAR` and optionally `POSCAR`)
- **Arguments:** None.
- **Reads:** `DOSCAR` (atom count, NEDOS, E-Fermi, total + per-atom blocks); `POSCAR`/CONTCAR (via aselite) to annotate each `DOSi` with that atom's position.
- **Writes:** `DOS0` (total, energies shifted by −E_Fermi) and `DOS1…DOSN` (per-atom; first line a `#` comment with the atom's x,y,z). Prints atom count, NEDOS, E-Fermi, spin flag.
- **Logic:** Reads NEDOS rows for the total block, then per atom, subtracting E_Fermi from every energy. Spin detected from per-atom column count; down-spin columns negated.
- **Notes:** Requires NumPy + aselite. Outputs are the inputs to `dosanalyze.pl`/`doslplot.pl`/`dosplot.pl`. All energies are E − E_Fermi.

### dosanalyze.pl
- **Purpose:** Integrate a split-out DOS (band center, total states, standard deviation) over a chosen orbital and atom set, optionally within an energy window.
- **Usage:** `dosanalyze.pl [w=<n>] [e=<emin>,<emax>] <s|p|d|a> <atom num(s)>` (orbital defaults to `d`; atoms = single index or `lo-hi`)
- **Arguments:**
  - `w=<number>` — energy range as a number of quarter-height widths around the peak.
  - `e=<emin>,<emax>` — explicit integration window (eV); dies if emin>emax.
  - `s|p|d|a` — orbital (s, p, d, or `a`=all); default `d`.
  - `<atom num(s)>` — single index or `lo-hi`; if omitted, the `DOS0` total.
- **Reads:** per-atom `DOSi` files (or total `DOS0`); auto-detects spin/lm layout from column count.
- **Writes:** stdout — Total States, Average Energy (band center), Standard Deviation; with `w=`, also the quarter-height width and energy cutoffs.
- **Logic:** Selects DOS columns by orbital and layout (spin cases take up−down), sums over selected atoms per energy point, band center = Σ(E·DOS)/Σ(DOS), std from the second moment. Warns if a windowed band center shifts >10% from the full-range value.
- **Notes:** Energies are already Fermi-shifted by `split_dos.py`. All files must share the energy grid (dies otherwise).

### doslplot.pl
- **Purpose:** Plot the l-projected (s/p/d or all) local DOS for selected atoms via gnuplot.
- **Usage:** `doslplot.pl <s|p|d|a> <atom num(s)>` (orbital defaults to d-band; atoms = index, `lo-hi`, or omitted for all)
- **Arguments:** `s|p|d|a` (orbital; `a`=s+p+d); `<atom num(s)>` (index/range, or all).
- **Reads:** `DOS1` (to detect column count/layout) and the selected `DOSi`; references `DOS0` for the total overlay. Column count picks the routine: 4=non-polarized, 7=spin, 10/19=phase-decomposed (`LORBIT=11`).
- **Writes:** `ldosplot.gnu` (temp) and `ldosplot.eps`.
- **Logic:** Builds a gnuplot script plotting each selected `DOSi` (orbital-specific column sum) overlaid with `DOS0`, then runs gnuplot. For 10-col data, d = columns 6–10 summed; spin cases plot up−down. eV.
- **Notes:** Needs gnuplot. The `pd_plot` path leaves `ldosplot.gnu` on disk. Related: `dosplot.pl`, `dosanalyze.pl`.

### dosplot.pl
- **Purpose:** Plot the total DOS (column 2 vs energy) of one or more split DOS files via gnuplot.
- **Usage:** `dosplot.pl <DOS file> [<DOS file> ...]` (typically `DOS0`)
- **Arguments:** one or more DOS filenames; each overwrites the same gnuplot script/EPS, so the last argument's plot remains.
- **Reads:** each named DOS file (columns 1,2 = energy, total DOS).
- **Writes:** `dosplot.gnu` and `dosplot.eps`.
- **Logic:** Writes a gnuplot script (Energy [eV] vs DOS) plotting col 1 vs col 2 and runs gnuplot. No transforms.
- **Notes:** Needs gnuplot. Viewer-launch and `.gnu` cleanup are commented out, so `dosplot.gnu` is left on disk.

---

## Structure-format converters

Convert among VASP `POSCAR`/`CONTCAR`, EON `.con`, `.xyz`, `.cif`, and `XDATCAR`, and compute distance/pair-distribution analyses. The `.pl` converters route through `pos2con.pl` + `Vasp.pm`; the `.py` ones use `aselite`.

### pos2con.pl
- **Purpose:** Convert between VASP POSCAR and EON `.con` in either direction (chosen by the input filename).
- **Usage:** `pos2con.pl <POSCAR or CON file> [outfile]`
- **Arguments:** input file (`.con` in the name → `.con`→POSCAR, else POSCAR→`.con`); `outfile` (optional; default `<input>.con` or input with `.con` stripped).
- **Reads:** a POSCAR (`read_poscar`) or a `.con` (parsed manually: box lengths line 2, angles line 3, components line 6, counts line 7, coords from line 11).
- **Writes:** a `.con` (con header, box, angles, masses, Cartesian coords + frozen flag + index) or a POSCAR (`Selective dynamics`, Direct, `T T T`/`F F F`).
- **Logic:** vasp→con: `set_bc`, derive box lengths/angles, rebuild an orthogonalized lattice, `dirkar` to Cartesian; Selective `F`→con flag 1. con→vasp: rebuild basis from box+angles, invert to fractional; con flag 1→`F F F`.
- **Notes:** Uses `Vasp.pm` + `Math::Trig`. **`.con` flag convention: 1 = fixed/frozen, 0 = free.** Underlies `pos2xyz.pl`, `diffcon.pl`, and the movie scripts.

### con2xyz.pl
- **Purpose:** Convert an EON `.con` into an `.xyz`.
- **Usage:** `con2xyz.pl <file.con>`
- **Arguments:** input `.con`; output name = input with `con`→`xyz`.
- **Reads:** `.con` (component count line 6, per-component counts line 7, coords from line 9).
- **Writes:** `.xyz` (count, "Generated with con2xyz", then `element x y z`); prints output name + atom count.
- **Logic:** Walks each component, emits `natoms[type]` lines taking the first three columns as x,y,z (Cartesian, passed through unchanged).
- **Notes:** Pure text parsing (no `Vasp.pm`). The `s/con/xyz/` replaces the first "con" in the name. Counterpart `con2xyz.py`.

### con2xyz.py
- **Purpose:** Convert an EON `.con` into an `.xyz` (aselite-based).
- **Usage:** `con2xyz.py FILENAME` (or `-h`)
- **Arguments:** `FILENAME` — input `.con`.
- **Reads:** `.con` (`aselite.read_con`).
- **Writes:** `.xyz` (name = input with `con`→`xyz`; `aselite.write_xyz`).
- **Logic:** Reads into an atoms object and writes `.xyz`; coordinate handling delegated to aselite.
- **Notes:** Python-2 `print`. Functional parallel to `con2xyz.pl`.

### 2con.py
- **Purpose:** Convert a POSCAR or `.xyz` into EON `.con`.
- **Usage:** `2con.py IN OUT`
- **Arguments:** `IN` (POSCAR or `.xyz`, auto-detected), `OUT` (output `.con`).
- **Reads:** POSCAR/`.xyz` (`aselite.read_any`).
- **Writes:** `.con` named `OUT` (`aselite.write_con`).
- **Logic:** Auto-detects the input format and writes `.con`; all coordinate handling in aselite.
- **Notes:** Depends on `aselite`. Name = "[anything]-to-con".

### xyz2con.py
- **Purpose:** Convert an `.xyz` into EON `.con`, placing the structure in a cubic box of a given side.
- **Usage:** `xyz2con.py FILENAME BOXSIZE` (or `-h`)
- **Arguments:** `FILENAME` (`.xyz`), `BOXSIZE` (cubic edge `a` in Å → cell `(a,a,a)`).
- **Reads:** `.xyz` (`aselite.read_xyz`).
- **Writes:** `.con` (name = input with `xyz`→`con`; `aselite.write_con`).
- **Logic:** Shifts positions so the minimum coordinate is 0, sets a cubic cell of side `BOXSIZE`, writes `.con`. Cartesian; no wrapping beyond the shift.
- **Notes:** Python-2 `print`; needs aselite + NumPy. Inverse of `con2xyz.py`. Non-cubic cells unsupported.

### pos2xyz.pl
- **Purpose:** Convert a POSCAR into `.xyz` by chaining `pos2con.pl` then `con2xyz.pl`.
- **Usage:** `pos2xyz.pl <POSCAR>`
- **Arguments:** input POSCAR.
- **Reads:** the POSCAR (indirectly, via the called scripts).
- **Writes:** `<POSCAR>.xyz`; the intermediate `.con` is created then deleted.
- **Logic:** `pos2con.pl` → `.con`, `con2xyz.pl` → `.xyz`, then removes the `.con`. Fractional→Cartesian done by `pos2con.pl`.
- **Notes:** Needs `pos2con.pl` + `con2xyz.pl` in the same `$Bin`. Counterpart `pos2xyz.py` does it directly.

### pos2xyz.py
- **Purpose:** Convert a POSCAR into `.xyz` using aselite (no intermediate `.con`).
- **Usage:** `pos2xyz.py POSCAR` (or `-h`)
- **Arguments:** `POSCAR`.
- **Reads:** POSCAR (`aselite.read_vasp`).
- **Writes:** `<POSCAR>.xyz` (`aselite.write_xyz`).
- **Logic:** Reads the POSCAR and writes Cartesian `.xyz`; conversion in aselite.
- **Notes:** Python-2 `print`. Simpler/faster than the `.pl` wrapper (no `.con` round-trip).

### cif2pos.pl
- **Purpose:** Convert a CIF into a VASP POSCAR (fractional coordinates).
- **Usage:** `cif2pos.pl <file.cif>`
- **Arguments:** the CIF; only its basename (before the first `.`) names the output.
- **Reads:** CIF — `_cell_length_a/b/c`, `_cell_angle_*`, and atom-site lines with exactly 7 fields (element = field 1; fractional x,y,z = fields 3,4,5).
- **Writes:** a POSCAR named after the CIF basename, VASP5 with `Selective Dynamics` and all atoms `T T T`.
- **Logic:** Builds the lattice from cell lengths/angles (deg→rad) via the standard triclinic formula, groups atom symbols into type counts, writes Direct coordinates verbatim. Strips parenthetical uncertainties in cell lengths.
- **Notes:** Source note: only works for triclinic cells with 7-number atom lines. Inverse of `pos2cif.pl`.

### pos2cif.pl
- **Purpose:** Convert a VASP POSCAR into a CIF.
- **Usage:** `pos2cif.pl <POSCAR> [outfile]`
- **Arguments:** input POSCAR; `outfile` (default `<POSCAR>.cif`).
- **Reads:** POSCAR (`read_poscar`); the description line supplies element symbols.
- **Writes:** a CIF (`data_` block, cell lengths/angles, P1 symmetry, `_atom_site_*` loop with fractional coords and per-element labels).
- **Logic:** `set_bc` wraps into the cell; cell lengths = basis-vector magnitudes, angles via dot products (rad→deg). Writes fractional coords; hardcodes P1, occupancy 1.0, U_iso 0.0.
- **Notes:** Uses `Vasp.pm` + `Math::Trig`. Element symbols come from the description/element line, so a meaningful VASP5 element line is required. Inverse of `cif2pos.pl`.

### pos2pos.pl
- **Purpose:** Rewrite a POSCAR into a normalized `POSCAR.out`, optionally translating all atoms by a fractional shift.
- **Usage:** `pos2pos.pl [POSCAR] [dx dy dz]` (no filename → `POSCAR`; with 4 args, args 2–4 are the shift)
- **Arguments:** input POSCAR (default `POSCAR`); fractional `dx dy dz` shift (only when exactly 4 args; default `0 0 0`).
- **Reads:** POSCAR (detects optional `Selective dynamics`).
- **Writes:** `POSCAR.out` (description, scale, basis, counts, `Selective dynamics`, `Direct`, shifted coords with `T T T`); prints the shift.
- **Logic:** Adds the shift to each fractional coordinate and wraps into [0,1); forces all selective flags to `T T T`. No `Vasp.pm`.
- **Notes:** Assumes Direct (fractional) input. Output is always `POSCAR.out`.

### out2pos.pl
- **Purpose:** Extract every ionic step's geometry from an OUTCAR and write each as a separate POSCAR.
- **Usage:** `out2pos.pl` (no args; acts on `POSCAR` and `OUTCAR`)
- **Arguments:** None.
- **Reads:** `POSCAR` (element labels, lattice, counts, selective flags) and `OUTCAR` (each `POSITION TOTAL-FORCE` block).
- **Writes:** `p000`, `p001`, … (one per ionic step), VASP4-style Direct with the original selective flags; prints one debug line per step.
- **Logic:** Converts each block's Cartesian positions to fractional by dividing by the diagonal lattice lengths.
- **Notes:** The fractional conversion divides only by diagonal basis elements, so it is **only correct for orthogonal cells**. No `Vasp.pm`.

### pos2jvasp.pl
- **Purpose:** Convert a POSCAR/CONTCAR into a `.vasp` file for the J-VASP/J-ICE viewer.
- **Usage:** `pos2jvasp.pl <POSCAR or CONTCAR>` (exactly one arg)
- **Arguments:** input file; output = `<input>.vasp`.
- **Reads:** POSCAR/CONTCAR (auto-detects VASP4 vs VASP5).
- **Writes:** `<input>.vasp` (`NCLASS=…`/`ATOM=…` header, counts line, `Direct`, the lattice block, then `x y z #index` per atom in fractional coords).
- **Logic:** Parses symbols/counts (accounting for the VASP5 element line) and re-emits the lattice + fractional coords with a trailing `#<atom number>`.
- **Notes:** No `Vasp.pm`. Assumes Direct input (copies columns verbatim). Used by `nebjmovie.pl`.

### xdat2pos.pl
- **Purpose:** Extract selected ionic step(s) from an XDATCAR into POSCAR files, and (for a range) assemble an `.xyz` movie.
- **Usage:** `xdat2pos.pl <0> <start step> <end step>` (range) or `xdat2pos.pl <1> <step number>` (single)
- **Arguments:** mode `0` (range, needs start+end) or `1` (single step); 1-based, inclusive step indices.
- **Reads:** `POSCAR` (labels, counts, selective flags; VASP4/5 auto) and `XDATCAR` (per-step fractional blocks; stride auto-detected).
- **Writes:** `POSCAR<step>.out` per extracted step (POSCAR header + coords + original selective flags); range mode also builds `movie.xyz` (via `pos2con.pl`→`con2xyz.pl`).
- **Logic:** Computes the step's line offset (`7+(natoms+1)*(step-1)` for VASP4, `8+…` for VASP5), reads that frame, writes Direct coords. Dies if the step is out of range.
- **Notes:** Output keeps the reference POSCAR's selective flags. Related: `xdat2xyz.pl`, `xdat2vdat.pl`.

### xdat2xyz.pl
- **Purpose:** Convert a full XDATCAR trajectory into a multi-frame `movie.xyz`, annotating each frame with OUTCAR max force and energy.
- **Usage:** `xdat2xyz.pl [XDATCAR-file]` (no arg → `XDATCAR`, auto-unzipped)
- **Arguments:** XDATCAR filename (optional; default `XDATCAR`).
- **Reads:** `XDATCAR` (VASP4/5 auto), `CONTCAR` else `POSCAR` (lattice + symbols + counts), `OUTCAR` (`FORCES: max atom, RMS` and `energy without entropy` per step).
- **Writes:** `movie.xyz` — per frame: atom count, `FORCE: <max>  …  ENERGY: <E>`, then `element x y z` (Cartesian Å).
- **Logic:** Assigns element symbols from type counts, converts each frame's fractional coords to Cartesian via the cell, pairs with the per-step force/energy from OUTCAR. PBC wrapping present but commented out.
- **Notes:** Re-zips OUTCAR/XDATCAR afterward (honors `VTST_ZIP`). Related: `xdat2pos.pl`, `xdat2vdat.pl`.

### xdat2vdat.pl
- **Purpose:** Compute per-atom velocities (and per-step kinetic energy / effective temperature) from a VASP5 XDATCAR by forward finite difference, writing a `VDATCAR`.
- **Usage:** `xdat2vdat.pl [XDATCAR-file]` (no arg → `XDATCAR`, auto-unzipped)
- **Arguments:** XDATCAR filename (optional; default `XDATCAR`).
- **Reads:** `XDATCAR` (VASP5 only — header + per-step fractional blocks) and `OUTCAR` (`POMASS` per type, `POTIM` timestep; auto-unzipped).
- **Writes:** `VDATCAR` — XDATCAR header + per-atom Cartesian velocities (Å/fs) per step, with `KINETIC ENERGY (eV)` and `TEMP EFF (K)`.
- **Logic:** Fractional displacement between successive frames (PBC-wrapped ±0.5) → Cartesian → ÷`POTIM` = velocity. KE = Σ½mᵢvᵢ²; `T = 2·KE/(k_B·(3N−3))`.
- **Notes:** Dies if not VASP5. Masses from `POMASS`, timestep from `POTIM`. Hardcodes N_A, k_B, eV→J.

### pos2exafs.pl
- **Purpose:** Compute a first-nearest-neighbor distance distribution (EXAFS-style coordination histogram) from a POSCAR.
- **Usage:** `pos2exafs.pl <POSCAR> <BinSize> <outfile> <choosetype 0|1> <atomtype1> <atomtype2>` (≥3 args; all six required if `choosetype=1`)
- **Arguments:** `POSCAR`; `BinSize` (Å, default `0.05`); `outfile` (default `exafs.dat`); `choosetype` (`0`=all pairs, `1`=between two named types); `atomtype1`,`atomtype2` (1-based component indices, required when `choosetype=1`).
- **Reads:** POSCAR (`read_poscar`).
- **Writes:** `exafs.dat` (or named) — "Distribution of 1st NN:" then `distance count` rows for the first shell.
- **Logic:** Minimum-image pair distances (`pbc`→`dirkar`) binned; for each atom accumulates neighbor counts out to twice the minimum-distance bin (first shell). `choosetype=1` restricts to the two component ranges.
- **Notes:** Atom types by 1-based component index, not symbol. Related: `pos2rdf.pl`, `pos2pdf.pl`.

### pos2pdf.pl
- **Purpose:** Compute the pair-distribution function (PDF) of a POSCAR over radial bins.
- **Usage:** `pos2pdf.pl [POSCAR] [Bin Size] (Density) (Outfile)` (≥2 args; `-h` supported)
- **Arguments:** `POSCAR`; `Bin Size` (Å; dies if 0); `(Density)` rho0 (optional; if 0, computed as atoms/volume); `(Outfile)` (default `pdf.dat`).
- **Reads:** POSCAR (`read_poscar`).
- **Writes:** `pdf.dat` (or named) — `r pdf_val`; prints bin size, cutoff, max distance, volume, average density.
- **Logic:** Counts pairs within half the minimum box length (minimum image), bins distances; g(r) = N_bin/(N·shell_volume·rho0); PDF value `4π·r·rho0·(g(r)−1)`.
- **Notes:** Uses `Vasp.pm` + `Options.pm`. Cutoff is half the shortest cell vector (valid for ~cubic cells). Related: `pos2rdf.pl`, `pos2exafs.pl`.

### pos2rdf.pl
- **Purpose:** Print the radial distribution (neighbor counts per distance bin) around one chosen atom.
- **Usage:** `pos2rdf.pl <POSCAR filename> <atom to measure from> <bin size in Angstroms>` (exactly 3 args)
- **Arguments:** `POSCAR`; central atom (1-based); bin size (Å).
- **Reads:** POSCAR (`read_poscar`).
- **Writes:** stdout — per-bin `distance (count) : neighbor indices…` (1-based) in ascending distance.
- **Logic:** For each other atom, fractional difference from the center (`pbc`) refined by Wigner–Seitz (`pbc_difference_ws`), → Cartesian (`dirkar`), binned by magnitude.
- **Notes:** The only converter here using the more accurate Wigner–Seitz minimum image. Related: `pos2pdf.pl`, `pos2exafs.pl`.

### diffcon.pl
- **Purpose:** Print the per-atom and total displacement between two POSCAR (or two `.con`) structures.
- **Usage:** `diffcon.pl <POSCAR 1 filename> <POSCAR 2 filename>`
- **Arguments:** the two structure files (POSCAR or `.con`).
- **Reads:** two POSCARs; if both names match `.con`, they are first converted to temp POSCARs via `pos2con.pl`.
- **Writes:** stdout — `dx dy dz : distance atom#` per atom (Cartesian, Å), then a summary line.
- **Logic:** Fractional difference (`pbc_difference`) → Cartesian (`dirkar`) → per-atom magnitudes; the printed "Vector" is `√(Σ distance²)`. Both share the second file's basis.
- **Notes:** Uses `Vasp.pm`. Source quirk: the per-atom `$dist` in the final "Sum" field is the last atom's distance, not a true sum. Temp POSCARs are deleted.

### tcon.pl
- **Purpose:** Interactive terminal program (v0.40) to view, select, edit, transform, and plot the atoms in an EON `.con` configuration file.
- **Usage:** `tcon.pl [-F | -rc <file>] <file>` (also `-v`/`--version`); then drives an interactive command loop on stdin.
- **Arguments:** `<file>` — the `.con` to load; `-v`/`--version`; `-F` start without an rc file; `-rc <file>` use that rc (startup-commands) file.
- **Reads:** the `.con` (seed/time, box, shear/angles, components, masses, coords, velocities); its rc file (`.tconrc`) and defaults file (`.tcondat`).
- **Writes:** saved `.con` files (`save` → default `out.con`); EPS plots; updates `.tcondat`. Most commands print to stdout.
- **Logic:** A `mainloop` reads commands to select atom groups (by index/range/component/tag) and apply operations: `add`/`drop`, `dist`/`bonds`, `mirror`, `rot`, `scale`, `shift`, set radius/color/label/type/tag/sphere, `box`/`sph` subselect, `info`, `store`/`recall`, `save`, `plot`. Geometry ops act on in-memory Cartesian `.con` coords; unknown commands are passed to `/bin/sh`.
- **Notes:** ~2000 lines, fully interactive (not a batch converter despite its group). Self-contained (no `Vasp.pm`); persistent aliases/options in `.tcondat`/`.tconrc`.

---

## General geometry & structure utilities

Small tools acting mostly on POSCAR/CONTCAR (or `.con`). **Note:** a few names are misleading vs what the source actually does — flagged per entry.

### posinterp.pl
- **Purpose:** Linearly interpolate between two POSCARs at a given fraction to produce an intermediate geometry.
- **Usage:** `posinterp.pl <POSCAR 1> <POSCAR 2> <fractional distance between>`
- **Arguments:** start POSCAR, end POSCAR, interpolation fraction (0.5 = midpoint).
- **Reads:** two POSCARs (`read_poscar`); the first file's line-1 comment becomes the output description.
- **Writes:** `POSCAR.out`; prints `Total atoms` and `Lattice`.
- **Logic:** Per component, `pbc(coord1 + fraction·pbc(coord2 − coord1))` — moves along the minimum-image vector by the fraction and re-wraps. Fractional coords; shared basis from the second read.
- **Notes:** Uses `Vasp.pm`. Both POSCARs must share atom count/ordering/lattice. Fractions outside [0,1] extrapolate. Used by `neb2dim.pl`/`insaddimages.pl`.

### dist.pl
- **Purpose:** Compute the total root-sum-square Cartesian displacement (one scalar) between two POSCARs with the same atoms/lattice, using minimum-image differences.
- **Usage:** `dist.pl <POSCAR 1 filename> <POSCAR 2 filename>`
- **Arguments:** the two structure files.
- **Reads:** two POSCARs (`read_poscar`); basis from the second.
- **Writes:** stdout — a single number (the distance, Å).
- **Logic:** Per-atom fractional difference (`pbc_difference`, refined by `pbc_difference_ws`) → Cartesian (`dirkar`); `magnitude` = √(Σ of all atoms' squared Cartesian displacements).
- **Notes:** Despite the name, this measures the **whole-structure** difference between two POSCARs (one scalar), not a distance between two atoms. For atom-to-atom distances use `distatom.pl`/`neighbors.pl`. Used by `nebbarrier.pl`/`neb2dim.pl`.

### distatom.pl
- **Purpose:** Compute the minimum-image distance between two atoms read from one or two `.con` files.
- **Usage:** `distatom.pl <file1.con> <atom1> <atom2>` (one file) or `distatom.pl <file1.con> <file2.con> <atom1> <atom2>` (two files)
- **Arguments:** first `.con`; optionally a second `.con`; the two 1-based atom numbers (indexed against per-type counts).
- **Reads:** one or two `.con` files (box lengths line 3, type count line 7, per-type counts line 8).
- **Writes:** stdout — each atom's index/file/Cartesian coords, then `The distance between them is: <dist>`.
- **Logic:** Locates an atom's line via cumulative type counts (block stride `10+2*type`); orthorhombic minimum image by adding/subtracting box lengths until within ±box/2; Euclidean norm. Cartesian, Å.
- **Notes:** No `Vasp.pm`. Assumes an orthogonal box.

### neighbors.pl
- **Purpose:** Compute minimum-image distances from one central atom to all atoms and write them sorted ascending (a neighbor list).
- **Usage:** `neighbors.pl <POSCAR filename> <central atom>`
- **Arguments:** POSCAR; central atom (1-based).
- **Reads:** POSCAR (`read_poscar`).
- **Writes:** `neighdist.dat` — sort-rank, original index, Cartesian coords, distance from the central atom.
- **Logic:** Per atom, fractional difference from the center (`pbc`) → Cartesian (`dirkar`) → `magnitude`; selection-sorted ascending. Å.
- **Notes:** Uses `Vasp.pm`. Single-image `pbc` (not Wigner–Seitz), so for very skewed cells the minimum image is approximate.

### center.py
- **Purpose:** Center a structure in its cell, optionally adding vacuum padding on each side.
- **Usage:** `center.py FILE [DISTANCE]`
- **Arguments:** `FILE` (read and overwritten); `DISTANCE` (optional Å of vacuum per side; default `None` = recenter without resizing); `-h`.
- **Reads:** `FILE` (`aselite.read_any`).
- **Writes:** overwrites `FILE` with the centered structure.
- **Logic:** `atoms.center(distance)` — with a distance, enlarges the cell to leave that much vacuum per side; without, centers in the current cell. Å.
- **Notes:** Depends on `aselite`. Overwrites the input.

### rattle.py
- **Purpose:** Randomly displace all atoms by Gaussian noise of a given standard deviation (break symmetry / perturb).
- **Usage:** `rattle.py FILENAME STDDEV`
- **Arguments:** `FILENAME` (read and overwritten); `STDDEV` (Gaussian std, Å).
- **Reads:** `FILENAME` (`aselite.read_any`).
- **Writes:** overwrites `FILENAME` with the rattled structure.
- **Logic:** `atoms.rattle(stddev)` — adds independent normal displacements (respecting constraints; default seed `None`, so non-deterministic). Å.
- **Notes:** Depends on `aselite`. The internal usage message misprints "center.py" (copy-paste). No seed argument, so runs are not reproducible.

### stretch.py
- **Purpose:** Move one atom along the bond defined by two atoms, lengthening/shortening that bond by a distance.
- **Usage:** `stretch.py FILENAME INDEX1 INDEX2 DISTANCE`
- **Arguments:** `FILENAME`; `INDEX1` (anchor, 0-based); `INDEX2` (atom to move, 0-based); `DISTANCE` (Å along the bond); `-h`.
- **Reads:** `FILENAME` (`aselite.read_any`).
- **Writes:** `FILENAME_stretch` (original left unchanged).
- **Logic:** Bond vector `r[INDEX2]−r[INDEX1]`, normalized; adds `DISTANCE·(unit bond)` to atom `INDEX2`. Cartesian, Å; no minimum image.
- **Notes:** Depends on `aselite` + NumPy. **0-based** indices (unlike the Perl tools). Only `INDEX2` moves.

### pushapart.pl
- **Purpose:** Relax a structure under a pairwise repulsive force so no two atoms are closer than a cutoff (remove overlaps).
- **Usage:** `pushapart.pl <distance in Ang> <file (POSCAR format)> [ORTHOGONAL]`
- **Arguments:** `rcut` (min allowed distance, Å); input POSCAR; `ORTHOGONAL` (optional; nonzero = fast orthorhombic minimum image; default `0`).
- **Reads:** the POSCAR (`read_poscar`).
- **Writes:** moves the original to `<file>.'orig'` and writes the relaxed structure back to `<file>`; prints per-step progress.
- **Logic:** Steepest descent (ε=0.1, ≤100000 steps, max step 0.2 Å): pairs within `rcut` get a linear repulsive force (slope −0.3); minimum image by brute-force ±1 lattice search (or box wrapping in orthogonal mode); respects frozen (`F`) DOF; converges when no pair is closer than `rcut`. Å.
- **Notes:** Uses `Vasp.pm`. Adapted from `nebavoid.pl`. The `mv` quoting writes the backup to a file literally named `<file>.'orig'`.

### boxset.pl
- **Purpose:** Rescale a POSCAR's lattice constant (line-2 scale) while keeping atomic Cartesian positions fixed.
- **Usage:** `boxset.pl [POSCAR] [New Lattice Constant]`
- **Arguments:** input POSCAR; the new overall scaling factor (Å); `-h`.
- **Reads:** the named POSCAR.
- **Writes:** `POSCAR.out`; prints `Total atoms`, `Lattice`, and an (empty) `Shift`.
- **Logic:** Converts coords to Cartesian (`dirkar`), multiplies each basis component by `new/old`, then `kardir` recomputes fractional coords against the rescaled basis — box scales while Cartesian positions are held fixed.
- **Notes:** Uses `Vasp.pm` + `Options.pm`. The printed `Shift` is a leftover with no effect.

### double.pl
- **Purpose:** Double the simulation cell (and atom count) along a chosen lattice vector.
- **Usage:** `double.pl <inputfile> [outputfile]` then enter `1`, `2`, or `3` at the prompt to pick the vector.
- **Arguments:** input POSCAR; `outputfile` (optional, default `ciPOSCAR`); interactive stdin `1`/`2`/`3` (else aborts).
- **Reads:** the POSCAR; an intermediate `tmp.con` from `pos2con.pl`.
- **Writes:** the output file (doubled POSCAR); temporaries `tmp.con`/`tmp2.con` created then deleted.
- **Logic:** Doubles each per-type count, writes each atom plus a copy with `+1` on the chosen fractional component, then converts through `.con` to double the box vector and back.
- **Notes:** Depends on `pos2con.pl`. Default output name `ciPOSCAR`. Minor source typos in prompt text.

### posvdel.pl
- **Purpose:** Strip velocity (and trailing predictor-corrector) blocks from a POSCAR/CONTCAR, including concatenated multi-image files.
- **Usage:** `posvdel.pl [POSCAR]` (no arg → `POSCAR`)
- **Arguments:** file to clean (default `POSCAR`).
- **Reads:** the input (VASP5 6-line header, counts, coordinate-mode, atom positions).
- **Writes:** a temp `<poscar>_nov` moved over the original (in-place); prints per-image messages.
- **Logic:** Per concatenated image, copies the header + counts + mode + `natoms` position lines, then peeks ahead — a blank line + a 3-component line signals a velocity block, which is consumed/discarded.
- **Notes:** No `Vasp.pm`. Self-names "posvstrip.pl". Assumes VASP5 format; relies on a blank-line-then-3-numbers heuristic.

### getangle.py
- **Purpose:** Report the three inter-lattice-vector angles, the three side surface areas, and the cell volume of a `.con` file.
- **Usage:** `getangle.py <file.con>`
- **Arguments:** `.con`/EON file (line 2 = scalar `a`, lines 3–5 = lattice vectors).
- **Reads:** the first five lines.
- **Writes:** stdout — angles (deg), side areas (Å²), volume (Å³).
- **Logic:** Angles from `arccos` of normalized dot products; areas = cross-product norms; volume = `(v2×v1)·v3·a³`.
- **Notes:** **Despite the name, reports lattice-vector angles, not a three-atom angle.** numpy-based; reads a `.con`-style header. The final `print("Volume…"` is missing its closing paren in the source.

### coverage.py
- **Purpose:** Developer/porting-status tool — lists every `.pl` in the current dir and reports whether a `.py` port exists / is missing / is intentionally skipped. **Does NOT compute adsorbate coverage.**
- **Usage:** `coverage.py` (status table) or `coverage.py <name.pl> […]` (toggle ignore-list entries)
- **Arguments:** zero or more `.pl` names; each toggles its membership in the hardcoded `ignore` list (the script rewrites its own source and exits).
- **Reads:** its own source (when editing the ignore list); globs `*.pl`/`*.py`.
- **Writes:** rewrites `__file__` (self-modifying) when given args; else prints a color-coded table.
- **Logic:** For each `.pl`, prints red if unported, green if a `.py` exists, or "not going to implement" if ignored. Pure porting bookkeeping.
- **Notes:** Python 2 only. Filename is misleading vs the "coverage" family.

### tist.py
- **Purpose:** Sum total ionic-step wall time across OUTCAR files (current dir + one level of subdirs, incl. `OUTCAR.gz`) and report cumulative compute time. **A timing/accounting tool, not a structure utility.**
- **Usage:** `tist.py` (no args; acts on `OUTCAR`/`OUTCAR.gz`/`job.sub`)
- **Arguments:** None (`sys.argv[1]` is read but unused).
- **Reads:** `OUTCAR` here and in immediate subdirs (`OUTCAR.gz` opened via gzip); optional `job.sub` for core count (after a `-n` token).
- **Writes:** stdout — per-file ionic-step times, total seconds and hours, optional core-hours, and an "overall average electronic step time".
- **Logic:** Parses `LOOP+:` lines to accumulate per-ionic-step times and counts `LOOP:` electronic steps; multiplies hours by the core count for total compute time. Seconds → hours (÷3600).
- **Notes:** Python 2/3. The electronic-step averaging is disabled, so the "average electronic step time" prints `0`. `filein = sys.argv[1]` is vestigial.

---

## Adaptive Kinetic Monte Carlo (AKMC)

AKMC drives long-timescale dynamics by repeatedly finding saddles out of the current state (via dimer searches), building a rate table from harmonic TST, and hopping to a new state. `akmc.pl` is the main driver; the others manage/visualize/reset the state-directory tree. See [overview.md](overview.md) and `references.html`.

### akmc.pl
- **Purpose:** Main AKMC driver — minimizes the initial state, spawns/monitors dimer saddle searches and minimizations, builds rate tables, selects a KMC event, and advances the system state to state (integrated with VASP and the VTST tools).
- **Usage:** `akmc.pl [amy | 1]` — run from inside the AKMC working directory; optional arg is the literal `amy` (verbose per-process screen logging) or `1` (force the orthogonal-cell fast path in radial-distance checks). No arg = normal run.
- **Arguments:** `$ARGV[0]` — `amy` → verbose logging; numeric `1` → `ORTHOGONAL=1` shortcut. No GetOptions; all real configuration comes from the `config` file.
- **Reads:** `config` (run parameters); `jobs.dat`, `st.dat`, `akmc.dat`, `freq.dat`, `OldRunDirFile`, `StEnergyFile`, per-state `RateTableFile`/`EventTable`; POSCAR/CONTCAR/POSCAR_sp and INCAR/OUTCAR in state and process subdirs.
- **Writes:** `akmc.dat` (KMC steps), per-state `st.dat`, `RateTableFile`(`_BolEqu`), appends to `StEnergyFile`, READMEs, and a rotated screen log (`out.dat`). Submits VASP jobs; prints progress.
- **Logic:** Reads ~35 config parameters (e.g. `MaxJobs`, `NumSearches=20`, `Temperature=77` K, `Ediffmax=0.05`, `Rdiffmax=0.04`, `SearchesAlgo="Dimer"`, `BarrierMax=10.0`, displacement params `NN_rcut=2.6`/`MaxCoordNum=8`). Each call reconciles running jobs, identifies the current state, spawns dimer searches + min1/min2 quench minimizations, classifies good vs bad saddles by reconnection and energy/distance tolerances, computes harmonic-TST rates (from `freq.dat` prefactors or a fixed `Prefactor`), assembles a rate table, draws a KMC event/time increment (optionally with a Boltzmann-equilibrium correction), and writes the new state. State equivalence uses energy (`Ediffmax`), configurational distance (`Rdiffmax`), and optional radial-distribution-function matching.
- **Notes:** ~5,500 lines; version 2.0 single-image dimer (Xu & Henkelman, *JCP* 129, 114104 (2008)). `UseKDB` is hard-disabled in this build. Depends on `Vasp.pm` and the wider VTST suite (`vfin.pl`, dimer/min helpers, `pos2con`/`con2xyz`). Run periodically (cron/queue) — each call advances as far as job availability permits.

### akmccleanjobs.pl
- **Purpose:** Clean up AKMC processes that were killed (e.g. for exceeding a barrier threshold) by archiving their files to reclaim disk space.
- **Usage:** `akmccleanjobs.pl [maindir]` (defaults to the current directory)
- **Arguments:** `maindir` — AKMC root to scan (default `.`).
- **Reads:** state dirs matching `st\d{4}`; each state's `st.dat` (greps `killed` processes); checks for `OUTCAR` in each.
- **Writes:** stdout status; runs `vfin.pl killed` in each killed process dir that still has an `OUTCAR`.
- **Logic:** For each killed process with an OUTCAR and no existing `killed` marker, finalizes/archives it via `vfin.pl killed`.
- **Notes:** Maintenance patch (Lijun Xu, 2008); newer `akmc.pl` handles killed runs as unconverged into `inter*` folders. Depends on `vfin.pl`.

### akmcmovie.pl
- **Purpose:** Build an XYZ movie of an AKMC run — either the KMC-step state walk or all mechanisms (saddle paths) within a single state.
- **Usage:** `akmcmovie.pl <filename (akmc.dat or st.dat)> <quadruple 0|1> <n inserted images> <all good+bad 0|1>` (last three optional, default 0)
- **Arguments:** `filename` (an `akmc.dat`-style index → step movie, or an `st.dat` → in-state mechanism movie); `quadruple` (1 = render a 2×2 supercell); `NumInsertedImages` (linear interpolation frames between configs); `all` (1 = include "bad"/non-connecting saddles).
- **Reads:** the index/`st.dat`; POSCAR/POSCAR_sp/CONTCAR in the state, process dirs (`prNNNN`), and their `mins/min1`,`mins/min2`,final subdirs.
- **Writes:** step movies → gzipped `watch_<akmcdir>.xyz.gz`; state movies → per-process `.xyz` tarred as `<akmcdir>_<stdir>.tar.gz`. Intermediate `.con`/`.xyz` removed.
- **Logic:** Parses the data file into energies/status/process records, converts the relevant POSCARs to xyz, concatenates initial→saddle→final, with optional linear interpolation (`spline_2sts`, PBC minimum-image).
- **Notes:** Uses `Vasp.pm`; shells to `quad.pl`/`quad_con.pl`/`pos2con.pl`/`con2xyz.pl`. Sets `VTST_BC=none` during quadrupling. Source typo: the visited-skip tests `$visited` vs the set `$visted` (ineffective).

### akmcprfc.pl
- **Purpose:** Report the total VASP force calls consumed by an AKMC process (its dimer search + both minimizations).
- **Usage:** `akmcprfc.pl [process directory] <--verbose> <--rezip>` (one or more dirs)
- **Arguments:** process directory/directories; `--verbose` (breakdown vs just the total); `--rezip` (re-compress any OUTCAR it decompressed).
- **Reads:** `OUTCAR`(.gz/.bz2) in the process dir and its `final`/`inter*` subdirs, plus `mins/min1`/`mins/min2`.
- **Writes:** stdout — the total force-call count, or a labeled breakdown with `--verbose`.
- **Logic:** Parses each OUTCAR's last `Iteration` number as that segment's force-call count and sums across all continuation/final segments and both minimizations.
- **Notes:** Relies on the VASP `Iteration N(…)` convention.

### akmcprocess.pl
- **Purpose:** Build a single connected XYZ movie (initial → saddle → final) for one AKMC process, run from inside that process directory.
- **Usage:** `akmcprocess.pl <quadruple 0|1> <st.dat>` (run inside a `prNNNN` dir; both args optional, default 0 and `st.dat`)
- **Arguments:** `quadruple` (1 = 2×2 supercell); `StFile` (parent state file, default `st.dat`).
- **Reads:** `../st.dat` (status/quality, which subdir is the final state); POSCAR/CONTCAR/POSCAR_sp + `medgamma` markers in the min/saddle dirs.
- **Writes:** `<prdir>.xyz` (concatenated initial+saddle+final); intermediate `.con`/`.xyz` removed.
- **Logic:** Reads the parent `st.dat` to order initial vs final minima, converts each endpoint (preferring `medgamma` else `CONTCAR`) and the saddle `POSCAR_sp` to xyz, concatenates.
- **Notes:** Uses `Vasp.pm`; shells to `quad.pl`/`pos2con.pl`/`con2xyz.pl`. Dies if not run inside a process dir.

### akmcprxyz.pl
- **Purpose:** Build an XYZ movie of the current configuration of every process in a state (one frame per process, labeled by directory).
- **Usage:** `akmcprxyz.pl` (no args; run inside a state dir with `st.dat` and `prNNNN` subdirs)
- **Arguments:** None.
- **Reads:** `st.dat` (process names); per process, best of `final/CONTCAR`, `final/POSCAR`, `CONTCAR`, `POSCAR`.
- **Writes:** `pr.xyz` — one frame per process, comment line set to the process directory name.
- **Logic:** Greps `st.dat` for `prNNNN`, copies each process's most current geometry, converts to xyz (`pos2con.pl`+`con2xyz.pl`), tags the header with the process name, appends.
- **Notes:** Uses `-s` checks so empty CONTCARs fall through to POSCAR. Depends on `pos2con.pl`/`con2xyz.pl`.

### akmcreset.pl
- **Purpose:** Reset AKMC processes that finished "done/bad" back to "quench/promising" so their saddles can be re-evaluated under new tolerances.
- **Usage:** `akmcreset.pl <st.dat>` (exactly one arg)
- **Arguments:** the `st.dat` to process.
- **Reads:** the `st.dat`; checks `prNNNN/mins/min1/final/CONTCAR` and `…/min2/final/CONTCAR` for each bad process.
- **Writes:** `st_reset_bad.dat` — a rewritten state file with eligible processes set to `quench`/`promising` and final fields blanked to `na`.
- **Logic:** Parses the state file; for each `done`+`bad` process whose two minima final CONTCARs exist, rewrites its fields (converting absolute energies back to barriers on write).
- **Notes:** Self-names `akmc_reset_bad.pl`; bundles its own `ReadSt`/`WriteSt`; uses `Vasp.pm`.

### akmcupdate.pl
- **Purpose:** Migrate an older AKMC `config` forward by appending the newer local-displacement parameters for `diminit.pl` if missing.
- **Usage:** `akmcupdate.pl` (no args; run in the AKMC dir with a `config` file)
- **Arguments:** None.
- **Reads:** `config` (`key = value` lines).
- **Writes:** rewrites `config` in place, appending any missing flags; prints the result and a count. No change if all present.
- **Logic:** Appends defaults for `DisplaceAlgo`=1, `DisplaceRange`=3, `NN_rcut`=2.6, `MaxCoordNum`=8 (the localized-displacement dimer-init scheme) when absent.
- **Notes:** Uses `Vasp.pm` (only for loading). Dies if no `config` found. Defaults match `akmc.pl`'s `ReadParm`.

### automagician.py
- **Purpose:** A SQLite-backed automation daemon that registers, monitors, re-processes (continues/fixes), and resubmits VASP optimization jobs across one or more queue machines, maintaining converged/unconverged ledgers.
- **Usage:** `automagician.py [options]` (no positional args; operates on the current directory tree and a job DB in `$HOME`/`$WORK`)
- **Arguments (optparse; default off unless noted):**
  - `-r`/`--register` — recursively find calculations under cwd and add to the DB.
  - `-p`/`--process` — re-check and re-process every unconverged job.
  - `-t`/`--test` — dry run (partial).
  - `-s`/`--silent` — suppress output.
  - `--rsc`/`--reset_converged`, `--rsa`/`--reset_all` — reset job convergence states.
  - `--cc`/`--clear_certificate`, `--ac`/`--archive_converged` — manage convergence certificates/archives.
  - `--cpl`/`--continue_past_limit` — keep processing but stop submitting once the limit is hit.
  - `-l`/`--limit N` — stop submitting beyond N queued jobs (default 99999).
  - `-b`/`--balance` — balance jobs across machines.
  - `--rcmb`, `--dbplaintext`, `--dbcheck`, `--rjs`, `--db_debug` — DB/utility modes (several partial).
  - `--delpwd` — remove the cwd from the DB.
- **Reads:** a SQLite DB (`$HOME`/`$WORK`); per-job `INCAR`, `ll_out`, `POSCAR`/`CONTCAR`, `XDATCAR`(.gz)/`fe.dat`, a submission template; queue state via `qstat`/`squeue`/`xqstat`. Convergence detected by grepping `ll_out` for "reached required accuracy - stopping structural energy minimisation".
- **Writes:** updates the DB; `preliminary_results.dat`, `error_log.dat`, `converged_jobs.dat`/`unconverged_jobs.dat`, `convergence_certificate` files, combined `cmbFE.dat`/`cmbXDATCAR`, modified `INCAR`s, generated SBATCH/PBS scripts, a single-instance lockfile. Submits via `sbatch`/`qsub`; cancels via `scancel`/`qdel`.
- **Logic:** Determines the host "machine number" (chooses `$HOME` vs `$WORK`, partitions, submission style), takes a lockfile, loads job statuses from DB + live queue, then per command registers jobs or inspects each unconverged job's output/INCAR to decide converged / errored (detects VASP "I REFUSE TO CONTINUE WITH THIS SICK JOB" etc.) / needs-continuation, edits restart files, and enqueues resubmissions honoring the limit. Can build follow-on `sc`/`dos`/`wav` calculations from a converged job. Releases the lock on exit/interrupt.
- **Notes:** Heavily site-specific (TACC-style machines, `xqstat`, hard-coded helper paths); several flags marked "not fully implemented". Supports remote operation over SSH. Depends on `vef.pl` and `vfin.pl`.

---

## Kinetic Database (KDB)

KDB stores found saddle processes (reactant/saddle/product + mode) so AKMC can reuse them by matching a configuration's local atomic environment. `kdbadd*` insert; `kdbquery*` search and transform matches onto the current structure. (Note: `akmc.pl` in this build has KDB disabled.)

### kdbaddpr.pl
- **Purpose:** Original full-featured kdb insertion — add a min1/min2/saddle/mode process with a rotation-alignment duplicate check.
- **Usage:** `kdbaddpr.pl [--debug] <min1_CONTCAR> <min2_CONTCAR> <saddle_CENTCAR> <mode_file>`
- **Arguments:** the four positional files; `--debug` (verbose + `stripped.xyz` + alignment-movie frames).
- **Reads:** the four inputs; existing DB entries `$KDBHOME/$desc/$N/{min1,min2,saddle}.xyz` for dedup.
- **Writes:** a new `$KDBHOME/$desc/$N/` with `min1.xyz`/`min2.xyz`/`saddle.xyz`/`mode`/`mobile`/`.info` and hidden `.car` copies; debug movies when `--debug`.
- **Logic:** Marks atoms moving ≥ `$cutoff`=0.7 Å as mobile (+ neighbors within covalent-radius×1.3), clumps across PBC, recenters on the saddle COM. Dedup: filter by element counts, then align onto each DB saddle by rotating about the two atoms farthest from the COM and relaxing with a spring/torque minimization (`springK`=10, `maxIter`=1000, `duplicateCutoff`=0.5 Å).
- **Notes:** Uses `Vasp.pm`/`kdbutil.pm`/`Math::Trig`. Larger/slower than `kdbaddprnew.pl`. `$desc` = sorted element list.

### kdbaddprnew.pl
- **Purpose:** Streamlined successor to `kdbaddpr.pl` — add a process, with a distance-table-mapping dedup instead of rotation fitting.
- **Usage:** `kdbaddprnew.pl [--debug] <min1_CONTCAR> <min2_CONTCAR> <saddle_CENTCAR> <mode_file>`
- **Arguments:** the four positional files; `--debug` (also writes `stripped.xyz`).
- **Reads:** the four inputs; existing `$KDBHOME/$desc/$N/saddle.xyz` for dedup.
- **Writes:** a new `$KDBHOME/$desc/$N/` with `min1.xyz`/`min2.xyz`/`saddle.xyz`/`mode`/`mobile`/`.info` + hidden `.car` copies; prints `good.` or `duplicate of …`.
- **Logic:** Same mobile-atom selection (`cutoff`=0.7 Å, neighbor tolerance 0.3) and PBC clumping/COM-centering as `kdbaddpr.pl`, but dedup uses element-count hashing + a recursive distance-table mapping (`dieIfMapped`, tolerance `ANGSTROM_FUDGE`=0.5 Å).
- **Notes:** Uses `Vasp.pm`/`kdbutil.pm`. `kdbaddvpr.pl` calls the add family per process directory.

### kdbaddvpr.pl
- **Purpose:** Batch wrapper — scan akmc `prNNNN` process dirs and call `kdbaddpr.pl` to insert each valid one.
- **Usage:** `kdbaddvpr.pl <pr_dir> [<pr_dir> ...]`
- **Arguments:** one or more akmc process dirs (each with `final/` and `mins/min1`,`mins/min2`).
- **Reads:** per dir, `final/CENTCAR`, `mins/min1/final/CONTCAR`, `mins/min2/final/CONTCAR`, `final/NEWMODECAR` or `MODECAR`; status/quality from `../st.dat`.
- **Writes:** no files directly; prints status and delegates to `kdbaddpr.pl` (which writes the DB entry).
- **Logic:** For each dir with all required files, picks the saddle/minima/mode and shells `kdbaddpr.pl`; skips incomplete dirs with a status message.
- **Notes:** Uses `kdbutil.pm`; hard-codes `kdbaddpr.pl` (not the `new` variant). Internal name `vkdbaddpr.pl`.

### kdbinsert.py
- **Purpose:** From a completed NEB run, locate reactant/saddle/product, compute forward/reverse barriers and the saddle mode, and insert the process via the local/remote kdb client.
- **Usage:** `kdbinsert.py [-l]` (operates on the NEB image dirs `00, 01, …`)
- **Arguments:** `-l` — insert into a local kdb (`kdb_local_client`) instead of remote (default remote).
- **Reads:** `INCAR` (`IMAGES`); each image's `OUTCAR` (`energy without`, gunzips `.gz`); image POSCAR/CONTCAR via `kdb.aselite.read_vasp`.
- **Writes:** `MODE.dat` (tab-separated mode vector); submits `run(["insert", reactant, saddle, product, MODE.dat, fwd_barrier, rev_barrier])`. Prints the barriers and saddle index.
- **Logic:** Reads every image's final energy, takes the max-energy image as the saddle, forward/reverse barriers = `Emax − E(reactant/product)`; the mode is the PBC-wrapped displacement between the images bracketing the saddle.
- **Notes:** Depends on `kdb_remote_client`/`kdb_local_client`/`kdb.aselite`. Endpoint-as-saddle is not handled; an inline comment flags the PBC handling as unfinished.

### kdbquery.pl
- **Purpose:** Search the kdb for saddle processes matching the current configuration's local environment using radial-histogram scoring + rotational alignment, emitting transformed candidate saddle/mode files (original implementation).
- **Usage:** `kdbquery.pl [--debug] [--mapping] [--score f] [--rhsco f] [--rhc f] [--rhbs f] [--rhs f] [--nfp f] <CAR-file-to-match>`
- **Arguments:** the query POSCAR/CAR (required); `--score` (per-atom cutoff, default 0.25); `--rhsco` (RH score cutoff, 0.5); `--rhc` (RH radial cutoff, 5.0); `--rhbs` (RH bin size, 5.0); `--rhs` (RH scale, 1.0); `--nfp` (neighbor tolerance, 0.3); `--mapping`; `--debug`.
- **Reads:** the query CAR; DB entries via `getProcessDirs` — each `min1.xyz`/`min2.xyz`/`mobile`/`saddle.xyz`/`mode`.
- **Writes:** a fresh `./kdbmatches/` with per-match `SADDLE_<N>` (predicted saddle POSCAR), `MODE_<N>` (normalized mode), `.done_<N>`.
- **Logic:** Builds per-atom radial histograms (Gaussian-binned, element-resolved) to pre-filter candidate correspondences, then aligns each DB process onto the query by rotation + torque/spring minimization (`maxIter`=16, `springK`=1.0); a per-atom cost below `ScoreCutoff` accepts the match (tolerance 0.25 Å).
- **Notes:** Uses `Vasp.pm`/`kdbutil.pm`/`Math::Trig`. Superseded by `kdbquerynew.pl`.

### kdbquerynew.pl
- **Purpose:** Newer kdb search using analytic three-atom geometric alignment (no radial-histogram pre-scoring), transforming each match onto the query and emitting candidate saddle/mode files.
- **Usage:** `kdbquerynew.pl [--debug] [--dedupe] [--allmob] [--score f] [--af f] [--nfp f] <POSCAR-to-match>`
- **Arguments:** the query POSCAR (required); `--score` (per-atom cutoff, default 0.1); `--af` (distance-equality tolerance, 0.1 Å); `--nfp` (neighbor tolerance, 0.2); `--dedupe` (drop matches within 0.25 Å of an emitted one); `--allmob`; `--debug`.
- **Reads:** the query POSCAR; DB entries via `getProcessDirs` — `min1.xyz`/`min2.xyz`/`mobile`/`saddle.xyz`/`mode`.
- **Writes:** a fresh `./kdbmatches/` with per-match `SADDLE_<N>`, `MODE_<N>`, `.done_<N>`.
- **Logic:** Selects three reference mobile atoms (a,b,c), analytically computes the translation + two rotations mapping the DB environment onto the query, refines by torque/spring minimization (`springK`=1.0, `maxIter`=64, `FineCriteria`=1e-4); matches below the per-atom `ScoreCutoff` have the DB saddle coords inserted into a copy of the query cell and the DB mode rotated/normalized in.
- **Notes:** Uses `Vasp.pm`/`kdbutil.pm`/`Math::Trig`. Usage string still self-identifies as "kdbquery.pl". Frozen (`F`) query atoms are left unmodified.

### kdbquery.py
- **Purpose:** Front-end that queries the kdb (local/remote) for a structure and optionally sets up dimer calculation directories or interpolation movies from the matches.
- **Usage:** `kdbquery.py [-l] [-s] [-m] [-c] <structure>` (operates in the cwd)
- **Arguments:** `<structure>` (query POSCAR, required); `-l` (local kdb); `-s` (set up per-match calc dirs); `-m` (build mechanism movies); `-c` (pass user config to the remote query).
- **Reads:** the query POSCAR; for `-s`/`-m`, the client's `./kdbmatches/` output (`PRODUCT_<i>`, `SADDLE_<i>`, optional `MODE_<i>`); for `-s` also `INCAR`/`KPOINTS`/`POTCAR`.
- **Writes:** with `-s`, `kdbmatches/KDB<i>/{SADDLE<i>,PRODUCT<i>}/` populated with copied inputs (+`MODE`), editing each saddle `INCAR` for a dimer run (`IBRION=3, POTIM=0.0, ICHAIN=2, EDIFF=1E-7, IOPT=2`); with `-m`, `PROCESS_<i>` movie files. Prints the suggested-process count.
- **Logic:** Delegates the matching to `kdb_local_client`/`kdb_remote_client` `run(["query", structure, …])`; this script only orchestrates and post-processes the client's `kdbmatches/` into ready-to-run dimer dirs or movies.
- **Notes:** Depends on the client modules and full `ase.io` (not aselite). The `PRODUCT_`/`SADDLE_`/`MODE_` files come from the client layer, not the Perl `kdbquery*.pl` (which emit only `SADDLE_`/`MODE_`).

### kdbquerymovie.pl
- **Purpose:** Generate interpolated `.xyz` movies (min1 → saddle → min2) for every kdb entry matching a given element list.
- **Usage:** `kdbquerymovie.pl <element> [<element> ...]`
- **Arguments:** element tokens joined into the description used to select DB entries.
- **Reads:** per matching DB dir, `min1.xyz`/`min2.xyz`/`saddle.xyz`.
- **Writes:** a fresh `./kdbmovie/` with `movie-<i>.xyz` and `.info_<i>` (source DB path); prints the index.
- **Logic:** Produces 16 linearly interpolated frames min1→saddle and 16 saddle→min2 per entry. Pure Cartesian interpolation; no PBC/energy.
- **Notes:** Uses `Vasp.pm`/`kdbutil.pm`; recreates `kdbmovie` each run.

---

## Shared modules, libraries & non-`.py`/`.pl` helpers

These are *not* standalone scripts (so they have no CLI), but the scripts above depend on them. Listed for completeness.

- **`Vasp.pm`** — the core Perl library (`read_poscar`/`write_poscar`, `read_othercar`/`write_othercar`, `dirkar`/`kardir`, `set_bc`, `pbc`/`pbc_difference`/`pbc_difference_ws`, `dist`, `magnitude`, `volume`, `inverse`, `dot_product`, `gauss`, vector helpers).
- **`Options.pm`** — command-line option parsing (`-h` help).
- **`kdbutil.pm`** — KDB helpers (`kdbHome`, `getProcessDirs`, `loadXYZ2CAR`, `stdatStatus`/`stdatQuality`).
- **`Math/Matrix.pm`, `Math/MatrixReal.pm`, `Math/Approx.pm`** — linear algebra (eigensolve, pseudo-inverse) and least-squares fitting used by the dynamical-matrix, kdb, and ssNEB scripts.
- **`Fortran/Format.pm`** — Fortran-style fixed-width output (used by `chgsumf.pl`).
- **`aselite.py`** — a bundled, self-contained minimal ASE used by the Python scripts (`read_vasp`/`write_vasp`, `read_con`/`write_con`, `read_xyz`/`write_xyz`, `read_any`, `read_vasp_out`, minimal `NEB`/`interpolate`). Not a CLI tool.
- **Compiled binaries / Fortran helpers** (no `.py`/`.pl` extension): `vp`, `scale`, `sum_dos`, `sum_dos_np`, `sumup_dos`, `split_dos` (a binary distinct from `split_dos.py`), and the `Math/`, `Fortran/` directories.
- **Shell cleaners (`*.sh`)** invoked by `vfin.pl`: `nebclean.sh`, `vclean.sh`, `dymclean.sh`, `dimclean.sh`/`dimclean2.sh`, `lanclean.sh`, `insclean.sh`; plus `chgsplit.sh`, `mddata.sh`/`mdplot.sh`, `am-cron-wrapper.sh`, `insta-submit*.sh`.
- **gnuplot templates (`*.gnu`)** used by the plot scripts: `vef.gnu`, `nebplot.gnu`/`nebplotss.gnu`, `dimplot.gnu`, `insplot.gnu`, `mdplot.gnu`.
