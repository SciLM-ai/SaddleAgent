# Topic 16201 — CI-NEB image asymmetry in vacancy migration in W

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> The AI is generally correct, but it is always annoying when it gets some statement fundamentally wrong, such as comparing an energy difference to a force criterion (EDIFFG = -0.03).  You can't compare numbers with different units.  So while this is basically correct, having a statement which is complete nonsense in there makes it look a little like AI slop.  (sorry AI)

## Files

No files were uploaded on this forum topic (text-only question).

## Original question

**ahterpet** (2026-02-05 00:47):

Hi all,

I’m running CI-NEB calculations to determine the minimum energy path for vacancy migration in pure W, and I’ve noticed some behavior that I don’t fully understand.

For a CI-NEB with 9 images, the 6th image is driven to the saddle point, with an energy of 1.679757 eV. Intuitively, I would have expected the 5th (middle) image to be the one promoted to the saddle point. What could cause this apparent asymmetry in image selection?

For a CI-NEB with 11 images, the 6th image (1.674699 eV) appears to sag between two higher-energy images: the 5th (1.679724 eV) and 7th (1.679920 eV). What might lead to this behavior?

For context, I’ve also performed CI-NEB calculations on the same system using 1, 3, and 5 images, and I did not observe any of these issues in those cases.

Unfortunately, I'm having difficulty attaching the project folders for the 9- and 11-image CI-NEB calculations, but I'll provide the INCAR tags here:

ADDGRID = .TRUE.

ALGO = Fast

EDIFF = 1e-05

EDIFFG = -0.03

ENCUT = 446.114

GGA = PE

IBRION = 3

ICHAIN = 0

IMAGES = 9 or 11

IOPT = 1

ISIF = 2

ISMEAR = 1

ISPIN = 1

ISTART = 1

ISYM = 0

LCHRG = .FALSE.

LCLIMB = .TRUE.

LREAL = Auto

LWAVE = .FALSE.

NCORE = 4

NELM = 200

NELMIN = 6

NSW = 200

POTIM = 0

SIGMA = 0.2

SPRING = -5

I'm also using a Monkhorst-Pack 3 x 3 x 3 k-point mesh.

Any insight into what might be causing this behavior would be greatly appreciated.

Thanks in advance!

---

**ahterpet** (2026-02-05 16:56):

Hi Professor Henkelman,

Unfortunately, I’m encountering an error when trying to attach the .tar.gz files to this message, likely due to their size. I’d be happy to email them to you instead if that works for you.

---

**ahterpet** (2026-02-05 17:26):

Okay, I sent you an email with the .tar.gz files. Apologies for any inconvenience this might have caused.

---

**ahterpet** (2026-02-05 17:53):

Okay, I’ll do that and report back. I also noticed that the distances between neighboring images tend to vary more as the number of images increases. In other words, it seems more difficult to maintain equal spacing between images when using a larger number of images with CI-NEB. Could this potentially explain my results?

## Expert answer (forum ground truth)

**graeme** (2026-02-05 08:02):

If you can attach a .tar.gz of the calculation (without CHG*, WAV* files), I can take a look at it.

---

**graeme** (2026-02-05 17:14):

Anyway to get the data to me is fine.

Do make sure to delete the large CHGCAR, CHG, and WAVECAR files - I don't need to see those.  We should be able to accept files as large as 500 MB.

---

**graeme** (2026-02-05 17:33):

These calculations look just fine to me.  It appears that there is a shallow intermediate minimum half way along the path.  Try minimizing the middle image.  It may have required sufficient resolution, with the 9 or 11 image band to resolve the minimum.

---

**graeme** (2026-02-05 17:58):

No, I don't see that as a problem. You could decrease ediffg and do a little more convergence and you can reach equal spacing to arbitrary accuracy. There is clearly a plateau at the top of the minimum energy path and what looks to be a local minimum half way along the path.  It does not look like an artifact to me.

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**This isn't a bug or a setup error — it's exactly what CI-NEB does on a flat/broad saddle once you sample it finely enough.** The climbing image is chosen by energy *rank* (the single highest-energy image), **not** by geometric position, so on a flat or slightly double-humped top it legitimately lands off the geometric midpoint. The energy differences you're worried about are at or below your convergence noise: in the 11-image run, images 5 and 7 differ by **0.2 meV** (1.679920 vs 1.679724) and the image-6 "sag" is only **~5 meV** — both far under what `EDIFFG = -0.03` can resolve. With 1/3/5 images the spacing near the top is coarse, the highest image is unambiguous, and the profile looks clean; at 9–11 images the top gets sampled finely enough that near-degenerate images and a tiny mid-top dip appear. **Your migration barrier of ≈1.68 eV is the robust, reportable number** (right in line with the accepted PBE value of ~1.7 eV for W vacancy migration).

## Why each observation happens

**9 images — CI on image 6, not the midpoint (5).** Per the VTST definition (`docs/vtst/neb.md`), the climbing image is "the highest-*energy* image," driven onto the saddle. That is picked by energy rank — it coincides with the geometric/reaction-coordinate midpoint *only for a clean harmonic saddle*. On a flat top, whichever image is marginally highest (here image 6, by what is almost certainly a sub-10 meV margin) becomes the climber. No physical asymmetry of the path is required — a flat top plus convergence noise is enough. The climbing image is also exempt from spring forces, so spacing on the two sides of the saddle differs by design; the CI is not constrained to sit at the center.

**11 images — image 6 sags between images 5 and 7 (the "M shape").** This is the canonical signature in the diagnostics: a mid-band image lower than both neighbors despite `LCLIMB=.TRUE.`. Image 6 *is* the symmetric midpoint here (images 1–11, midpoint = 6). Two readings are possible and they're physically different:

- **A real, shallow metastable intermediate** at the symmetric configuration — i.e. a two-saddle (M-shaped) path, which does occur in some BCC metals.

- **A flat saddle with near-degenerate top images**, where the 5 meV dip and the 0.2 meV 5-vs-7 split are just noise at `EDIFFG=-0.03`.

Critically, **a single CI-NEB converges only its one highest image to a true saddle.** So in the 11-image run only image 7 (the climber) is a converged saddle; images 5 and 6 relaxed under ordinary NEB forces and their energies are *not* converged stationary-point values. Don't over-read the 0.2 meV / 5 meV differences — they aren't resolved.

**Why 1/3/5 images looked fine.** This feature is invisible at low image counts and only a dense band (≈9–11) samples it — coarse spacing near the top makes the single highest image unambiguous and hides the flat/dip structure.

## What to do

1.

**Report ≈1.68 eV as the barrier.** The climbing-image energy is your reliable rate-limiting barrier regardless of which image it lands on, and it's consistent across your runs (1.6798 / 1.6799). Don't force the CI to "center" — there's no requirement that it sit on the geometric midpoint.

2.

**Decide whether the dip is real with one test: tighten convergence.** Set `EDIFFG = -0.01` (and `EDIFF = 1E-6` for cleaner energies), restart from the current `CONTCAR`s, and re-examine `neb.dat`. The doctrine is decisive here: a *real* intermediate/plateau **persists** under tighter `EDIFFG` (and as you add images), while a numerical artifact **washes out** and the spacing equalizes. `EDIFFG=-0.03` is the loose end of the VTST range (`-0.01` to `-0.03`); it cannot resolve meV-scale top structure.

3.

**If the dip survives tightening and you care about the intermediate:** relax image 6 in isolation. If it settles into a stable minimum below its neighbors, you have a genuine two-step path — split into two separate NEBs (IS→intermediate, intermediate→IS) to converge each saddle properly. If you only need the migration barrier, you already have it.

4.

**Minor workflow refinement (not the cause):** VTST recommends running plain NEB first, *then* switching on `LCLIMB`, so the highest image is already near the saddle before it starts climbing — starting CI from the outset can worsen the uneven spacing you're seeing. Your `IBRION=3 / POTIM=0 / IOPT=1` deck is otherwise correct.

**Confidence:** high that the behavior is expected physics + resolution, not a deck error — the symptom matches the documented signature line-for-line (including the literal "image 6 of 9, not 5" case). To tell the *real-intermediate* vs *flat-saddle-noise* sub-cases apart, I'd want to see `neb.dat` (per-image energy **and** force columns) from a run tightened to `EDIFFG=-0.01`. If you can post that, I can confirm which it is.
