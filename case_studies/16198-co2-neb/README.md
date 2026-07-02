# 16198 — a CO2-formation NEB with multiple humps

- **Who / when:** `shkwon`, Henkelman Group support forum, December 2025 (topic 16198)
- **Model:** recorded production run, SaddleAgent with Opus 4.8 (ts-debug skill)
- **Verdict:** strong — independently reached the expert's core point and added several
  real, file-level fixes the expert did not mention. One judgement call differs (below).

## The problem
A CO2-formation NEB on Pd shows several barriers along the band and will not
converge cleanly. The user asks whether the climbing image or too-few images is
the issue.

## The expert's answer (ground truth)
Two problems. First, the path is long: most of it is CO2 moving away from the
surface, so with only 4 images just one is really in the reaction step. Second,
CO2 has high-frequency modes, so it needs a smaller timestep; the endpoints
converged because they used CG. Note there is a lower initial state, so minimize
image 02 to get a new initial state.

## What SaddleAgent said
(1) The band never converged (no image met `EDIFFG = -0.026 eV/A`), so the plotted
energies are not path energies. (2) The endpoints bundle two distinct processes,
CO2 *formation* and then CO2 *desorption* into the gas phase (product CO2 ~4.5 A
above the slab), which is what stretches the path and adds the extra humps. Fix:
rebuild the final endpoint as just-formed CO2 still near the surface and re-run,
treating desorption separately. It also caught issues the expert did not list: an
oversized `SIGMA = 0.41 eV`, a binary/`ISYM`/`EDIFF` mismatch between endpoints
(vasp 5.4.4) and band (vasp 6.5.1), and NaN velocity blocks in the restart files.

**The one divergence:** on the timestep, the expert wanted it *smaller* (to resolve
CO2's stiff modes); SaddleAgent instead read QuickMin as crawling and suggested
*raising* `TIMESTEP` for faster convergence. Both are defensible for different
goals, but this is where the agent and the expert part ways.

See `transcript.md` for the full reasoning and every tool call.

## Files
`question.md` · `expert_answer.md` · `saddleagent_answer.md` · `transcript.md` · `precheck_report.txt` · `files/` (complete uploads; POTCAR excluded)
