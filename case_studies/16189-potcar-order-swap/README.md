# 16189 — POTCAR element order swapped between endpoints and band

- **Who / when:** `jordanchapman`, Henkelman Group support forum, June/July 2025 (topic 16189)
- **Model:** shipped agent, Claude Opus 4.8 (ts-debug skill), guardrails on
- **Verdict:** correct — matches the expert exactly.

## The problem
An NEB for an F-interstitial hop in LiF returns intermediate images with energies
nearly 10 eV *below* both endpoints. The user has already checked that `ENCUT`, the
k-mesh, symmetry, and geometry are all consistent, and that the POSCAR ordering is
the same across images. What is causing the downward shift?

## The expert's answer (ground truth)
*"It looks like you switched the order of Li and F in your POTCAR file, between the
endpoints and the band."*

## What SaddleAgent said
It traced the ~8-13 eV offset to exactly that: every POSCAR declares `Li F / 108 108`
(Li block first), but the band images' POTCAR is concatenated `F` then `Li_sv`, so
VASP positionally maps the F pseudopotential onto the Li sublattice and vice versa.
Because both blocks hold 108 atoms and the total electron count is unchanged, VASP
raises no error and just silently computes a different, physically meaningless
crystal. Fix the POTCAR order and rebuild. It read the species-to-block mapping
(`TITEL` / `POMASS` / `ZVAL`) straight out of each OUTCAR to prove the flip.

## Note: the skill carries this one on its own
This case was also run **without** the prechecks and Stop-hook audit
(`--no-precheck --no-audit`), and the bare agent reached the **same correct
diagnosis**. Unlike topic 16186, the guardrails do not change the answer here — the
POTCAR mapping is unambiguous in the OUTCARs, so the skill alone is enough. That is
the honest picture: the deterministic guardrails matter for the ambiguous, red-herring
cases (see 16186), not for every case.

See `transcript.md` for the full reasoning and every tool call.

## Files
`question.md` · `expert_answer.md` · `saddleagent_answer.md` · `transcript.md`
