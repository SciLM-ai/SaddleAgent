# Topic 15608 — ZPE corrected Energy barrier calculations

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> AI is going crazy here.  It is true that there will never precisely be a zero mode, but near zero modes are not appropriate for the harmonic approximation to zero point energy.  Small negative modes will make the script give an error.  The problem is really one of physics and not computer science, and the AI missed it completely.

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**flake** (2023-08-22 04:15):

Dear All,

I ran Ci-NEB for H migration energy barrier calculations and got the results. In the second step, I need zero point energy corrected energy barrier values so I ran dynamical matrix calculations using structures from my NEB calculations. Since my supercell contains 54 iron atoms and 1 hydrogen, I included 55 atoms for the generation of the DISPLACECAR  file with a displacement of 0.05. Moreover, I have subdirectories numbered 01 to 03 where 01 is the initial structure and 03 is the saddle point. After the calculation was finished, first I ran dymmatrix.pl for initial and saddle point OUTCAR files, and then I used "dymeffbar.pl" script to see the final results, however,  I got an error "Illegal division by zero at ./dymeffbar.pl line 81.". I think the problem occurred since I have so many 0 values in my freq.dat files but I am not sure. Could you please help me?

## Expert answer (forum ground truth)

**graeme** (2023-08-22 08:07):

I think that you are right.  That ZPE script just calculates quantum harmonic corrections to TST, so zero or negative modes will lead to a divergence.  If you can identify 3 translational modes at both the reactant and saddle, as well as (perhaps) 3 rotational modes, you can simply remove them and run the script with a reduced set of only positive vibrational modes.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**The crash is dymeffbar.pl dividing by a zero‑frequency mode, and you have those zero frequencies for two compounding reasons: (1) the dynamical‑matrix run almost certainly did not evaluate every displacement — for a 55‑atom DISPLACECAR you have 165 DOF, so the run needs `NSW = 166` and a tiny `EDIFFG`, or VASP quits early and leaves most Hessian rows (hence most frequencies) exactly zero; and (2) displacing all 54 Fe + H injects 3 acoustic (rigid‑translation) zero modes plus extra near‑zero/imaginary modes that this script cannot handle anyway. The real fix is to regenerate a small, localized DISPLACECAR (the H atom and its first Fe shell only) and rerun with the correct `NSW`/`EDIFFG`.** Confidence: high on the mechanism; I'd confirm which of (1)/(2) dominates with three greps below.

### Why it divides by zero

`dymeffbar.pl` builds the harmonic/Vineyard quantities from the mode list — the prefactor is the product of frequency ratios `∏ (ω_min,i / ω_saddle,i)` and the quantum/Wigner terms carry `1/sinh(ħω/2kT)`‑type factors. **Both blow up the instant any mode frequency is 0.** The script also assumes the saddle's single imaginary mode is the *first* entry and skips exactly one (per the VTST dynmat docs); it has no logic to drop acoustic zeros or extra imaginary modes. So any genuine zero in the spectrum → "Illegal division by zero."

Your own observation — "so many 0 values in freq.dat" — is the tell. A *complete* full‑cell Hessian would show only ~3 zeros (the acoustic modes). *Many* zeros means most displacements were never computed, which points straight at `NSW`/`EDIFFG`.

The authoritative dynmat runbook is explicit on both points:

- `NSW = DOF + 1` — "one force call at equilibrium plus one per displaced degree of freedom." For you: 165 + 1 = **166** per directory.

- "If all frequencies come out zero, check `EDIFFG` in the INCAR (set it tiny so VASP doesn't stop early). **The number of force calls should equal `NSW`.**" Required values: `EDIFF=1E-8`, `EDIFFG=-1E-8`, `ICHAIN=1`, `IBRION=3`, `POTIM=0`.

### Confirm in 60 seconds (run in your `01` and `03` dirs)

1. `grep -E 'NSW|EDIFFG' INCAR` — is `NSW` 166? Is `EDIFFG` ≈ `-1E-8`? If `NSW` is small or `EDIFFG` is a normal value like `-0.02`, that's the cause.

2. `grep -c 'TOTAL-FORCE' OUTCAR` — number of force evaluations actually done. It must equal `NSW` (166). Fewer ⇒ the run truncated and the missing DOF are your zero modes.

3. In `freq.dat`, count the imaginary flags (4th column = `1`): the **minimum (01) must have 0**, the **saddle (03) exactly 1**. Anything else means the spectrum is contaminated.

### The fix (recommended path — localized Hessian)

For an H‑migration ZPE correction you should *not* shake all 54 Fe. The ZPE difference is dominated by the light H; heavy‑Fe contributions are tiny and largely cancel between IS and TS. Holding the lattice fixed also removes the rigid‑translation zero modes entirely (no global translation when the substrate is frozen), so the spectrum comes out clean: 0 imaginary at the minimum, exactly 1 at the saddle.

1. Regenerate DISPLACECAR around H only (or H + first Fe shell), e.g.
`dymselsph.pl POSCAR <H_atom_index> 2.5 0.01` (atoms within 2.5 Å of H), or
`dymseldsp.pl <initial_POSCAR> <saddle_POSCAR> <N> 0.01` (the N most‑displaced atoms IS→TS).
Use **~0.01 Å**, not 0.05 — 0.05 is ~50× the recommended step and adds anharmonic contamination; converge the frequency vs. step if in doubt (`dymanalyze.pl`).

2. Recompute `NSW = (number of displaced DOF) + 1` for the *new* DISPLACECAR, keep `EDIFF=1E-8`, `EDIFFG=-1E-8`, `ICHAIN=1`, `IBRION=3`, `POTIM=0`, and carry over all electronic tags from the NEB.

3. Rerun VASP in `01` and `03`, then `dymmatrix.pl`, and verify the imaginary counts (0 and 1).

4. Re‑run the barrier post‑processing.

One more thing to check before you re‑run dymeffbar: in the VTST suite `dymeffbar.pl`/`dymrate.pl` consume the **ω² eigenvalue file (`eigs.dat`)**, not the cm⁻¹ `freq.dat`. Open lines ~70–90 (`sed -n '70,90p' dymeffbar.pl`) to see exactly what line 81 divides by and which file it reads — if you paste those lines I'll pin the exact denominator and the correct invocation. The call is `dymeffbar.pl <Ti> <Tf> <dV> <min eigs.dat> <saddle eigs.dat>` with `dV` = your classical CI‑NEB barrier in eV.

If you'd rather keep the full‑cell Hessian, you can't feed it to `dymeffbar.pl` as‑is — you'd have to strip the 3 acoustic zeros (and any spurious extra imaginaries) by hand first. The localized DISPLACECAR is the standard and far less error‑prone route.

What would let me confirm rather than infer: the `01`/`03` `INCAR`, the `grep -c 'TOTAL-FORCE' OUTCAR` counts, and the head of one `freq.dat` (or `eigs.dat`).
