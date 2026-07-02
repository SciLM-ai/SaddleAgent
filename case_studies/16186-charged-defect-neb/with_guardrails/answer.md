**VASP *is* reading `NELECT=1072` correctly — that's a red herring. The run dies because your two NEB endpoints list their F atoms in *different orders*, so `nebmake` pairs ~52 fluorines with the wrong partner and drags them 5–9 Å straight across the cell. The interior images end up with atoms ~0.01 Å apart, the density is garbage, and VASP crashes. Fix the atom-ordering of the endpoints and re-interpolate; the electron count is irrelevant.**

## Why it isn't NELECT

`03/OUTCAR` shows your electron count was applied exactly as set:

```
NELECT =    1072.0000    total number of electrons
```

The line you fixated on —

```
old charge density: 1073.00000  new 1072.00000
```

— is just VASP imposing that `NELECT` on the first SCF step. With `ICHARG=2` the starting density is a *superposition of atomic (neutral) charge densities* (`docs/vasp/icharg.md`), which integrates to the neutral count **1073**; after one iteration it's constrained to your **1072**. That 1 e⁻ gap on step 1 is normal for any charged-cell start and is a symptom, not the cause. (Your on-disk INCAR actually has `ICHARG=0` = "from the initial wavefunctions" per the same doc; with no WAVECAR present the initial density still carries the neutral count, so the same thing happens — not the failure either.)

## What actually killed it

Image 03's own log, `03/stdout`:

```
The distance between some ions is very small. ... I HOPE YOU KNOW WHAT YOU ARE DOING!
DAV:  1   0.248925792357E+07   ...        <-- SCF energy = 2.5 MILLION eV
Error EDDDAV: Call to ZHEGV failed. ...  ----> I REFUSE TO CONTINUE ... <----
```

`03/OUTCAR`'s neighbor table has dozens of pairs at **0.01–0.05 Å** (e.g. Li ion 11 ↔ F ion 145 at 0.01 Å). Atoms are sitting on top of each other. Comparing your `POSCAR_i` vs `POSCAR_f` (both 108 Li + 107 F = one F vacancy, cubic a = 12.079 Å):

| Atom correspondence | # atoms that move | max displacement |
|---|---|---|
| **by line order** (what `nebmake` uses) | **52 F atoms** | 9.44 Å (atom 162), several ~7 Å |
| **by nearest physical site** | **1 F atom** | one vacancy hop |

As *sets of positions*, 106/107 F and all 108 Li coincide between your endpoints — only a single F genuinely relocates, so the endpoints correctly describe one anionic-vacancy hop and both are relaxed (`reached required accuracy` in `00`/`06`). But `nebmake` interpolates **atom-i → atom-i by line order**, and your F block is reordered between the two files. Fifty-two fluorines therefore get matched to a *different* physical F 5–9 Å away. I confirmed image 03 is the exact minimum-image linear midpoint of your endpoints (max fractional deviation 0.0), so the interpolation is faithfully drawing straight lines between mismatched atoms; halfway along, each swapped pair collapses onto the same point → the 0.01 Å overlaps → density explodes → `ZHEGV` crash.

The many-atoms-cross-over, "too close" warnings, and hundreds-to-millions-of-eV interior energies are the textbook signature of **inconsistent per-atom ordering across the band** — distinct from a single migrating atom passing through one occupied site (which strands only *one* image). This is the reorder-to-fix case, not the IDPP-only case.

"Neutral worked, charged didn't" is coincidence: the neutral endpoints happened to share atom order; the charged final state got its F atoms reindexed (a re-sorted or independently rebuilt/converted CONTCAR). Nothing here depends on the electron count.

## The fix

Don't touch INCAR/NELECT — rebuild the band with consistent ordering:

1. **Make index N the same physical atom in both endpoints.** Cleanest route: take the relaxed initial structure (`00/CONTCAR`) and build the final state by moving **only the migrating F** into the vacancy, leaving every other atom line exactly in place; relax that (CONTCAR preserves order). Because this is a vacancy/equivalent-site path, same-index pairing isn't enough if you instead reorder `POSCAR_f` — you must pair each F to its **nearest** counterpart in the other endpoint (a min-displacement matching script), or identical atoms swap across the cell again.
2. **Re-interpolate:** `nebmake.pl POSCAR_i POSCAR_f 5`, or better `nebmake.py POSCAR_i POSCAR_f 5` (IDPP by default — more robust for a hop). Note IDPP still pairs atom-i→atom-i, so step 1 is required *first* regardless of interpolation method.
3. **Verify before submitting:** `dist.pl 00/POSCAR 06/POSCAR` — only the one migrating F should show a large IS→FS displacement; anything else moving far flags residual misordering. Then play the band movie (`nebmovie.pl` in VESTA/OVITO): every atom should glide sub-Å between adjacent images. Your current images 02/03/04 (min pair 0.65 / 0.00 / 0.65 Å) fail this.

Secondary (not the cause): VTST *is* linked — the `VTST` banner is present in the actual NEB image dirs `01–05` (its absence in `00`/`06` is expected, those are plain endpoint relaxations). VASP also warned it used the default `MAGMOM=1`; for LiF with a hole (a spin-½ small-polaron / open-shell state) set `MAGMOM`/`NUPDOWN` deliberately and confirm the endpoints sit in the lowest-energy spin state. And your on-disk INCAR still reads `System = Si`.

**Confidence: high** — the overlap, the crash, and the 52-vs-1 mover contrast are all directly in your files. If you paste `POSCAR_i` and `POSCAR_f` (or `00/CONTCAR` and `06/CONTCAR`) I'll identify exactly which F indices are swapped and hand back a correctly ordered final endpoint.
