# Topic 16188 — Question Regarding CI-NEB Convergence Issue Using VTST Tools

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, the true expert answer, and the user's files.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman
- **Trace:** [`trace.md`](trace.md) — the graded run's step-by-step thinking and full tool-call log

## Graeme's grader note

> The AI response is accurate.

## Files

`files/` — the complete upload (101 files; `POTCAR` excepted, for licensing).

## Original question

**Chenjiao** (2025-06-13 15:35):

Hi, I'm running a CI-NEB calculation using VASP and VTST tools, but I'm encountering convergence issues.

As shown in the attached plot, the ionic steps remain almost unchanged, and the maximum force is stuck at around 0.353 eV/Å. Moreover, instead of tracing a reaction path with decreasing energy, the image energies are increasing monotonically from the initial state (image 0) to the final image (image 6), which seems unphysical.

My setup:

IBRION = 3, IOPT = 3, IMAGES = 5

SPRING = -5, LCLIMB = .TRUE.

ENCUT = 500, EDIFF = 1E-5, EDIFFG not explicitly set

NSW = 1200, ISIF = 2, NELM = 100

I used linear interpolation for image generation and ran the standard VTST NEB workflow. nebef.pl shows little structural change between images and a rising energy trend. The climbing image seems not to be helping at this stage.

What might be the cause of this behavior? Should I regenerate the images with greater initial displacements, change the spring constant, or disable climbing until forces converge better?

Any advice would be appreciated!

---

**Chenjiao** (2025-06-18 13:48):

Dear Graeme,

Thank you so much for your kind reply and for offering to help!

I’ve now attached two zip files as requested:

Test.zip – This contains a small test calculation I ran right after compiling VTST. It completed successfully and was mainly used to confirm the installation.

V-1.zip – This is the actual NEB calculation where I encountered the issues (frozen images, unchanging forces, and steadily increasing energy despite IOPT = 3 and LCLIMB = .TRUE.). I’ve excluded all CHG and WAV files to keep the size reasonable.

I really appreciate your time and support in helping me troubleshoot this. Please let me know if you need any additional files or information.

Thank you again for your generosity and expertise.

Warm regards,

Chenjiao

---

**Chenjiao** (2025-06-19 08:41):

Dear Graeme,

Thank you very much for pointing this out.

You're absolutely right — I used the VTST-linked vasp.5.4.4 binary for the endpoints, but mistakenly used vasp.6.4.1 (which does not include VTST) for the NEB calculation.

I'll re-run the NEB calculation using the correct VTST-enabled vasp.5.4.4 binary and see if that resolves the convergence issue.

Really appreciate your help!

## Expert answer (forum ground truth)

**graeme** (2025-06-13 16:14):

If you can attach a .tar.gz of the simulation (with no CHG* WAV* files) I can help to debug it.

---

**graeme** (2025-06-13 17:35):

Additionally, I don't think that you have our vtstcode linked into your binary.  You can check by greping for VTST in any OUTCAR.

---

**graeme** (2025-06-18 15:15):

it looks like you linked the VTST code into the binary that you used to calculate the endpoint, but not the binary that you used to calculate the NEB:

endpoints:

vasp.5.4.4.18Apr17-6-g9f103f2a35 (build Jun 16 2022 14:25:58) complex 

NEB:

vasp.6.4.1 05Apr23 (build May 18 2024 16:13:51) complex

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**Your INCAR is a correct CI-NEB deck, but the VASP binary running the NEB has no VTST (vtstcode) linked in — so `IOPT`/`LCLIMB`/`SPRING` are silently ignored, and with `POTIM=0` + `IBRION=3` VASP's own optimizer takes zero-length steps. The band never moves off the linear-interpolation guess.** That single fault explains every symptom: forces frozen at 0.353, no ionic motion, and the monotonic rising energy (that profile is just your un-relaxed straight-line path). Don't touch the images, SPRING, or LCLIMB — fix the executable.

## The evidence that nails it

The smoking gun is in your own `nebef.pl` table:

| image | force | rel-E |
| --- | --- | --- |
| 0 (endpoint) | 0.028700 | 0.000 |
| 1–5 (interior) | 0.000000 | 0.39 → 2.30 |
| 6 (endpoint) | 0.027024 | 2.884 |

`nebef.pl` reads the `FORCES: max atom, RMS` line that **the VTST optimizer prints** into each image's OUTCAR (per `docs/vtst/scripts.md`: it parses the last `max at` line). Every *interior* image reads exactly `0.000000` — that line was never written, i.e. the tangential-force projection never ran. Meanwhile your plot's 0.353 comes from the raw per-image `TOTAL-FORCE`, which is normal — each image is just running as an independent single point. *Interior `nebef` forces all `0.000000` while raw OUTCAR forces look normal = VTST not in the binary* (reference/neb-diagnostics.md, "NEB forces frozen/static… despite IOPT/LCLIMB set").

Why zero motion follows: `docs/vtst/optimizers.md` says the VTST workflow sets `IBRION=3, POTIM=0` precisely to *disable VASP's stepper* and hand stepping to `IOPT`. If vtstcode isn't linked, `IOPT=3` is an unknown tag → ignored → VASP's `IBRION=3` damped MD runs with `POTIM=0` → **step size zero → the geometry is frozen** at the interpolation. Hence a dead-flat force line and a monotonic energy that's simply the initial guess. If `IOPT` had actually parsed, a 0.353 eV/Å force would move the band immediately.

Telling detail: your endpoints (00, 06) *do* show real forces, but the interior images don't. That fits the common sub-case — vtstcode is linked into the build you relaxed the **endpoints** with, but your `vasp.sbatch` points the **NEB** job at a stock `vasp_std`.

## Confirm it in 10 seconds

```
grep -i vtst   03/OUTCAR     # VTST version banner at startup — ABSENT = not linked
grep -i 'OPT:' 03/OUTCAR     # e.g. "OPT: QM, TIMESTEP" — ABSENT = IOPT never parsed
grep 'NEB: '   03/OUTCAR     # projections/tangent/distance lines — ABSENT = NEB code idle
```

Then check the executable line in `vasp.sbatch` and compare it to the one used for the endpoint relaxations.

## The fix

1. **Run the NEB with a VTST-patched `vasp_std`** (vtstcode compiled in) — the same build (or equivalent) you used for the endpoints. Point `vasp.sbatch` at it.

2. **Keep your INCAR exactly as is.** `IBRION=3 POTIM=0 IOPT=3` is the canonical quickmin driver; once `IOPT` parses it produces the ionic moves (parameters.md). Re-run from the current image POSCARs/CONTCARs — no re-interpolation needed.

3. Verify the banner appears in the new OUTCARs, then watch the force *trend* over the first ~20 steps — it should start dropping below 0.353 instead of sitting flat.

## Your three questions — all "no"

- **Bigger initial displacements?** No. The geometry is fine; nothing is moving because the optimizer is inert, not because the path is too gentle.

- **Change SPRING?** No. `SPRING=-5` is the canonical solid-state value (parameters.md) — and it's being ignored anyway. Lowering it never cures a stall.

- **Disable climbing?** No. `LCLIMB` should be on from the outset; it's also a VTST-only tag, so it's doing nothing right now. It's a non-issue until the band is actually relaxing.

One correction: you wrote "EDIFFG not explicitly set," but your INCAR shows `EDIFFG = -0.05` — correctly negative, which is exactly what `IOPT>0` requires. Leave it; you can tighten to `-0.03`/`-0.02` for a cleaner saddle on the final approach.

## After VTST is live — one thing to watch

Re-check the profile once forces are genuinely dropping. If the energy *still* climbs monotonically to image 6 with no interior maximum, that's a separate physics question (the "final state" may be ~2.9 eV uphill and not a true minimum, or the reaction direction puts the TS at/beyond the product). But you can't judge that until the band moves — right now the profile is just the straight-line interpolation, so it tells you nothing about the real MEP.

Confidence: high on the diagnosis from the `nebef.pl` zero-force signature + frozen band + `POTIM=0`. The one grep above will confirm the missing VTST banner. If it turns out the banner *is* present, send me `03/OUTCAR` and I'll look for an `IOPT` parse error (tab/typo) instead.
