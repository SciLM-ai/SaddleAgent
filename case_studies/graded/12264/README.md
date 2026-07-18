# Topic 12264 — Question around CI-NEBs and the saddle point

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> A sensible response from AI.

## Original question

**BuddyMacaulay** (2021-08-23 14:13):

Hey, I've been working on some NEBs for a group of fairly finnicky systems for a while now and have a few questions that I'm a little unsure about.

Generally, for most of the NEB's the results look nice and converge well, with the climbing image finding a visually reasonable Transition state.

1.

I'm about to run some NEB's on a process which i believe may have a fairly stable intermediate and not transition state at the midpoint. 

Will running these calculations with a climbing image result in poor convergence/incorrect intermediates or will it work completely fine?

If i shouldn't use a climbing image, is there any suggestions as to anything else I can do with computational resources being somewhat limited. 

2.

With another bit of work I'm trying to show the relative energies of a specific pathway alongside a different (expect higher energy) pathway . However obviously running a neb on the higher energy path results in the MEP being found. Was wondering if you had any suggestions to force this higher energy path to be found.

I'm assuming for both these cases, running two separate nebs of initial->midpoint then midpoint->final would likely be an idea although i'm not sure the midpoint for the higher energy pathway is very stable and I would be able to get a reasonably converged energy.

Thanks In advance for your suggests. I can send some images of my structures and expected TS/intermediates at a later point if that'd help.

- Buddy

## Expert answer (forum ground truth)

**graeme** (2021-08-23 14:37):

Hi Buddy,

1. If you have an intermediate minimum, I would recommend finding that first and then running two NEB calculations (as you suggest).  It's not that the climbing image will not work with an intermediate minimum, it just that you will need more images to resolve a multi-step path, and there are annoying situations such as where the path goes into an intermediate minimum and back out following the direction that it entered, causing a 180 deg turn in the path.

2. You would have to say more about what makes the higher energy path a well-defined path.  If there is a higher energy saddle, the NEB can be used to find it.  If there is no saddle corresponding to the higher-energy path, I imagine that there should be some way to define it, either by symmetry or some constraint.  If so, you might be able to apply the constraint to the NEB.  I might be able to give more specific suggestions if you provide more details.

Graeme

## The graded AI answer (SaddleAgent (with Opus 4.8))

Both of your questions are really about the **topology of the potential-energy surface**, not about a broken run — and the good news is the VTST doctrine has clean answers for each. Let me take them in turn.

## Q1 — A stable intermediate at the "midpoint"

**A single climbing image won't corrupt the intermediate, but it also won't properly resolve a two-barrier path — and if the two saddles are close in height it can stall. The right move (and the *cheaper* one) is exactly what you guessed: locate the intermediate, relax it to its own minimum, then run two separate CI-NEBs.**

Details:

- **CI-NEB does not produce an "incorrect intermediate."** The climbing image only acts on the single highest-energy image (it inverts the parallel force there); every other image — including one sitting in an intermediate minimum — relaxes normally. So the intermediate basin shows up faithfully in the band. What you lose is *the other barrier*: a single CI climbs **only the one global maximum** (neb-diagnostics.md, MEP-topology / multi-step rows), so on a double-barrier path one saddle is converged and the other is left as an unclimbed between-images estimate — i.e. under-resolved and likely under-estimated.

- **The convergence risk is real but specific:** when the two saddles are *similar* in height, a single CI-NEB tends to pre-converge to ~0.1 eV/Å and then **stall**, with the climbing image oscillating between the two competing maxima — it can't seat both. That's the "double-barrier" failure mode in neb-diagnostics.md. If the two saddles are clearly different heights you usually still converge, just with the minor barrier poorly resolved.

- **Recommended workflow (mechanism-agnostic — you don't have to know in advance):**

  1. Run **one plain NEB with CI *off* (`LCLIMB=.FALSE.`)**, enough images to span the *whole* coordinate — budget ~1 image / 0.5–1 Å, so **≥8 for a suspected two-step** (neb-diagnostics.md). You don't even need tight convergence; a loose `EDIFFG=-0.1` is enough to reveal the shape. Inspect `neb.dat` — an interior **minimum** (not a single hump) confirms the intermediate.

  2. **Relax that intermediate image to its own minimum** as a standalone calculation (it becomes the shared endpoint of both segments, so it must be a true relaxed minimum — workflows.md). A quick frequency check (all-real modes) confirms it's a genuine intermediate rather than a shoulder.

  3. **Split into two independent CI-NEBs**, IS→intermediate and intermediate→FS (`LCLIMB=.TRUE.`, `EDIFFG=-0.03`, ≥4 images each). Run them in parallel — no recombine.

- **On limited compute — splitting is the economy, not a cost.** A single band stretched across two steps *wastes* images: they pile up in the deep intermediate well and starve each saddle, so you resolve both barriers *worse* at equal or higher cost (workflows.md). Two focused segments each cleanly resolve one saddle. Stack that with the standard convergence economy — do the exploratory band at *cheap* electronic settings (`PREC=Normal`, `ENCUT≈POTCAR` minimum, coarse/Γ k-mesh, `ISPIN=1` if non-magnetic), since a barrier is an energy *difference* and is robust to absolute-energy precision; tighten only on the final per-segment bands.

Deck for the exploratory band: `ICHAIN=0, IMAGES≈8, IBRION=3, POTIM=0, IOPT=3, TIMESTEP=0.1, LCLIMB=.FALSE., EDIFFG=-0.1, ISYM=0`.

## Q2 — Forcing the higher-energy alternative pathway

**Whether you *can* force it depends on one thing: is the higher path a genuinely distinct valley (its own first-order saddle), or just a higher region of the same surface that drains into the low MEP? That you keep recovering the low MEP means your initial band sits in the low valley — or no separate saddle exists. The discriminator decides the tool.**

The hierarchy of options, cheapest/cleanest first:

1. **Seed the band *through* the higher valley.** `nebmake.py` (and ASE) interpolate *through* any intermediate structures you supply, not just the two endpoints (workflows.md build-the-band). Build the band with a waypoint — a hand-made geometry or TS guess that lies in the alternate mechanism's valley (`interpolate.pl A B frac` makes one) — and set **`ISYM=0`** so a symmetry-breaking alternate path isn't suppressed. If a distinct saddle exists, NEB converges to *that* MEP (there can be several MEPs between the same endpoints; NEB finds the one in its initial basin).

2. **Use a min-mode search to nail the *specific* saddle — the best fit for "I have a particular higher TS in mind."** A **dimer or Lanczos finds the saddle *nearest* its starting geometry**, independent of whether it's the global MEP (dimer-diagnostics.md). Seed it from a guess of the alternate TS (or from the secondary-max image of the Q1 exploratory band — neb-diagnostics.md explicitly suggests "seed a dimer/Lanczos from the secondary-max image to capture the non-global saddle CI never climbs"). Then relax ±the negative mode (`dimmins.pl`) to recover the two minima it connects and **verify it connects your intended IS/FS** (IRC connectivity — workflows.md).

3. **If both of the above slide back to the low path, there is no separate saddle** — the "higher path" is a shoulder that drains downhill (the "band slid off a shoulder onto a lower path" mode, neb-diagnostics.md). NEB/dimer *cannot* hold it. Your rigorous fallback is a **constrained-coordinate scan**: pick the collective variable that distinguishes the two mechanisms, fix it at a ladder of values, relax everything else, and report the constrained energy profile — stating the constraint explicitly. That's the standard, defensible way to present an alternative higher-energy channel that isn't a true MEP.

On your split idea for the higher path — **your worry is well-founded.** Splitting IS→midpoint→FS is valid *only if* the higher-path midpoint is a genuine relaxed minimum (even a shallow one); you **cannot** stitch two segments at an *unrelaxed* interior image — the join is not a stationary point and MEP continuity isn't enforced (workflows.md). If that midpoint isn't a real minimum, it relaxes away and you'll never get a converged intermediate energy there — so for the higher path, splitting fails for exactly the reason you suspected, and you fall back to the constrained scan.

**One caveat that applies to both questions:** for the two pathways' energies to be comparable, both must share *identical* endpoints (same relaxed IS and FS) and *identical* electronic settings — energies from different settings (or different cells) are never comparable.

Yes, please **send the images** — they'd let me tell you which case you're actually in, which is the crux of both questions. Most useful:

- the `neb.dat` / MEP profile from a converged (or even loosely converged) exploratory band, so I can see whether the midpoint is a real minimum or a shoulder;

- the IS/FS geometries and your TS/intermediate guesses for both the low and high paths;

- for the high path specifically, what coordinate you think distinguishes it from the low one (that becomes the constraint if it comes to option 3).
