**Bottom line: The shallow minima are physical in kind — HSE localizes charge that GGA spuriously smears out, and that symmetry-breaking genuinely creates several nearly-degenerate wells (GGA's single smooth well is the artefact, not the other way round). But in the files you attached the ~0.01 eV differences are not yet trustworthy: the SCF is not converging for your interior images, so part of what you're seeing is electronic noise sitting at the exact energy scale of the wells. Fix the electronics before deciding what is physical.** You were right that TIMESTEP and the optimizer are not the problem — don't touch those.

## What the files actually show

Per-image final energies (relative to image 00, `free energy TOTEN`):

| image | ΔE vs 00 (eV) |
|---|---|
| 00 (initial endpoint) | 0.000 |
| 01 | +0.005 |
| 02 | **−0.008** |
| 03 | +0.026 |
| 04 (final endpoint) | +0.057 |

So image 02 genuinely sits *below* your initial endpoint, and 04 is the highest point on the whole path. That is exactly the "endpoint isn't a local minimum / lower configs along the MEP" you reported — there is a real intermediate well in the band.

**The critical finding you haven't accounted for:** the interior images are running on non-self-consistent forces. You have `EDIFF=1E-10` with `NELM=20` for HSE06, and the SCF simply never reaches that target in 20 electronic steps. Counting the aborted electronic loops:

- image 01: SCF unconverged in **10 of 13** ionic steps
- image 02: unconverged in **10 of 13**
- image 03: unconverged in **13 of 13** (never once reached EDIFF)
- endpoints 00 and 04: fine

The ionic loop then reports "reached required accuracy" because the *projected forces* dipped below `|EDIFFG|=0.01`, but those forces come from a density that never converged. Noise from a non-self-consistent density lands right at ~0.01 eV / ~0.01 eV/Å — the same size as the wells you're trying to resolve. That is your "sketchy convergence." (VTST 4.1 is properly linked in vasp.6.4.2, so the method itself is fine.)

**Fix the electronics first:**
- `NELM = 100` (20 is far too low for HSE)
- `EDIFF = 1E-6` (1E-8 at the tightest) — `1E-10` is unreachable here and is the reason SCF bails every step; achievable-and-actually-reached beats nominally-tight
- consider `ALGO = Damped` (keep `TIME=0.4`) or `ALGO = All` — you're on `IALGO=38` (ALGO=Normal), which is often the least stable choice for hybrids
- `LCLIMB = .TRUE.` — you have it `.FALSE.`; it's the VTST default and costs nothing. Without a climbing image a small/narrow saddle falls *between* images and reads as barrier-less, which is part of why your barrier "doesn't show up."

## Your three questions

**1. Physical or an HSE artefact?** Both framings are partly right, so separate them:
- *In kind — physical.* Hybrids remove GGA's self-interaction/delocalization error, so a hole/electron/off-center relaxation that GGA spreads over many equivalent sites localizes onto one (self-trapped-hole / polaron-type behaviour, very common in wide-gap ionic solids like LiF). The resulting symmetry-broken configurations are real nearly-degenerate wells. GGA's featureless surface is the *under*-structured one.
- *Numerically.* DFT total-energy *differences* in one fixed cell can be resolved well below 0.01 eV **if the SCF is converged** — so this is not a "DFT can't see 0.01 eV" problem. Right now your SCF isn't converged, so the ordering (e.g. 02 below 00) is not yet reliable. Re-run with the fixes above and check whether the ordering is stable.
- *Model-dependence.* The depth — and sometimes the very existence — of these wells depends on the exact-exchange fraction. Your `AEXX=0.25` is a choice; a different fraction can reshape a 0.01 eV landscape. So "well X is 0.01 eV below well Y" is a functional-dependent statement — report it as such, and if the ordering matters, test sensitivity to AEXX.

**2. Pure DFT for endpoints; hybrids in NEB?** There's no fundamental incompatibility — CI-NEB is force-method-agnostic and VTST handles HSE fine. The real constraints:
- **Don't mix levels for anything you report.** If the intermediate wells only appear at HSE, then a PBE path has the *wrong topology* — PBE will miss exactly the intermediates you care about, and PBE geometries may not even be minima at HSE (which is precisely what you saw: a PBE-converged NEB grows new minima when re-run at HSE). Never relax at PBE and take HSE single points across a path; the energies aren't comparable.
- **Correct workflow:** use PBE only to *pre-relax/seed* geometries (cheap), then re-relax the endpoints **and** run the whole band at HSE, consistently. Expect new intermediates to appear — that's the physics, not a failure.

**3. Loose NEB to scout the mechanism?** Yes — that's a standard, legitimate strategy, with two case-specific caveats:
- Loosen `EDIFFG` to about `-0.05` to `-0.1` eV/Å to get the qualitative atomic motions cheaply, then tighten only the segment you care about. Keep it **negative** — VTST NEB requires a negative EDIFFG (force criterion), per the EDIFFG docs; a positive value switches to an energy criterion the band methods don't accept.
- But tightening alone will **not** collapse a multi-well band into one clean barrier, because the extra minimum (image 02) is real. The right move is to **split the path at the intermediate**: relax image 02 as its own minimum, then run two short NEBs, 00→02 and 02→04. Each has a single small barrier and converges far more easily than one band dragged across several wells. Also add images — a shallow, structured path wants ~1 image per 0.5 Å; three interior images spanning multiple wells is too coarse to resolve these small saddles.

**Confidence:** high on the SCF diagnosis and the energy profile (both direct greps of your OUTCARs), high on the HSE-localization physics (well-established for ionic insulators). What I'd check next after you re-run with converged SCF: whether image 02 stays below endpoint 00, and whether the two split NEBs (00→02, 02→04) each give a clean single saddle. If you send the endpoint POSCARs I can check the atom correspondence and vacuum/cell consistency too.
