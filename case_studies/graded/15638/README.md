# Topic 15638 — What does it mean &quot;A&quot; in the Reaction Coordinate axis.

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> The AI response is sensible.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**Sam** (2023-11-09 09:36):

Hello Friends,

After calculation by CINEB, we can obtain the reaction path plot (Energy vs Reaction Coordinate). My question is regarding the Reaction Coordinate  axis. It mentions in the brackets "A", this means the unit of the Reaction Coordinates axis or what else? If the A is unit, A should be Å. So could you please explain me what does it mean "A" and the unit of the Reaction Coordinate axis.

Thank you.

---

**Sam** (2023-11-10 08:46):

Thank you so much, Prof. Graeme.

## Expert answer (forum ground truth)

**graeme** (2023-11-09 11:48):

Angstrom.

---

**graeme** (2023-11-10 11:21):

You can change it on line 3 of nebplot.gnu , in the vtstscripts , if you want.

set grid

set pointsize 2

set xlabel "Reaction Coordinate "

set ylabel "Energy "

set nokey

set terminal postscript eps color

set output "mep.eps"

plot "spline.dat"  u 2:3 w l lt 1 lw 2.4 , \

     "neb.dat" u 2:3 w p lt 3 lw 3.0 pt 7 ps 1.3

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Yes — "A" is the unit, and it means Ångström (Å). The Reaction Coordinate axis is a *distance*: the cumulative path length in Å traveled along the minimum-energy path from the reactant to each image.** The plotting script just renders "Å" as the ASCII letter "A" (gnuplot/PostScript in the VTST tools can't emit the Å glyph), so it's exactly the Å you expected.

### What that distance actually is

It is **not** a single bond length or one atom's displacement. It is the *cumulative inter-image distance* accumulated from image `00` (reactant) up to each image — i.e. the running sum of the structural change of the whole system along the band.

This comes straight from how the VTST post-processor builds the plot. `nebbarrier.pl` (the engine behind `nebresults.pl`/`nebspline.pl`) writes `neb.dat` with columns:

```
index   cum_dist   rel_energy   force   dirname
```

where `cum_dist` is your x-axis (`docs/vtst/scripts.md`). For each step from one image to the next it computes the distance between the two structures and adds it to the running total:

- **Default:** the RMS Cartesian distance between adjacent images (via `dist.pl`) — the root-mean-square of every atom's displacement between the two images.

- **`-alt_dist` flag:** that displacement projected onto the average force direction instead of plain RMS.

- **Solid-state NEB (`LNEBCELL`):** VASP's own reported `NEBCELL: distance`.

And the units are stated explicitly in the docs: **distance/displacement = Å**, energy = eV, force = eV/Å (`docs/vtst/scripts.md`, "Units").

### Practical reading

- The total width of your x-axis = the total RMS atomic rearrangement from reactant to product, in Å. For a reaction where one atom moves ~1.5 Å and the rest barely move, the axis will span well under that, because RMS averages over *all* atoms (or all *free* atoms).

- The spacing between points is the per-step image distance — uneven spacing (especially around the climbing image, which is exempt from the springs) is normal, not an error.

- Because it's a *summed path length*, the value at the product is path-dependent and not a physical bond distance — treat it as "progress along the MEP," with Å as the natural unit.

Confidence: high — confirmed against the bundled VTST docs (`docs/vtst/scripts.md`: `neb.dat` column definition and the Units line). If your plot's "A" looked suspicious for another reason (e.g. an oddly small or zero axis span), send me your `neb.dat` and I'll check whether the distances were computed correctly.
