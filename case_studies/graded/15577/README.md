# Topic 15577 — Estimated opinion on the simulation results

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> The AI response is pretty useless, but there is insufficient data in the question to give a useful reply.

## Original question

**Supracrystal** (2023-06-21 09:25):

Hello

I am trying to find activation barriers to study the diffusion of interstitial atoms along grain boundaries in iron. If your time permits, could you take a look at the preliminary results and formulate an opinion on how well the simulation was performed. Thanks for your time.

---

**Supracrystal** (2023-06-21 09:41):

Dear Prof, thank you very much.

## Expert answer (forum ground truth)

**graeme** (2023-06-21 09:37):

It looks good to me; I don't see any problems.

## The graded AI answer (SaddleAgent (with Opus 4.8))

**I can't actually assess the run yet — no files came through with your message, and there are none on disk for me to grep.** To review "how well it was performed" I have to see the deck and the output, not a description. Below is exactly what to send and the specific things I'll scrutinize, ranked by what most often goes wrong for *this* class of problem (a magnetic Fe NEB on a low-symmetry grain-boundary cell).

## What to send

Minimum, for the NEB main directory plus the two relaxed endpoints:

- **`INCAR`** (the NEB INCAR, and the endpoint-relaxation INCAR if different)

- **`KPOINTS`** and the first ~10 lines of **`POTCAR`** (`grep TITEL POTCAR`)

- **`neb.dat`** (or `nebef.pl` output) and a directory listing `ls -d [0-9][0-9]/`

- The **tail of one image's `OUTCAR`** (last ~50 lines) and `grep 'reached required accuracy' */OUTCAR`

- `grep mag */OUTCAR` piped output, or each image's `OSZICAR` tail — this is the big one for Fe (see below)

- If you've done the saddle confirmation: the **frequency `OUTCAR`** + its selective-dynamics block

Tell me the **VASP and VTST/vtstscripts versions** too (`grep 'vasp\.' OUTCAR; grep 'VTST: version' OUTCAR`) — some fixes are version-gated.

## What I'll check, and the failure modes I expect for Fe-GB interstitial diffusion

1.

**Magnetism consistency across the band — the #1 silent killer here.** Fe is ferromagnetic, so the band is only valid if every image relaxed to the *same* magnetic branch. The classic artifact is one or two interior images settling on a different local moment, producing a spurious bump or even a negative/KRA barrier. I'll check `ISPIN=2` is set, that `MAGMOM` is initialized explicitly on all Fe (docs/vasp/ispin.md: required for Fe; init via MAGMOM), and that `grep mag */OUTCAR` shows a smooth IS→FS moment trend with no outlier image. If an image is off-trend with sane geometry, that's electronic, not structural.

2.

**Endpoints: same fixed cell, fully converged.** A GB supercell must not change shape between IS and FS — both should be relaxed at `ISIF=2` in one identical cell, then I diff the lattice-vector block of `00/POSCAR` vs the last image. Cell mismatch makes linear interpolation deform the slab and fakes a barrier. I'll also confirm each endpoint hit `reached required accuracy`.

3.

**It's actually CI-NEB and actually converged.** `LCLIMB=.TRUE.` for a real barrier; convergence judged by the **NEB-projected force** (`nebef.pl` max force / OUTCAR `FORCES: max atom`) reaching `|EDIFFG|`, not by hitting `NSW`. Per docs/vasp/ediffg.md, EDIFFG **must be negative** for VTST (e.g. −0.01 to −0.03); a positive or too-loose value is a common defect.

4.

**Optimizer legality.** `IBRION=3 POTIM=0` with `IOPT>0` (e.g. `IOPT=3`/QuickMin or `IOPT=1`/LBFGS). If I see `IBRION=2` (VASP CG), that's invalid for any force-projected method and I'll flag it immediately.

5.

**Image count / path resolution.** For a GB hop I want enough images that inter-image spacing is ~0.5–1 Å (≥4 for a reliable MEP, more if the path curves around the boundary). Too few → an under-resolved or multi-hump profile.

6.

**Metal electronic settings.** Smearing should be metallic — `ISMEAR=1` or `2` (Methfessel–Paxton) with a sensible `SIGMA`, or `0` (docs/vasp/ismear.md); `ISMEAR=-5` is wrong for NEB forces. I'll sanity-check `ENCUT`, k-mesh density for the supercell, and `LMAXMIX` (≥4 for Fe d-electrons if you're near DFT+U territory).

7.

**Saddle confirmation.** Whether you ran a frequency check yielding **exactly one** imaginary mode, and that its eigenvector points along the diffusion coordinate — without it, "converged" only means a local minimum on the current band, not a verified TS.

Send the files above and I'll work through these top-to-bottom and give you a concrete verdict with the exact tags to change. My current confidence is necessarily zero on the actual run — I'm flagging *where* I expect trouble, not asserting trouble exists.
