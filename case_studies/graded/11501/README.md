# Topic 11501 — nebmake.pl bug?

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> Good response from AI.

## Files

`files/` — the complete upload (3 files; `POTCAR` excepted, for licensing).

## Original question

**kai** (2020-12-03 14:37):

Hi, everyone,

I have been using nebmake.pl to prepare my files, and everything went on fine until recently. Simply put, nebmake didnt interpolate good intermediate images any more.

# image 00: POSCAR

  0.6205393683339545  0.3748186251700154  0.6113134379103631 T T T

  0.4407191996091184  0.3753464715751533  0.6109833865746312 T T T

#image 02: POSCAR

  0.6205250119801456  0.8749946587628363  0.6126018270732655 T T T

  0.4404841117364926  0.8751503266829158  0.6121692792622382 T T T

But by keying in nebmake.pl 00/POSCAR 02/POSCAR 1, i got 01POSCAR as

  0.6205321901570500  0.1249066419664260  0.6119576324918160 T T T

  0.4406016556728080  0.6252483991290350  0.6115763329184321 T T T

It seems that y values are not correct, but i cannot pinpoint where things went wrong. They are not so close to the edge of the box! 

Help! I am using vtst-scripts947

I am attaching the files, and many thanks

---

**kai** (2020-12-09 02:12):

got it and thanks

---

**rachita_panigrahi** (2021-01-22 22:00):

while i m calculating NEB by using nebmake.pl script..so its showing (In vasp.pm::read_poscar, cannot open POSCAR00)...so can u help me...thanks in advance

---

**Xingru Tan** (2021-07-01 02:09):

I encountered the same problem. When I am trying to use the script nebmake. Error message appears(In vasp.pm::read_poscar, cannot open 'filename'). Can someone please help me?

---

**Xingru Tan** (2021-07-01 22:03):

rachita_panigrahi wrote:

> while i m calculating NEB by using nebmake.pl script..so its showing (In

> vasp.pm::read_poscar, cannot open POSCAR00)...so can u help me...thanks in

> advance

same error solved. Mine is due to typing the wrong dir of the two POSCAR file in the command. Double-check the command.

## Expert answer (forum ground truth)

**graeme** (2020-12-04 14:05):

The script is working as it should.  The issue is that you are moving almost exactly 1/2 way across the box in the y-direction between images 0 and 2.  In our script, we find the shortest path between the initial and final states relative to the periodic boundary conditions.  For the first atom, it is slightly shorter to go along +y but for the second, it is closer along -y.  If you just move the molecule a little closer between the 00 and 02 images, then it will interpolate as you expect it to.

## The graded AI answer (SaddleAgent (with Opus 4.8))

I've confirmed the cause exactly. This is a minimum-image artifact in `nebmake.pl`, not a bug or a version regression.

## Bottom line

**`nebmake.pl` interpolates each atom along the *shortest* (minimum-image) path, and your two Ag atoms move ≈ exactly half the box in y (Δy ≈ 0.500, ≈ 7.68 Å of the 15.36 Å cell). One atom's displacement lands just over 0.5 and the other just under, so the minimum-image convention sends them in *opposite* y-directions — one through y≈0.625 (direct), one through y≈0.125 (wrapping across the cell). That split is your "bad" image 01.** Nothing to do with atoms being near the box edge, and nothing wrong with vtst-scripts947.

## The evidence (your numbers, exactly reproduced)

`nebmake.pl` computes a PBC-aware difference (`pbc_difference` = minimum image) and steps linearly by `diff/(nim-1)` (docs/vtst/scripts.md). Minimum image means: displacement `Δ → Δ − round(Δ)`, i.e. always take the branch with |Δ| ≤ 0.5.

| atom | y in 00 | y in 02 | raw Δy | > 0.5? | min-image takes | → image-01 y |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.37482 | 0.87499 | +0.50018 | yes | wraps to −0.49982 | 0.12491 ✓ |
| 2 | 0.37535 | 0.87515 | +0.49980 | no | direct +0.49980 | 0.62525 ✓ |

Both computed midpoints match your `01/POSCAR` to the last digit. So the script did exactly what it's designed to do — your two atoms just straddle the 0.5 knife-edge, and at half-a-box the two directions are essentially the *same length* (~7.68 Å either way), so the choice is genuinely ambiguous and flips atom-by-atom.

That's also why it "broke recently": the script didn't change — your endpoints' y-displacement crept from comfortably under 0.5 to right at 0.5. (vtst-scripts947 is fine; no version/binary issue here — this is pure script geometry, deterministic.)

## Fix

**Immediate** — if you want both atoms going the direct way (through y≈0.625), just correct atom-1's y in the interpolated image. Linear interpolation gives the direct midpoint = 0.37482 + 0.50018/2 = **0.62491**. So `01/POSCAR` should read:

```
  0.6205321901570500  0.6249066419664259  0.6119576324918160 T T T
  0.4406016556728080  0.6252483991290350  0.6115763329184321 T T T
```

Now both Ag atoms travel together through y≈0.625.

**To make `nebmake.pl` do it automatically** (so you don't hand-edit every image): the script will *always* min-image atom 1 the wrap way as long as its raw Δy > 0.5. Push that displacement just under 0.5 by nudging the **endpoint** so the intended direction is the short one — e.g. raise atom-1's y in `00/POSCAR` from 0.3748186 to 0.3750 (a 0.003 Å change, negligible; re-relax if you're strict). Then Δy = 0.49999 < 0.5 and nebmake interpolates the direct way for both atoms. (Note: shifting the *origin* of the whole cell does **not** help — min-image depends only on `y_final − y_initial`, which is origin-invariant.)

**Worth a sanity check first:** this is a ~7.68 Å migration of *both* Ag atoms — half your cell in y (x and z barely move). If that large, direction-degenerate hop isn't what you intended, your endpoints are describing a half-cell translation and you should reconsider the cell/sites rather than the interpolation. If it *is* intended, the hand-edit above is correct.

One note on `nebmake.py` (IDPP): it won't reliably rescue this — its initial guess also uses `interpolate(mic=True)` (same minimum image), so it can land on the same ambiguous branch; IDPP mainly keeps pairwise distances physical, it doesn't choose the direction for you.

Confidence: high — the arithmetic matches your output exactly. If you can share `00/POSCAR`'s intended final site (or whether 02 is meant to be 00 translated by +½ in y), I can tell you whether the direct or wrapped path is the physically right one to keep.
