# Topic 10941 — Confusion about NEB calculation

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> Accurate response from AI.

## Original question

**nyShi** (2020-08-04 08:12):

Dear Professor,

I am a beginner of VASP software.Recently, when I was learning to calculate the energy barrier of the S atom crossing an edge of the Ni55 cluster, several problems appeared.I can’t figure out the reason by myself, So i hope to find suggestions and solutions here.

The problem is that in NEB calculation, the energy of IS and FS is too far from the energy of five images. This is unreasonable. I don’t know what went wrong.Based on the first question, I did a single-point energy test. The energy difference between TS and IS is 0.58 eV, which is reasonable, so I don’t know if which parameter is wrong in the NEB process.At the same time, I also did a frequency verification of the transition state (03), which showed that it was correct, so I was really at a loss as to the reason why the energy barrier was too large. All the data was packed in the attachment compression package.

Hope to get your attention and thank you in advance！

## Expert answer (forum ground truth)

**graeme** (2020-08-04 08:29):

Your calculation setting have to be the same for the endpoints and the NEB.  In your case, it looks like the endpoints were spin polarized and the NEB was not.  If you turn on spin polarization for your band, the energies should line up better.

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**Your NEB is missing `ISPIN = 2`.** The `NEB/INCAR` has no `ISPIN` tag, so the five interior images (01–05) ran **spin-unpolarized (ISPIN=1)**, while your endpoints 00/06 were copied from the spin-polarized `IS-Opt`/`FS-Opt` (ISPIN=2). For a magnetic Ni₅₅ cluster (total moment ≈ **40 μB**), turning off spin costs **~4.5 eV** of magnetic energy. That ~4.5 eV — not a real barrier — is the gap you see between IS/FS and the band. Add `ISPIN = 2` (plus `MAGMOM`) to the NEB INCAR and rerun.

## The evidence

I checked the `ISPIN` value VASP actually echoed in each OUTCAR:

| dir | ISPIN | final E0 (eV) |
| --- | --- | --- |
| 00 (IS) | 2 | −262.264 |
| 01 | 1 | −257.768 |
| 02 | 1 | −257.406 |
| 03 (apex) | 1 | −257.237 |
| 04 | 1 | −257.408 |
| 05 | 1 | −257.772 |
| 06 (FS) | 2 | −262.264 |

- Apparent NEB barrier = E(03) − E(IS) = −257.237 − (−262.264) = **+5.03 eV** ← the "too large" value.

- Even the *lowest* interior image (01) sits ~4.5 eV above IS — i.e. every interior image is shifted up by roughly the cluster's magnetic energy, exactly the ISPIN=1↔ISPIN=2 offset.

- Endpoint 00 reports total magnetization **≈ 40 μB** → this cluster is strongly magnetic; ISPIN=1 is physically wrong for it.

Why your two cross-checks looked fine:

- **Single-point test (0.58 eV):** both IS and TS there ran **ISPIN=2** (I confirmed). Consistent reference → real barrier: E0(TS) −261.686 vs E0(IS) −262.264 = **0.578 eV**. That is your true barrier.

- **Frequency check:** `vib/INCAR` also has `ISPIN=2`, so it validated a genuine saddle on the *magnetic* surface. Both checks were spin-polarized; only the NEB was not.

This is a textbook endpoints↔band inconsistency: the NEB INCAR silently dropped to the ISPIN=1 default, so the interior images optimized on the wrong (non-magnetic) potential-energy surface. (Your `KPOINTS` is Gamma-only `1 1 1` everywhere — consistent; the "4x2x1" first line is just a mislabeled comment and is harmless. Version is fine: VASP 5.4.4 + VTST 3.2, IOPT supported.)

## The fix

Edit `NEB/INCAR` to make the electronic setup match the endpoints. Add:

```
ISPIN  = 2
MAGMOM = 55*2 1*0     # 55 Ni initialized at 2 µB, 1 S at 0 (order is Ni then S in your POSCAR)
PREC   = Normal       # match IS/FS-Opt (currently unset in NEB)
LREAL  = Auto         # match IS/FS-Opt
```

Then restart the band from the geometry you already have (cheaper than from scratch, and the geometry is a fine starting guess):

```
cd NEB
for i in 01 02 03 04 05; do cp $i/CONTCAR $i/POSCAR; done
# resubmit
```

Because the previous interior geometries were relaxed on the non-magnetic surface, let the spin-polarized run re-converge the path — don't just re-evaluate energies.

Two robustness notes for **magnetic NEBs** specifically (this is the common failure mode and worth doing up front):

- Keep the **explicit `MAGMOM`** above so every image starts ferromagnetic and lands on the *same* magnetic minimum; otherwise individual images can settle into different spin states and give a jagged band.

- After it finishes, `grep mag */OUTCAR` and confirm the moment trends smoothly IS→FS (≈40 μB throughout). If one image's moment is an outlier, seed it with `CHGCAR`/`WAVECAR` from a correct spin-polarized single point and rerun that image.

**Expected result:** the band will collapse onto the ~0.5–0.6 eV scale, consistent with your single-point TS−IS = 0.58 eV and your confirmed saddle.

**Confidence: very high** — the ISPIN mismatch is echoed directly in the OUTCARs and the ~4.5 eV offset matches the cluster's magnetic energy quantitatively.
