# 16186 — charged-defect NEB (a precheck ablation)

- **Who / when:** `jordanchapman`, Henkelman Group support forum, June 2025 (topic 16186)
- **Guardrail under test:** the deterministic **precheck**
- **Result:** with the precheck the agent reaches the expert's diagnosis; without it,
  the agent gives a plausible but **wrong fix**.

This is a controlled A/B run of the shipped agent (Claude Opus 4.8, xhigh) on the
same case. The only difference is the guardrails: `with_guardrails/` is the default
(precheck + Stop-hook audit on); `without_guardrails/` was run with
`--no-precheck --no-audit`. Reproduce it yourself with those flags.

## The problem
A charged-defect NEB (an anionic vacancy hop in LiF, one electron removed) dies at
startup with `BRMIX: very serious problems / old 1073 new 1072`. The user concludes
VASP "isn't reading `NELECT`" and asks why.

## The expert's answer (ground truth)
Two replies. graeme's first guess was to delete stale `CHG*`/`WAV*` files. His
**second, correct** reply, after looking at the files: *"the problem is that in your
initial band, you have atoms running into each other... The problem is a result of
atom ordering; make sure that each atom in your initial structure corresponds to the
same atom in the final structure."*

## What changed with the guardrail

**Both** runs correctly dismiss the `NELECT` red herring, and **both** discover the
same symptom: the interior NEB images have atoms collided on top of each other. The
answers diverge on *what that collision means*, because a mid-band collision has two
different root causes that need **opposite** fixes:

1. a single migrating atom linearly interpolated through an occupied site — fix by
   re-interpolating with **IDPP**;
2. a **same-species atom permutation between the two endpoints**, so `nebmake` pairs
   atom-*i* to atom-*i* by line order and mis-matches them — fix by **reordering the
   endpoints** (IDPP does *not* help, it still pairs by index).

graeme's answer is #2.

- **`without_guardrails/`** pattern-matched the collision to the common textbook case
  #1 (*"linear interpolation of a vacancy hop dragging an atom through an occupied
  site"*, citing the vacancy-hop row of `neb-diagnostics.md`) and prescribed **IDPP
  re-interpolation** — a fix that would not solve this problem. It never compared the
  two endpoints atom-by-atom.
- **`with_guardrails/`** reached #2 and **reordering the endpoints** — matching graeme.

## Why the precheck flipped it

The precheck report handed the guardrailed run two facts the bare run never had:

1. the exact colliding pair, `03 = 0.00 Å pair 127(F)-156(F)` — two **different**
   fluorines sitting on top of each other, which is the fingerprint of a permutation
   (#2), not of one atom crossing a site (#1);
2. an `atom_order_endpoints` **directive**: *"a permutation of same-species atoms
   between endpoints silently breaks the path... confirm each atom's initial→final
   displacement."*

The `with_guardrails/` transcript shows the chain directly. Step 1 opens *"since the
precheck flagged something alarming about the intermediate geometries,"* then the
pivot: *"many same-species pairs meeting at the midpoint is what a per-atom ordering
swap between endpoints produces — let me verify against the endpoint files,"* after
which it computed the per-atom endpoint displacements and found **~52 F displaced,
not 1**, confirming the reordering. It spent 22 tool calls to the bare run's 15; the
extra work was exactly that endpoint-ordering check the bare run skipped.

So the precheck did not merely "find the bug." It **disambiguated two collision
causes that look identical at the image level but need opposite fixes**, by reporting
that the collision is between two same-species atoms and directing the agent to run
the endpoint-permutation check.

## Files
`question.md` · `expert_answer.md` · `with_guardrails/{answer,transcript}.md` ·
`without_guardrails/{answer,transcript}.md`
