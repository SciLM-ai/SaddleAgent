# 16199 — endpoints and band run with different Hf pseudopotentials

- **Who / when:** `shkwon`, Henkelman Group support forum, December 2025 (topic 16199)
- **Model:** recorded production run, SaddleAgent with Opus 4.8 (ts-debug skill)
- **Verdict:** correct — same root cause as the expert, with the quantitative mechanism worked out.

## The problem
A CO-gas-formation NEB on an Hf surface: the interior images sit about 90 eV
*below* both endpoints, an apparently huge and unphysical well in the band.

## The expert's answer (ground truth)
You must use the same settings in the endpoints as in the band. The endpoints
used `Hf_pv` and the band used `Hf_sv`; the k-point mesh also differed. DFT
energies only compare when the settings match.

## What SaddleAgent said
It traced the ~90 eV drop to a POTCAR mismatch: the relaxed endpoints (00, 05)
used a 10-valence Hf potential (`ZVAL = 10`, a `Hf_pv` type) while the interior
images (01–04) used `Hf_sv` (`ZVAL = 12`). The 2 extra semi-core electrons per
Hf times 32 Hf is 64 extra electrons, which drives each interior image's `TOTEN`
about 90 eV more negative. It reached this from the precheck's NELECT-mismatch
lead (endpoints 454 vs images 518 electrons on identical 65-atom geometries),
then grounded the ZVAL/NELECT reasoning in `docs/vasp/potcar.md` before writing.

See `transcript.md` for the full reasoning and every tool call.

## Files
`question.md` · `expert_answer.md` · `saddleagent_answer.md` · `transcript.md`
