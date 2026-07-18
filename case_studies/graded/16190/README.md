# Topic 16190 — Handling Vacancies in VCA Setup (NEB calculation)

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> The AI is basically correct, but there is no evidence that ISYM is a problem.  ISYM can cause problems with bands where the endpoints have a symmetry that images along the band does not, but here, even the endpoints are not converged, so it is misleading to point to ISYM as a significant concern.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**musanna** (2025-07-14 12:55):

Hello All,

I am trying to use VCA in a mixed-anion system for the migration energy barrier. After setting up the POSCAR as per VASP documentation (with duplicated coordinates for the mixed species), the relaxation works fine. However, when I introduce a Li vacancy, the simulation crashes with an internal error in us.F and a segmentation fault for the initial and final structure.

Is there something additional I need to do in the POSCAR or POTCAR to make VCA + vacancy stable?

I’d really appreciate any guidance on how to handle vacancies properly within a VCA context.

Thanks,

Musanna

## Expert answer (forum ground truth)

**graeme** (2025-07-15 09:56):

I would suggest starting with the endpoints.  Nothing is converged, in fact, the energies and forces diverge and are crazy.  Start with getting those working.  There is no special considerations for VCA with NEB; if you can get it working with a regular optimization, it should work with the NEB as well.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Bottom line: this almost certainly isn't a VCA↔vacancy incompatibility — it's VASP's symmetry package choking on the VCA structure once the vacancy lowers the cell symmetry. Set `ISYM = 0` in the INCAR, and re-check the POSCAR you just hand-edited (atom-count line and species order) and the `VCA` weight list. Debug this in the plain endpoint relaxation, not as an NEB problem — VCA + a vacancy is transparent to NEB; nothing NEB-specific is needed.**

### Why this is the diagnosis

The discriminator you gave is the whole story: the **perfect (vacancy-free) VCA cell relaxes fine, and only the defected cell crashes**. Almost nothing about the VCA *setup* changes when you delete one Li — the concatenated POTCAR, the duplicated-coordinate sites, and the VCA weights are identical. What genuinely changes is (a) the **symmetry**, (b) the **atom count in POSCAR**, and (c) the electron count. An internal error in `us.F` (the non-local/ultrasoft + augmentation-charge machinery) followed by `signal 11` is the classic signature of the **augmentation-charge symmetrization being applied with symmetry operations that are inconsistent with the actual atom set**.

VCA represents each mixed-anion site as two atoms sitting at *identical* coordinates, one per POTCAR block, weighted by `VCA`. VASP's symmetry routines don't know about virtual atoms — in the perfect cell the symmetry it detected happened to stay self-consistent, so it ran. Remove a Li and the point group/Wyckoff multiplicities shift; the symmetrization of the PAW/US augmentation charges in `us.F` is now driven by operations that don't map the (duplicated-coordinate) atom set onto itself, and it crashes. The standard VCA practice is therefore to **run with symmetry off** — and `docs/vasp/isym.md` confirms `ISYM` should be off (`0` or `-1`) whenever the structural symmetry assumption is broken. You'd want it off for the migration band anyway, since the hopping path breaks symmetry.

This matches the skill's launch-crash doctrine (`reference/neb-diagnostics.md`): a `us.F`/segfault at launch is *not* the shiny new ingredient being "NEB-incompatible" — VCA, vacancies, and special pseudos are transparent to NEB. Debug the ingredient in a **standalone single-image relaxation** (which is exactly what your endpoint relax is), get it to the `EDIFFG` force criterion, then reuse the *identical* POSCAR/POTCAR/INCAR for the band with no NEB-specific changes.

### Concrete fixes / checks, in order

1. **`ISYM = 0`** in INCAR (try `-1` if `0` still misbehaves). This is the single most likely fix.

2. **Re-check the POSCAR you edited** — after deleting the Li line, the per-species count line must still sum *exactly* to the number of coordinate lines, and the species order must still match the POTCAR concatenation order (`docs/vasp/potcar.md`: POTCAR is one block per species, same order as POSCAR). An off-by-one or a stray blank line here is the other thing that only affects the defected cell, and it also crashes the projector setup.

3. **`VCA` tag length** — deleting a Li atom must *not* change the number of POTCAR blocks (you keep the Li block, just lower its count). Confirm `VCA` (and any per-species `POMASS`) still has exactly one entry per POTCAR species, in order.

4. **`NELECT`** — if you set it by hand, subtract the removed Li's valence (1, or 3 for a Li_sv POTCAR); a stale `NELECT` can also abort. If you didn't set it, ignore.

5. After it runs, confirm the endpoint truly converged before building the band:

  - `grep 'reached required accuracy' <dir>/OUTCAR` (absent ⇒ not converged)

  - `grep -E 'energy  without|FORCES' <dir>/OUTCAR` for NaN / `+++` / absurdly large values.

### Confidence and what I'd check next

High confidence that symmetry (`ISYM`) is the cause; medium that it's *solely* that vs. a POSCAR edit slip — both only bite the defected cell, so verify both. To pin it down, please share: the **tail of the crashing OUTCAR + the job stderr** (the exact `us.F` line and the line printed just before the segfault), the **INCAR** (`ISYM`, `VCA`, `NELECT`, `IBRION`, `NSW`), and the **POSCAR header** (species line + counts) for the vacancy structure. If the crash persists with `ISYM=0` and a clean POSCAR, the OUTCAR's last lines will tell us whether it's instead a real-space projector issue (`LREAL`) or a per-rank memory segfault — the latter clears when you double the nodes.
