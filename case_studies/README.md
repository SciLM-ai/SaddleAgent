# Case studies — real Henkelman-forum questions

These are real transition-state-search questions from the Henkelman Group's VASP/VTST
support forum, run through SaddleAgent.

Every case directory holds:

- `question.md` — the user's forum post (the problem, in their words)
- `expert_answer.md` — the forum expert's actual reply (the ground truth)
- `precheck_report.txt` — the deterministic precheck output on the user's files (the
  raw facts the shipped agent gets injected up front)
- `files/` — the **complete set of the user's uploaded VASP files** (INCAR, POSCAR,
  OUTCAR, OSZICAR, KPOINTS, neb.dat, scripts, logs, …), except `POTCAR` (see below)
- the agent's answer(s) and full transcript(s)

**Showcase** cases add `saddleagent_answer.md` and `transcript.md` (the full reasoning
trace and every tool call). **Ablation** cases instead add two run subdirectories (each
with its own `answer.md` + `transcript.md`) that toggle exactly one guardrail on versus
off, so you can see what that guardrail changes.

## The cases

| case | who · when | the real cause (expert) | type · result |
|---|---|---|---|
| [16186 — charged-defect NEB](16186-charged-defect-neb/) | jordanchapman · 2025-06 | atoms overlap from a mis-ordered band (not `NELECT`) | **precheck ablation** — flips wrong→right |
| [16189 — POTCAR order swap](16189-potcar-order-swap/) | jordanchapman · 2025-06 | Li/F swapped in the band's POTCAR | showcase — correct (both with and without guardrails) |
| [16196 — shallow minima](16196-shallow-minima/) | jordanchapman · 2025-11 | exact-exchange artifact; endpoint not minimized | **Stop-hook ablation** — no flip (an honest null result) |
| [16198 — CO2 NEB](16198-co2-neb/) | shkwon · 2025-12 | path bundles formation + desorption; timestep | showcase — strong (core point + extra fixes) |
| [16199 — Hf POTCAR mismatch](16199-hf-potcar-mismatch/) | shkwon · 2025-12 | endpoints Hf_pv vs band Hf_sv | showcase — correct |

## What the guardrail ablations show

As a debugging session grows, the ts-debug skill's guidance falls far back in the
model's context and the agent can drift toward whatever the user *thinks* is wrong.
Two cheap, deterministic nudges are meant to pull it back — and they do different jobs:

- The **precheck** greps the files first and hands the agent the hard structural facts
  (atom-count and NELECT mismatches, image-directory layout, empty OSZICARs, missing
  VTST banners) up front. This is the lever that **flips a diagnosis**. In
  [16186](16186-charged-defect-neb/) the user blames `NELECT`; both runs get past that
  and find atoms colliding, but only the precheck's atom-order directive steers the
  agent to the right *fix* (reorder the endpoints, matching the expert) instead of the
  plausible-but-wrong one (IDPP re-interpolation).

- The **Stop-hook self-audit** forces the agent, right before it finishes, to back every
  VASP/VTST claim with a doc it actually opened and refuse to over-assert. This is a
  **discipline / anti-overconfidence** guard, not a diagnosis-flipper. The isolation in
  [16196](16196-shallow-minima/) is an honest null result: the audit made the answer
  doc-grounded and appropriately hedged (in the spirit of the expert's own reasoning),
  but did **not** flip a wrong answer to a right one — the bare run reached the same core
  fix. We include it as-is rather than cherry-pick a win.

Reproduce either ablation yourself with `saddleagent --no-precheck` and/or
`--no-audit` versus the defaults.

## Provenance and data handling

These questions and their attachments were posted on the Henkelman Group support
forum; the group's PI, Graeme Henkelman, is a co-author of this project, and the
uploaded VASP files are included here under `files/` so each case is fully inspectable
and reproducible.

**One exception: `POTCAR` files are not included.** VASP pseudopotentials are licensed
by VASP Software GmbH and may not be redistributed publicly — that is VASP's license,
independent of who uploaded the file. Where a run used a POTCAR, a
`POTCAR.EXCLUDED.txt` placeholder marks its location and explains how any VASP licensee
regenerates it (concatenate the element POTCARs in POSCAR order). The agent only ever
reads a POTCAR's `TITEL` / `ZVAL` metadata, which the OUTCARs also record, so nothing
in the diagnoses depends on the omitted files.
