# Topic 15625 — non-linear interpolation

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> Good answer from AI.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**pkluijtmans** (2023-10-09 09:19):

Hi!

I am doing research into plastic crystals, where anions exhibit rotational freedom. I want to use NEB to determine the energy barrier for such rotations. But nebmake.pl only interpolates linearly and therefore cannot imitate a rotation of a molecule. I tried to create intermediate images with nebmake.pl and nebavoid.pl but I am not satisfied with the results. Is there a nice way to create images for rotation? Thanks in advance!

---

**pkluijtmans** (2023-10-09 10:08):

Thanks for your quick answer! I am going through the scrips, but nebmake.py is not there. Where can I download the script?

## Expert answer (forum ground truth)

**graeme** (2023-10-09 10:01):

Try using the IDPP method, which is on by default if you use the nebmake.py script.

---

**graeme** (2023-10-09 12:09):

it is the vtstscripts : https://theory.cm.utexas.edu/vtsttools/scripts.html   (download the entire collection)

## The graded AI answer (SaddleAgent (with Opus 4.8))

**The problem is the interpolator, not your inputs. `nebmake.pl` interpolates linearly in Cartesian space — every atom travels the straight chord between its start and end position, so a rotating anion *contracts* (bond lengths shrink toward the rotation center) at the intermediate images. `nebavoid.pl` only pushes too-close atom pairs apart under a repulsive potential; it patches collisions but never restores the rotation, so the band stays unphysical. The fix is distance-preserving interpolation: use IDPP (`nebmake.py`), and for large-angle / symmetric anions seed the band with an explicit rigid-body rotation.**

### Why linear interp fails for a rotation

For a rigid rotation the bond lengths are identical at both endpoints, but the straight-line path between corresponding atoms cuts *through* the arc. At the midpoint the molecule is maximally compressed/sheared — exactly the garbage you saw. `nebavoid.pl` (per its doc: a steepest-descent pairwise-repulsion relax that just enforces a minimum interatomic distance) can only space those atoms back out; it has no notion of "this should be a rotation," so the result is still wrong.

### Fix 1 — IDPP (try this first)

IDPP (image-dependent pair potential, Smidstrup et al., *J. Chem. Phys.* **140**, 214106 (2014)) optimizes the interior images so their *pairwise distance matrix* interpolates smoothly. For a rigid rotation the intramolecular distances are constant at both endpoints, so IDPP's target is "hold every bond at its real length" — precisely what linear interp violates. It's built into the VTST python builder:

```
nebmake.py POSCAR_initial POSCAR_final N
```

(IDPP is the default; `-NOIDPP` would fall back to linear. Internally it runs `neb.interpolate('idpp', mic=True)`.) **Then check the band movie and the bond lengths in the middle image.**

One caveat worth knowing: IDPP's default optimizer tolerance (`fmax ≈ 0.05 eV/Å`) is loose and can exit early, leaving the path barely moved from linear. If the rotation still looks compressed, tighten it — in ASE directly:

```
from ase.mep.neb import idpp_interpolate
idpp_interpolate(images, fmax=0.01, steps=1000, mic=True)
```

### Fix 2 — rigid-body rotation seed (robust for large / symmetric rotations)

IDPP constrains only pair *distances*, and a reflection/collapse can satisfy the same distance targets — so for a ~180° flip of a symmetric anion (BF₄⁻, PF₆⁻, NO₃⁻, …) it can still pick a non-rotational path. The bulletproof route is to build the images by physically rotating the anion about its axis at evenly spaced angles — bond lengths and rotational sense are then exact by construction:

```
from ase.io import read, write
import os

initial = read('POSCAR_initial', format='vasp')
mol   = [...]          # 0-based indices of the rotating anion's atoms
axis  = (0, 0, 1)      # its rotation axis
angle = 90.0           # total rotation, degrees (init -> final orientation)
N     = 8              # interior images

for i in range(N + 2):
    img = initial.copy()
    sub = img[mol]
    sub.rotate(angle * i / (N + 1), axis, center=sub.get_center_of_mass())
    img.positions[mol] = sub.positions
    d = f'{i:02d}'; os.makedirs(d, exist_ok=True)
    write(f'{d}/POSCAR', img, format='vasp', direct=True)
```

Optionally run IDPP afterward to let the *surrounding* lattice relax around the rotated anion while the molecule itself stays rigid.

### Three things that will otherwise bite you

- **Do NOT set `remove_rotation_and_translation=True` (NEB-TR).** That option removes overall molecular rotation between images — i.e. it strips out the exact coordinate whose barrier you're trying to measure.

- **Endpoints:** two *distinct* stable orientations (rotated by the inter-site angle), both relaxed in the **same fixed cell** (`ISIF=2` — never relax the cell for an NEB). For a symmetric anion the two orientations are symmetry-equivalent, so they'll be degenerate in energy — expected; CI-NEB will find the saddle between them.

- **Image count:** a rotation is a large-amplitude curved path — budget generously (~1 image per ~10–15° of rotation, ≥6–8 interior images) or the path stays under-resolved.

### What I'd want to confirm

Share the anion identity, the rotation axis/angle, and your two endpoint POSCARs, and I'll check that the generated band actually preserves the bond lengths through the middle image (the single fastest tell of whether the interpolation is physical). Confidence is high that the linear interpolator is your root cause — that's the textbook signature of "nebmake.pl + nebavoid.pl can't make a rotation."
