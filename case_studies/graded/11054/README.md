# Topic 11054 — SSNEB for 2D material

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> Amazingly good response from AI.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**leiwy** (2020-11-08 22:37):

Dear experts,

In VASP, we can optimize the lattice (only xy direction) and atomic positions of a 2D material through modifying the constr_cell_relax.F file. However, it seems this trick does not work if we turn the SSNEB on to study the phase transition of a 2D material (the z direction would be optimized as well during the run). I wonder whether it is possible to use SSNEB method to study the 2D phase transition (without changing the lattice along z direction).

Best

Leiwy

---

**leiwy** (2020-11-09 18:58):

Dear Graeme,

Thanks a lot for your reply. I will look into ASE for a solution following your first suggestion. As for the second one, it seems using NEB method provided by VASP itself works for 2D material if the constr_cell_relax.F is modified. But I'm also interested in if we can realize it by using ssneb provided by VTST code (LNEBCELL=T). Please shed some hints on how to do that, and I believe this can help a lot of researchers working on 2D phase transitions.

Best regards

Leiwy

---

**leiwy** (2020-11-09 19:33):

Dear Graeme,

By the way, I found a twodim_flag hiding in chain.F which set the z component of stress to zero. So this function has already been realized in VTST code?

Best 

Leiwy

---

**leiwy** (2020-11-09 22:07):

Dear Graeme,

Thanks a lot for the efforts from you and your colleagues. We appreciate it so much!

Best wishes

Leiwy

## Expert answer (forum ground truth)

**graeme** (2020-11-09 14:50):

Hi Leiwy,

I think that the best approach might be to run vasp through the ASE code.  Vasp can be used as a calculator in ASE and the SSNEB is implemented there as well.  ASE has a great deal of flexibility in terms of constraints that be applied for the calculations.

It would also not be difficult to modify the SSNEB code in vasp for 2D materials.  This would likely be very similar to the modification in constr_cell_relax.F.  One could either zero any change of the cell in z, or zero the stress component along z.  I think that a '2D' tag could be used to turn this option on.  Let me know if you want to proceed along these lines, and if you need any help - again, it should not be hard.

Graeme

---

**graeme** (2020-11-09 21:14):

Wow, yes, it is already implemented!  This has to be thanks to Penghao Xiao.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**The `constr_cell_relax.F` patch can't work for SS-NEB — it's bypassed. SS-NEB builds its cell step from the stress tensor *inside* the VTST `neb.F` source, not through VASP's native cell-constraint hook, so the stress it actually integrates is never masked and every lattice component (including z) stays free. To hold z you must zero the z-coupled stress components in `neb.F` itself — or run SS-NEB through TSASE and apply a cell mask. So yes, a 2D phase transition with fixed z is doable with SS-NEB; you just have to constrain it in the right place.**

### Why your patch does nothing on the band

`constr_cell_relax.F` lives in VASP's ordinary stress→cell-update path used for `ISIF≥3` relaxation. When `LNEBCELL=.TRUE.`, SS-NEB takes over: it forms its own generalized force vector (atoms + lattice, weighted by `JACOBIAN`) from the stress *within* `neb.F` and integrates the cell there. Your VASP-side patch never touches that copy of the stress. The diagnostic tell, if you want to confirm: the patch **holds in a plain `ISIF=3` relaxation but has no effect on the band** — that's the bypass, not a bad build.

### Where to constrain it instead (the `neb.F` patch)

Grep the VTST `neb.F` for the stress-zeroing loop *by name* — `stress(i,j)=0._q` lines — never a quoted line number (it drifts between VASP 5.x/6.x; a VASP 5.3.5-era report put it near line 236, but verify). SS-NEB stores the stress **upper-triangular**: the lower triangle `(2,1),(3,1),(3,2)` is already pre-zeroed, so the six *active* cell DOF are the upper elements:

`(1,1) (1,2) (1,3) (2,2) (2,3) (3,3)`

For a standard 2D slab (a, b in-plane, **c along z**), keep only the in-plane lattice free and freeze everything involving z by adding:

```
stress(1,3) = 0._q   ! a–z shear
stress(2,3) = 0._q   ! b–z shear
stress(3,3) = 0._q   ! c (z) length
```

That leaves `(1,1),(1,2),(2,2)` — the full in-plane (xy) lattice — free. Rebuild, then **verify on a short run**: diff `CONTCAR` vs `POSCAR` cell vectors (or OUTCAR `direct lattice vectors`) — the c-length and z-tilts must not move, the xy block should.

>

Caveat: this mapping assumes c is the z (vacuum) axis and the cell is oriented so z-coupling lives in those three components. If your cell is non-orthogonal, identify which components carry z first.

### No-Fortran alternative

Run SS-NEB through **TSASE** (ASE-native cell-enabled NEB). It exposes a cell filter/mask, so you can freeze the z components directly — no recompile.

### Two things that will bite you on a 2D/vdW slab regardless

1. **The variable cell is under-constrained here.** A 2D/layered slab pays almost no energy to change its z-length or tilt, so off-diagonal shear is nearly degenerate with atomic displacement — SS-NEB from a *linear-interpolation* start tends to oscillate or crawl without dropping the force. Freezing z actually removes exactly those soft DOF, so your constraint *helps* convergence. Still, **bootstrap**: pre-converge a fixed-cell NEB (`LNEBCELL=.FALSE.`, `ISIF=2`, atoms only) for a sane path, *then* re-enable SS-NEB (`LNEBCELL=.TRUE.`, `ISIF=3`, `IOPT=3`) restarting from those CONTCAR images.

2. **Cell-relaxation precision.** The PAW basis isn't re-adjusted as the cell changes, so use `ENCUT ≈ 1.3×ENMAX` and `PREC=High`, with a denser k-mesh than a fixed-cell run needs — otherwise the in-plane barrier carries a Pulay/basis-incompleteness error.

### Before you patch anything — confirm the build

`LNEBCELL` (SS-NEB) is a VTST feature (≈2.04+). Grep your OUTCAR init block for `LNEBCELL` and the `VTST: version` banner — if the tag is silently absent, the patch predates SS-NEB and no `neb.F` edit will matter until you upgrade.

**Confidence:** high on the root cause (constr_cell_relax bypass) and the patch location/components; the exact component indices assume c‖z, which I'd confirm against your POSCAR. If you paste your endpoint POSCAR cell block and `grep -i 'lnebcell\|isif\|iopt\|encut\|prec' INCAR` plus the OUTCAR VTST banner, I'll pin the exact `stress(i,j)` lines and check the convergence deck.
