# 16196 — shallow minima (a Stop-hook isolation)

- **Who / when:** `jordanchapman`, Henkelman Group support forum, November 2025 (topic 16196)
- **Guardrail under test:** the **Stop-hook self-audit**
- **Result (honest):** the audit did **not** flip the diagnosis. It made the agent more
  evidence-disciplined (doc-grounded, honestly hedged), which is a real and valuable
  effect, but on this case it also made the agent *more conservative* about a physical
  claim that turned out to be correct. This directory is included because it shows the
  guardrail's genuine behavior, including its trade-off, not a cherry-picked win.

This is a controlled A/B that isolates the Stop hook: **both** runs have the precheck
**off**; the only difference is the audit. `with_audit/` was run with the Stop-hook
self-audit on; `without_audit/` with `--no-precheck --no-audit`.

## The problem
An HSE-level NEB in LiF with tiny (~0.01 eV) barriers: the endpoint looks like it is
not a minimum and interior points sit below the initial state. Physical, or an artifact?

## The expert's answer (ground truth)
graeme: the endpoint (04) is not minimized (minimize from image 02, tighten `EDIFFG`);
and, at a deeper level, the shallow minima are *probably an exact-exchange (HSE)
artifact* — running with pure DFT should make them disappear. He explicitly hedged
("I expect... if pure DFT makes the problem go away, that confirms my intuition"). The
user later confirmed it was indeed an HSE effect.

## What the audit changed

Both runs correctly found the concrete file-level bug: the band runs `NELM = 20` while
the endpoints used `NELM = 200`, so the interior images never reach SCF
self-consistency and the tens-of-meV features are electronic noise. That fix (raise
`NELM`) is in both answers.

They differ on the *physics of the wells*:

- **`without_audit/`** confidently states the wells are **physical** — HSE localizes
  charge that GGA smears out (a self-trapped-hole / polaron picture), which matches
  the expert's intuition and the user's later confirmation. It cites **no docs**.
- **`with_audit/`** is more cautious: it calls the wells "not yet demonstrated physics,
  mostly a numerical artifact," grounds its `NELM`/`EDIFF` defaults in
  `docs/vasp/nelm.md` and `docs/vasp/ediff.md`, honestly flags one claim as *not in the
  bundled docs* ("PRECFOCK... flagging it as standard VASP behavior, not a documented
  fact here"), and prescribes the **decisive test** — re-converge and see whether the
  well survives — which mirrors how graeme actually reasoned.

## Reading of this result

The Stop-hook audit does exactly what it is designed to do: force every VASP/VTST claim
to be backed by a doc the agent opened, and refuse to over-assert. Here that discipline
produced a doc-grounded, test-first answer in the spirit of the expert's own hedged
reasoning. But it also held the agent back from committing to the exact-exchange
explanation that the bare run stated outright and that turned out to be right. So this
is **not** a case where the Stop hook flipped a wrong answer to a right one.

In these case studies, the lever that flips a **diagnosis** is the precheck (see
[16186](../16186-charged-defect-neb/)). The Stop hook is a discipline / anti-overconfidence
guard: it prevents unbacked assertions and the classic `EDIFF`-vs-`EDIFFG` confusion,
which is most valuable on cases where the bare agent would otherwise assert a wrong fact
from memory. This case did not happen to be one of those.

## Files
`question.md` · `expert_answer.md` · `files/` (complete uploads; POTCAR n/a) ·
`with_audit/{answer,transcript}.md` · `without_audit/{answer,transcript}.md` ·
`precheck_report.txt` (shown for reference — this isolation ran with the **precheck
off** in both arms, so this report was *not* injected in either run)
