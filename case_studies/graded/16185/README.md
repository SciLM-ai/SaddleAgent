# Topic 16185 — NEB: force dissociation

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> Here I think the AI did a better job than the expert.  I don't see the files, but I see in the question that the user is suggesting to remove species from one side of an NEB, which does not work, as the AI points out.  The expert interpreted this as asking about a band where a ligand was spatially 'removed' from the metal, but upon a second reading, I think the AI is correct in assuming that the user is actually suggesting to remove the ligand, which will not work for an NEB calculation.  Good job AI!

## Original question

**jess_white** (2025-05-25 22:32):

Hi,

I apologise in advance if this is a super silly question but essentially I want to see the activation barrier for removing a metal from a ligand. What I am doing is having the initial starting point (with the metal attached to the ligand) and then the final shot is the metal dissociated from the ligand. For this last frame I have just removed the metal so its dissociated. Is this really bad practice or still reasonable? 

Thanks,

Jess

---

**jess_white** (2025-05-29 08:02):

Thanks so much :)

## Expert answer (forum ground truth)

**graeme** (2025-05-26 11:51):

That is just fine.  If the metal is sufficiently far from the ligand in the final state, you should be able to relax it, as well as the initial state.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Don't delete the atom — that breaks the NEB at the most basic level, and "dissociation" isn't the same as "deletion." Keep the metal in the final frame and move it far from the ligand instead. And before you commit to a full NEB, check whether there's even a barrier to find — metal–ligand removal is very often barrierless.**

Not a silly question at all — this is exactly the thing to sort out *before* spending core-hours.

## Why deleting the atom doesn't work

NEB builds the band by interpolating **each atom's position** between your initial (IS) and final (FS) endpoints — there has to be a one-to-one atom correspondence. The builder enforces this directly: `nebmake.pl` "checks both files share atom counts/types, computes the PBC-aware difference, and steps linearly in Cartesian space" (the per-type atom-count check is enforced). If your FS has one fewer atom than your IS, there's no atom for the metal to map onto, and the build fails (or produces garbage). The same is true for the IDPP builder `nebmake.py` and for ASE NEBs. So this isn't "bad practice" so much as "the method can't run."

The physical point underneath: the reaction coordinate for removal is the **metal–ligand distance increasing**, not the metal blinking out of existence. The FS is the metal still in the cell, just pulled far away and re-relaxed.

## What to do instead

1.

**Build the FS with the metal present but displaced.** Take your bound structure, move the metal to a large separation from the ligand (as far as the cell allows — make sure there's enough vacuum that its energy has plateaued and it isn't talking to a periodic image), and fully relax it. Same atom count, same atom ordering as the IS. Then `nebmake.py IS_POSCAR FS_POSCAR <nimages>`.

2.

**Decide the chemistry explicitly** — this dominates the answer:

  - **Charge state**: does the metal leave neutral or as a cation (leaving the ligand charged)? A charged fragment in a periodic cell needs care (compensating background / `NELECT`), and the two endpoints' energies are only comparable if you've fixed this.

  - **Spin state**: a separated metal atom/ion often has a different ground-state spin than when bound. If endpoints differ in spin, you'll need explicit per-image `MAGMOM` — otherwise the band lands on inconsistent magnetic minima and the barrier comes out wrong.

3.

**First check whether a barrier even exists.** Bond-breaking/desorption is frequently **barrierless** — the energy just rises monotonically to the dissociation asymptote, and the reverse (association) has no barrier. If that's your case, NEB adds nothing: the "activation energy for removal" is simply the **binding/dissociation energy**, ΔE = E(separated) − E(bound), from your two relaxed endpoints. So do a cheap **relaxed distance scan** first: fix the metal–ligand distance at a series of increasing values, relax everything else, plot energy vs. distance.

  - **Monotonic rise** → no saddle; report ΔE as the barrier, no NEB needed.

  - **A clear maximum** → that's a real TS (a "late"/reorganization barrier). *Now* run CI-NEB (`LCLIMB=.TRUE.`) seeded across that maximum, and confirm with a frequency check (exactly one imaginary mode along the metal–ligand stretch).

**Confidence:** high on the mechanical point (same atoms required) and on "scan before NEB."

If you can share your IS `POSCAR` (and the `POTCAR` order / whether the metal is meant to leave charged), I'll tell you exactly how to construct the FS and whether your system is likely to have a real saddle or just a binding-energy climb.
