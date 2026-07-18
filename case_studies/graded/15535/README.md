# Topic 15535 — Vacancy migration

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> This is a sensible response from the AI.

## Original question

**anirudhnk** (2023-05-24 14:58):

Dear Prof. Henkelman,

I just had a general conceptual question wrt vacancy migration in a structure. The vacancy formation energies are negative and favourable, however the energy barrier for vacancy migration between the two sites is extremely high (~ 7 eV). I am not sure if this would make sense, can you please explain?

---

**anirudhnk** (2023-05-25 17:35):

Thank you for your reply. Yes i meant that removing 1 atom from the structure, the formation energy of the structure is still negative. 

But I am not able to understand how then the migration barrier is extremely high.

---

**anirudhnk** (2023-05-25 18:06):

Sorry if its a simple question but I just want to understand better. I am not able to get the difference between vacancy formation energy and the structure with 1 vacancy defect. Do you mean that the vacancy formation energy = (energy of perfect structure - energy of defected structure) ? And that i was referring to the energy of the defected structure earlier (it being negtive)?

So, did i get it right? the energy of an imperfect crystal is always > energy of perfect crystal. Hence by above formula, energy of defect would be always -ve ?

---

**anirudhnk** (2023-05-26 14:01):

Got it, thanks very much for your reply

## Expert answer (forum ground truth)

**graeme** (2023-05-24 15:24):

So first, the vacancy formation energy should be positive in the sense that it costs energy to make a vacancy in a material.  If it was negative, the material would not be thermodynamically stable.

In terms of a vacancy diffusion barrier, 7 eV sounds pretty high, but I don't know what the material is.  Basically, the numbers seem a little fishy (that said knowing nothing about the system).

---

**graeme** (2023-05-25 17:38):

No, even if the overall formation energy is negative, that is not what's important: if the vacancy formation energy is negative the system will be unstable to vacancy formation.

---

**graeme** (2023-05-25 18:33):

Normally one would talk about a free energy difference, but let's just assume that the energy is the key component of free energy for solids.

So a negative formation energy of a material means that the material is more stable than your reference components.  That does not mean that the material is stable with respect to decomposition to other phases.  Stability of a material is typically defined by compositions on a convex hull plot.  If you are above the convex hull, then you would thermodynamically like to decompose into structures on the hull.

In terms of a structure with a vacancy - just because a structure with a vacancy has a negative formation energy does not make it stable with respect to other phases.  Specifically, the vacancy formation energy describes the energy of the material with a vacancy plus the per-atom reference energy of the vacancy material as compared to the original material.  If this is negative, the material would prefer to have a vacancy.  But then it will likely prefer to have another vacancy and so the material becomes unstable.  The vacancy formation energy of a stable material should be positive (even if the formation energy of a material with a vacancy is negative).

## The graded AI answer (SaddleAgent (with Opus 4.8))

**Neither number is physical, and they're two *independent* calculations — so you have two separate setup bugs, not one consistent picture. A negative vacancy formation energy almost always means a broken energy reference (wrong chemical potential, or inconsistent perfect-vs-defect cells). A ~7 eV migration barrier for a vacancy hop is almost certainly an NEB artifact — typically straight-line interpolation driving the migrating atom *through* a neighboring atom.** The two don't "explain" each other; they cancel out the one thing they share (see below).

## Why these are separate problems

The two quantities are built differently:

- **Formation energy:** `E_f = E(defect, N−1 atoms) − E(perfect, N atoms) + μ_X`, where `μ_X` is the reservoir/chemical-potential energy of the *removed* atom. This depends on `μ_X`.

- **Migration barrier:** `E_barrier = E(saddle) − E(initial vacancy)`. Both endpoints have the **same composition** (one vacancy each), so `μ_X` cancels exactly.

So a wrong `μ_X` corrupts `E_f` but has *zero* effect on the barrier. Getting both numbers unphysical means two independent things are off.

## The negative formation energy

A negative `E_f` says the perfect crystal spontaneously sheds atoms — it's not the ground state. That's essentially never true for a stable material (real vacancy `E_f` are positive, typically ~0.5–4 eV). The usual culprits, in order:

1. **Wrong `μ_X` / wrong bookkeeping.** For an elemental solid the clean form is `E_f = E(vac) − (N−1)/N · E(perfect)`. A common slip is subtracting a *full* `E(perfect)` instead of the `(N−1)/N`-scaled value — that injects roughly `−μ` and flips the sign.

2. **Inconsistent settings between the two cells** — different `ENCUT`, `PREC`, `ISMEAR`/`SIGMA`, or (most often) a **k-mesh that wasn't scaled** when the supercell changed size. The defect and perfect energies must come from the same convergence.

3. **The "perfect" reference isn't the relaxed ground state** (wrong lattice constant, wrong magnetic state, or not fully relaxed) — then removing an atom and relaxing lowers the energy artificially.

4. **Compound/multicomponent:** `μ_X` must lie inside the thermodynamic stability window set by competing phases; an arbitrary `μ_X` easily gives a spurious negative.

## The 7 eV barrier

7 eV is 3–50× a normal vacancy migration barrier; at that height the hop rate `ν·exp(−E/kT)` is astronomically immobile — it's not a diffusion barrier, it's a flag. For a *vacancy hop* the dominant cause is **linear-interpolation collision**: the straight Cartesian path routes the migrating atom across the occupied lattice site, giving a near-zero interatomic separation in an intermediate image and a huge energy spike.

Cheap checks (do these before anything else):

- Play the **initial band movie** — every atom should move smoothly and sub-Å per image.

- `grep -m1 'DAV\|RMM' */OSZICAR` — one interior image 100–1000× the others localizes the bad image.

- Inspect that image's POSCAR for any pair **< ~1 Å**. Outlier energy + sub-Å pair = interpolation overlap.

Fixes:

- **Rebuild with `nebmake.py`** (IDPP is its default), which curves the path around the collision instead of going straight through it.

- Confirm **both endpoints are fully relaxed in one fixed cell** (`grep 'reached required accuracy'` in each endpoint OUTCAR) — an unrelaxed endpoint dumps relaxation energy into the apparent barrier.

- Use **≥4 images** for a reliable MEP.

- Make sure **selective dynamics isn't freezing atoms next to the vacancy** — only far-field bulk atoms should carry `F F F`; a frozen DOF along the hop fabricates a barrier.

## What I'd need to pin it down

I'm confident on the *pattern* but not which sub-cause without the files. Please send:

1. The **perfect-cell and defect-cell OUTCARs** (so I can compare `ENCUT`/k-points/`ISMEAR`/cell and check your `E_f` arithmetic), and **how you computed `μ_X`**.

2. The NEB **`neb.dat`**, the per-image **OUTCARs**, and the **image POSCARs** (to confirm an interpolation collision and that the endpoints were relaxed).

My strong expectation: fix the reference and `E_f` lands positive; rebuild the band with IDPP and the barrier drops into the ~1 eV-or-below range.
