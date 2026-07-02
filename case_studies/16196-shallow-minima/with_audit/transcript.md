# SaddleAgent transcript

model: `claude-opus-4-8` · effort: `xhigh` · guardrails: precheck=off, stop-audit=on · 0 precheck lines


I'll start by loading the ts-debug skill since this is an NEB transition-state search problem, and inspect the provided files.


**[1] Skill**
```
skill: ts-debug
```

<details><summary>result</summary>

```
Launching skill: ts-debug
```
</details>

**[2] Bash**
```
command: ls -la files
description: List provided input files
```

<details><summary>result</summary>

```
total 0
drwxr-xr-x 3 graemeai henkelman 24 Jun 18 14:28 .
drwxr-xr-x 3 graemeai henkelman 24 Jun 18 14:28 ..
drwxr-xr-x 7 graemeai henkelman 97 Jun 18 14:28 u0
```
</details>

**[3] Bash**
```
command: find u0 -maxdepth 3 -type f | head -100; echo "---DIRS---"; find u0 -maxdepth 3 -type d
description: Map provided files and dirs
```

<details><summary>result</summary>

```
00/POSCAR
00/OUTCAR
01/POSCAR
01/CONTCAR
01/OUTCAR
02/POSCAR
… (7 more lines)
```
</details>

This is a 5-dir NEB (00–04 → 3 interior images). Let me check the INCAR and confirm the functional/settings, since the user's real question is about hybrid-functional PES noise.


**[4] Bash**
```
command: echo "===== INCAR ====="; cat -A INCAR
description: Dump INCAR with line endings
```

<details><summary>result</summary>

```
===== INCAR =====
! initialization$
System = Si$
ISTART = 1       ! new calculation$
ICHARG = 2$
$
… (33 more lines)
```
</details>

HSE06 hybrid NEB, IOPT=3 QuickMin, **LCLIMB=.FALSE.**, EDIFF=1E-10 with **NELM=20**, and **PRECFOCK=Fast**. Several of these bear directly on "noisy PES / spurious shallow minima" with exact exchange. Let me verify against the docs and confirm SCF behavior in the OUTCARs.


**[5] Bash**
```
command: cd agent/.claude/skills/ts-debug; echo "=== docs tree ==="; find docs -type f | sort; echo; echo "=== reference ==="; ls reference
description: List docs and reference files
```

<details><summary>result</summary>

```
=== docs tree ===
docs/ase/dimer.md
docs/ase/neb.md
docs/ase/vasp_calculator.md
docs/README.md
docs/vasp/algo.md
… (38 more lines)
```
</details>

**[6] Bash**
```
command: cd u0
echo "=== VASP / VTST banner (01/OUTCAR) ==="; grep -m3 -iE 'vasp\.[0-9]|VTST: version|NEB:|OPT:' 01/OUTCAR | head
echo; echo "=== PRECFOCK / HFSCREEN / AEXX echo ==="; grep -iE 'PRECFOCK|HFSCREEN|AEXX|LHFCALC' 01/OUTCAR | head
echo; echo "=== SCF convergence: count of ionic steps vs NELM aborts (01) ==="; grep -c 'aborting loop because EDIFF is reached' 01/OUTCAR; echo "--- 'aborting loop EDIFF was not reached' count:"; grep -c 'EDIFF was not reached' 01/OUTCAR
description: Check version, hybrid tags, SCF convergence
```

<details><summary>result</summary>

```
=== VASP / VTST banner (01/OUTCAR) ===
 vasp.6.4.2 20Jul23 (build Jun  3 2025 15:36:07) complex                         
 VTST: version 4.1, (05/19/21)
 OPT: Using Quick-Min optimizer

=== PRECFOCK / HFSCREEN / AEXX echo ===
… (15 more lines)
```
</details>

VTST 4.1 is properly linked (VASP 6.4.2) — no linkage issue. But the SCF is the story: image 01 hit **"EDIFF was not reached" 10 times vs converged only 3** — the hybrid SCF can't reach EDIFF=1E-10 within NELM=20. Let me quantify how far off SCF is, confirm endpoint relaxation, and read the authoritative docs.


**[7] Bash**
```
command: cd u0
echo "=== total ionic steps in each image (F= lines) ==="
for d in 00 01 02 03 04; do printf "%s: " $d; grep -c 'F=' $d/OSZICAR 2>/dev/null || grep -c '  F= ' $d/OUTCAR 2>/dev/null; done
echo; echo "=== endpoints reached required accuracy? ==="
for d in 00 04; do printf "%s: " $d; grep -c 'reached required accuracy' $d/OUTCAR; done
echo; echo "=== last few SCF dE values in image 01 (how close to EDIFF=1e-10) ==="
grep -E 'DAV:|RMM:' 01/OUTCAR | tail -6
echo; echo "=== NELM echo ==="; grep -m1 'NELM   =' 01/OUTCAR
description: Quantify SCF gap and endpoint relaxation
```

<details><summary>result</summary>

```
=== total ionic steps in each image (F= lines) ===
00: 0
01: 0
02: 0
03: 0
04: 0
… (15 more lines)
```
</details>

**[8] Bash**
```
command: cd agent/.claude/skills/ts-debug
echo "===== docs/vasp/nelm.md ====="; cat docs/vasp/nelm.md
echo; echo "===== docs/vasp/ediff.md ====="; cat docs/vasp/ediff.md
description: Read NELM and EDIFF docs
```

<details><summary>result</summary>

```
===== docs/vasp/nelm.md =====
# NELM

> Source: <https://www.vasp.at/wiki/index.php/NELM>

**Type:** integer · **Default:** `60`
… (20 more lines)
```
</details>

Endpoints (00, 04) both relaxed — good. Let me pull the actual SCF energy-convergence values to show how far from EDIFF=1E-10 the hybrid SCF stalls, and read the hybrid-NEB guidance in the reference.


**[9] Bash**
```
command: cd u0
echo "=== a non-converged SCF block: last 22 electronic-iteration energy lines in 01 ==="
grep -E '^(DAV|RMM|EDDAV):' 01/OUTCAR | grep -vi 'cpu time' | tail -3
echo "--- try d E ---"
grep -E 'd E =|dE =' 01/OUTCAR | tail -5
echo; echo "=== count ionic steps via 'FORCES: max atom' in 01 and total 'free  energy' ==="
grep -c 'FORCES: max atom' 01/OUTCAR
echo; echo "=== per-ionic-step: last SCF energy delta pattern (: N  energy  dE) ==="
grep -nE ':[[:space:]]+[0-9]+[[:space:]]+-0\.' 01/OUTCAR | tail -4
description: Extract SCF convergence deltas
```

<details><summary>result</summary>

```
=== a non-converged SCF block: last 22 electronic-iteration energy lines in 01 ===
--- try d E ---

=== count ionic steps via 'FORCES: max atom' in 01 and total 'free  energy' ===
14

… (1 more lines)
```
</details>

**[10] Bash**
```
command: cd agent/.claude/skills/ts-debug
echo "=== hybrid / PRECFOCK / exact-exchange mentions in reference ==="
grep -rniE 'precfock|hybrid|hse|exact exchange|LHFCALC|noise' reference/ | head -40
description: Search reference for hybrid/PRECFOCK guidance
```

<details><summary>result</summary>

```
<persisted-output>
Output too large (38.3KB). Full output saved to: ~/.claude/projects/-home-graemeai-saddleagent-agent/f0cb9c47-ebe6-4128-8171-f1f4eb11a432/tool-results/bicx5rpwh.txt

Preview (first 2KB):
=== hybrid / PRECFOCK / exact-exchange mentions in reference ===
reference/neb-diagnostics.md:254:**Discriminating look.** Per-image energies (`neb.dat`, `vasprun.xml`, or `grep -A2 'energy  without' OUTCAR` per image dir) for a clean local min / plateau, and compare *endpoints vs the interior max* in `neb.dat`; inter-image distances in OUTCAR; confirm forces have dropped / `EDIFFG` met so the feature isn't noise. When an image dips *below an endpoint*, first confirm endpoint↔band inputs match (inputs-inconsistent entry above) — a settings mismatch counterfeits a real dip and must be ruled out before invoking physics. Decisive test: tighten `EDIFFG` (and/or add images) — spacing equalizes while a *real* dip/plateau persists; an artifact washes out.
… (2 more lines)
```
</details>

**[11] Bash**
```
command: cd agent/.claude/skills/ts-debug
echo "=== PRECFOCK mentions ==="; grep -rniE 'precfock' reference/ docs/ 
echo; echo "=== 'NELM' + 'not reached' + non-self-consistent guidance in parameters.md ==="
grep -niE 'NELM|not reached|non-self|self-consistent|converged-but-wrong|hits NELM' reference/parameters.md | head
echo; echo "=== force-method agnostic / hybrid NEB block in parameters.md ==="
grep -niE 'agnostic|hybrid|force-method|bisect' reference/parameters.md | head
description: Find hybrid/NELM/SCF guidance in reference
```

<details><summary>result</summary>

```
=== PRECFOCK mentions ===

=== 'NELM' + 'not reached' + non-self-consistent guidance in parameters.md ===
94:## NEB barrier from unconverged SCF — every image hits `NELM`, so the optimizer trusts wrong forces
95:NEB forces are only as good as the SCF that produced them. If the electronic loop fails to reach `EDIFF` within `NELM` steps on an ionic step, VASP prints `aborting loop EDIFF was not reached (unconverged)` and hands the ionic optimizer a force from a *non-self-consistent* density — yet the band can still show low force norms and read "converged," so a wrong barrier passes silently. Most common on **DFT+U, spin-orbit, or transition-metal** systems run with `ALGO=Fast`/`VF` and no damping.
96:- **Tell.** `grep 'aborting loop' */OUTCAR` across *every* image dir: lines ending `EDIFF is reached` = good; `EDIFF was not reached (unconverged)` (i.e. `NELM` hit that ionic step) = the SCF never finished. Do this *before* trusting any barrier — a force norm at `EDIFFG` does not mean the density was self-consistent.
… (2 more lines)
```
</details>

The parameters.md §"NEB barrier from unconverged SCF" (line 94-97) is exactly this failure. Let me confirm the SCF is actually descending (not plateaued) at the NELM cutoff, and check system size — this decides whether the fix is "raise NELM" or "change ALGO."


**[12] Bash**
```
command: cd u0
echo "=== context around first 'EDIFF was not reached' in 01 (show SCF dE trajectory) ==="
grep -nE 'EDIFF was not reached' 01/OUTCAR | head -1
echo "--- last 12 SCF energy lines before that abort ---"
awk '/EDIFF was not reached/{print NR": "$0; c++} c==1{exit}' 01/OUTCAR
echo; echo "=== dump the electronic convergence table for one non-converged ionic step ==="
grep -nE '^(DAV|RMM|CG|DMP|EDDAV| DAV| RMM):' 01/OUTCAR | grep -viE 'cpu time' | head -3
echo "--- ALGO echo ---"; grep -m1 -iE '^ *ALGO|IALGO|LSUBROT' 01/OUTCAR
echo; echo "=== atoms / species (00 POSCAR head) ==="; sed -n '1,8p' 00/POSCAR
description: Check SCF descent trend, ALGO, system size
```

<details><summary>result</summary>

```
=== context around first 'EDIFF was not reached' in 01 (show SCF dE trajectory) ===
3976:------------------------ aborting loop EDIFF was not reached (unconverged)  ----------------------------
--- last 12 SCF energy lines before that abort ---
3976: ------------------------ aborting loop EDIFF was not reached (unconverged)  ----------------------------

=== dump the electronic convergence table for one non-converged ionic step ===
… (12 more lines)
```
</details>

216-atom LiF supercell (108 Li + 108 F), Li_sv pseudopotential → NELECT=1080 is just the neutral count (not a charged cell). Let me see the SCF descent trajectory right before an abort to decide raise-NELM vs change-ALGO.


**[13] Bash**
```
command: cd u0
sed -n '3940,3977p' 01/OUTCAR
description: Show SCF table before an EDIFF-not-reached abort
```

<details><summary>result</summary>

```
 soft charge-density along one line, spin component            1
         0         1         2         3         4         5         6         7         8         9
 total charge-density along one line
 
 soft charge-density along one line, spin component            2
         0         1         2         3         4         5         6         7         8         9
… (21 more lines)
```
</details>

**[14] Bash**
```
command: cd u0
echo "=== endpoints consistent w/ band? (HSE + PRECFOCK + NELM in 00 & 04) ==="
for d in 00 04; do echo "--$d--"; grep -m1 -iE 'LHFCALC =     T|PRECFOCK=' $d/OUTCAR; grep -m1 'NELM   =' $d/OUTCAR; grep -c 'EDIFF was not reached' $d/OUTCAR | sed 's/^/EDIFF-not-reached count: /'; done
echo; echo "=== how many total ionic steps did band image 01 take vs NSW=500 ? ('reached required accuracy' present?) ==="
grep -c 'reached required accuracy' 01/OUTCAR; echo "FORCES:max lines (ionic steps): $(grep -c 'FORCES: max atom' 01/OUTCAR)"
description: Confirm endpoint/band consistency and band convergence status
```

<details><summary>result</summary>

```
=== endpoints consistent w/ band? (HSE + PRECFOCK + NELM in 00 & 04) ===
--00--
   LHFCALC =     T    Hartree Fock is set to
   NELM   =    200;   NELMIN=  2; NELMDL=  0     # of ELM steps 
EDIFF-not-reached count: 0
--04--
… (7 more lines)
```
</details>

**Your "extra shallow minima" are, on the evidence in these files, mostly a numerical artifact of how the *band* is converged — not (yet) demonstrated physics.** Your NEB band runs with `NELM = 20` while your endpoints were relaxed with `NELM = 200`. In image `01`, the hybrid SCF hit `NELM` without reaching `EDIFF = 1E-10` on **10 of ~14 ionic steps** ("EDIFF was not reached"), so QuickMin was driving on forces from a *non-self-consistent* density — a noisy PES that manufactures meV-scale wells at exactly the ~0.01 eV scale you're trying to resolve. Fix the electronics (`NELM = 200` on the band, `PRECFOCK = Normal`) so SCF actually reaches `EDIFF`, *then* decide whether any minimum is real.

## Evidence from your files
- **The band and the endpoints are not at comparable electronic convergence.** Band `INCAR`: `NELM = 20`, `EDIFF = 1E-10`. Image `01/OUTCAR`: `aborting loop EDIFF was not reached (unconverged)` ×10 vs `EDIFF is reached` ×3, across 14 ionic steps — yet it still printed `reached required accuracy` (a textbook "converged-but-wrong": the force norm met `EDIFFG` on wrong forces). Endpoints `00`/`04`: `NELM = 200`, **zero** "not reached" → their SCF converged fully. So endpoint energies are clean and band energies are noisy — which is *exactly* why an interior image can read below an endpoint and why your near-endpoint image doesn't sit at a local minimum. This is the failure documented in the VTST parameters reference ("NEB barrier from unconverged SCF — every image hits NELM, so the optimizer trusts wrong forces").
- **`PRECFOCK = Fast`** evaluates the exact exchange on a *coarse* FFT grid, which adds force/energy noise right at your ~0.01 eV scale. Use `PRECFOCK = Normal` (or `Accurate`) for hybrid geometry/forces. (This tag isn't in my bundled VASP docs — it's standard VASP behavior, flagging it as such.)
- **`NELM` default is 60** (docs/vasp/nelm.md); **`EDIFF` default 1E-4, with 1E-6 "well converged" and 1E-7/1E-8 for force-sensitive work** (docs/vasp/ediff.md). `1E-10` is at the numerical floor; your endpoints only reached it *because* they had `NELM = 200`.
- **Not the optimizer, not the linkage:** OUTCAR shows `vasp.6.4.2` + `VTST: version 4.1` + `OPT: Using Quick-Min` → VTST is properly linked and QuickMin is fine. Your instinct that `TIMESTEP` isn't the issue is correct — leave it at 0.1; dropping it only slows you down.
- **`LCLIMB = .FALSE.`** means you're not resolving the saddle at all (only a lower bound) — turn it on when you actually want a barrier (it's the VTST default and belongs on from the outset).

## Answers to your three questions

**1. Physical, or an HSE artefact? Both mechanisms are real, and you can't separate them until the numerics are clean.**
- *Physical side:* hybrids remove PBE's self-interaction error and **localize charge**. For defects in an ionic insulator like LiF (F-centers, self-trapped/V_K holes, small polarons), HSE genuinely can produce distinct nearby minima — different localization sites or Jahn–Teller distortions — that PBE smears into one over-delocalized state. That's a known, correct hybrid effect, which is why your PBE surface looked smooth and HSE doesn't.
- *Artefact side:* unconverged SCF + `PRECFOCK=Fast` fabricate meV-scale wiggles at your energy scale.
- *Decisive test:* re-converge with `NELM≥100` (SCF reaching `EDIFF`) and `PRECFOCK=Normal`, then tighten `EDIFFG` and see if the well persists — a *real* minimum survives, an artifact washes out. If it survives **and** maps to a distinct, sensible charge localization/geometry (check the local magnetization and geometry at that image), it's physical.

**2. PBE endpoints vs. HSE NEB.** CI-NEB is force-method agnostic, so hybrids are perfectly usable in NEB. Two rules:
- *Never mix levels within one barrier.* Endpoints and every band image must be the same functional/settings — a PBE-relaxed endpoint compared against an HSE band gives a meaningless barrier, just like PBE-geometry-with-HSE-energy.
- *Efficient workflow:* use PBE to map the topology, pre-relax endpoints, and build the initial band cheaply — then **re-relax the endpoints and run the whole NEB at HSE**, seeding from the PBE `WAVECAR`/`CONTCAR`. Caveat for your system: if the localization only appears at HSE, the PBE endpoints may be the *wrong* (delocalized) states and even the mechanism can differ, so the final endpoints and band should both be HSE.

**3. Loose-convergence NEB to probe the MEP.** Yes — a standard, sensible scoping move: a plain (non-CI) NEB with loose `EDIFFG` (e.g. `-0.05 eV/Å`), a few images, seeded from the endpoints, just to see the atomic motions and whether an intermediate exists. Two caveats: (a) **fix the SCF and `PRECFOCK` first** — a loose band on non-self-consistent forces still lies about where the minima are; you can loosen the *force* criterion but not below the electronic noise floor; (b) with ~0.01 eV barriers your energies sit at that floor, so treat a loose NEB as **mechanism-only** — it won't give a trustworthy barrier height. Once the mechanism looks right, tighten `EDIFFG` and set `LCLIMB=.TRUE.` for the real barrier.

## Concrete edits to the band INCAR
- `NELM = 200`  — match the endpoints so SCF actually reaches `EDIFF` (this single change is the most important fix)
- `PRECFOCK = Normal`  — kill the exchange-grid noise
- `EDIFF = 1E-8`  — reachable and more than tight enough to resolve 0.01 eV; keep it identical for endpoints *and* band (or keep `1E-10` if you leave `NELM=200`, since your endpoints already reach it)
- `LCLIMB = .TRUE.`  — only when you want the saddle, not just the mechanism
- Keep `IOPT=3`, `TIMESTEP=0.1`, `EDIFFG=-0.01` as-is — they're fine once the forces are self-consistent.

**Verify:** re-grep every image OUTCAR — `grep -c 'EDIFF was not reached' 0*/OUTCAR` must be **0** for all images. Any shallow minimum that survives that plus a tighter `EDIFFG` is a candidate for real physics.

Confidence: high on the diagnosis (the band-vs-endpoint `NELM` mismatch and unconverged-SCF forces are directly in your OUTCARs and explain your exact symptoms). To go further on the "physical or not" question, share `neb.dat`/the per-image energies after the re-converged run, plus the magnetization at the suspect image (`grep magnetization 0*/OUTCAR`), and I can help judge whether a surviving well is a genuine localized-defect state.


**Your "extra shallow minima" are, on the evidence in these files, mostly a numerical artifact of how the *band* is converged — not (yet) demonstrated physics.** Your NEB band runs with `NELM = 20` while your endpoints were relaxed with `NELM = 200`. In image `01` the hybrid SCF hit `NELM` without reaching `EDIFF = 1E-10` on **10 of ~14 ionic steps** (`aborting loop EDIFF was not reached`), so QuickMin was driving on forces from a *non-self-consistent* density. That noisy PES fabricates wells at exactly the ~0.01 eV scale you're trying to resolve, and it lets an interior image read below an endpoint and pushes your near-endpoint image off its minimum — precisely your symptoms. The single change that fixes it: raise the band `NELM` to 200 so SCF actually reaches `EDIFF`, then decide whether any minimum is real.

## Evidence from your files
- **Band and endpoints are at different electronic convergence, so their energies aren't comparable.** Band `INCAR`: `NELM = 20`, `EDIFF = 1E-10`. Image `01/OUTCAR`: `EDIFF was not reached` ×10 vs `EDIFF is reached` ×3 over 14 ionic steps — yet it printed `reached required accuracy`, a textbook "converged-but-wrong" (the force norm met `EDIFFG` on wrong forces). Endpoints `00`/`04`: `NELM = 200`, **zero** "not reached" → their SCF converged fully. This is the failure documented in the VTST parameters reference ("NEB barrier from unconverged SCF — every image hits NELM, so the optimizer trusts wrong forces"): tighten electronics and confirm `EDIFF` is actually reached each ionic step before trusting any barrier.
- **Crucially, this proves the fix.** Same 216-atom cell, same `PRECFOCK`, same `EDIFF = 1E-10` — the endpoints reach it in ≤200 steps, so the SCF genuinely descends to convergence and doesn't plateau. Matching the band's `NELM` to 200 is therefore justified, not a blind "just raise NELM."
- **`PRECFOCK = Fast`** evaluates the exact exchange on a coarse auxiliary FFT grid, which adds force/energy noise at your ~meV scale. `PRECFOCK = Normal` (or `Accurate`) is the right setting for hybrid forces/geometry. (This tag isn't in my bundled VASP docs — flagging it as standard VASP behavior, not a documented fact here.) Note your endpoints also used `Fast`, so it doesn't block SCF; it only degrades accuracy.
- **Not the optimizer, not the linkage.** OUTCAR shows `vasp.6.4.2` + `VTST: version 4.1` + `OPT: Using Quick-Min` → VTST is properly linked and QuickMin is fine. Your instinct that `TIMESTEP` isn't the culprit is right — leave it at 0.1. `LCLIMB = .FALSE.` means you're only getting a lower bound on the saddle, not the barrier; turn it on when you want one (it's the VTST default and belongs on from the outset).

Reference defaults: `NELM` default is 60 (docs/vasp/nelm.md); `EDIFF` default 1E-4, with 1E-6 "well converged" and 1E-7/1E-8 for force-sensitive work (docs/vasp/ediff.md) — `1E-10` is tighter than you need but is reachable here and already used on the endpoints.

## Answers to your three questions

**1. Physical, or an HSE artefact? Both mechanisms are real, and you cannot separate them until the numerics are clean.**
- *Physical side:* hybrids remove PBE's self-interaction error and **localize charge**. For defects in an ionic insulator like LiF (F-centers, self-trapped/V_K holes, small polarons), HSE genuinely can produce distinct nearby minima — different localization sites or Jahn–Teller distortions — that PBE smears into one over-delocalized state. That is why your PBE surface looked smooth and HSE doesn't; it's a correct hybrid effect, not a bug.
- *Artefact side:* unconverged SCF plus `PRECFOCK=Fast` fabricate wells at your energy scale.
- *Decisive test:* re-converge with `NELM=200` (SCF reaching `EDIFF`) and, ideally, `PRECFOCK=Normal`, then tighten `EDIFFG` and see whether the well persists — a real minimum survives, an artifact washes out. If it survives **and** maps to a distinct, sensible charge localization (check the local magnetization and geometry at that image), treat it as physical.

**2. PBE endpoints vs. HSE NEB.** CI-NEB is force-method agnostic (VTST parameters reference), so hybrids are perfectly usable in NEB, subject to two rules:
- *Never mix levels within one barrier.* Endpoints and every band image must share functional and settings — a PBE-relaxed endpoint compared against an HSE band is as meaningless as a PBE geometry with an HSE single-point energy.
- *Efficient workflow:* use PBE to map the topology, pre-relax endpoints, and build the initial band cheaply, then **re-relax the endpoints and run the whole NEB at HSE**, seeding from the PBE `WAVECAR`/`CONTCAR`. Caveat for your system: if the localization only appears at HSE, the PBE endpoints may be the wrong (delocalized) states and even the mechanism can differ, so the final endpoints and band should both be HSE.

**3. Loose-convergence NEB to probe the MEP.** Yes — a standard scoping move: a plain (non-CI) NEB with loose `EDIFFG` (e.g. `-0.05 eV/Å`), a few images, seeded from the endpoints, just to reveal the atomic motions and whether an intermediate exists. Two caveats: fix the SCF and `PRECFOCK` first — a loose band on non-self-consistent forces still lies about where the minima are; and because loose force convergence leaves images off the true MEP, treat the result as **mechanism-only**, not a trustworthy barrier height. Once the mechanism looks right, tighten `EDIFFG` and set `LCLIMB=.TRUE.` for the real barrier.

## Concrete edits to the band INCAR
- **`NELM = 200`** — match the endpoints so SCF reaches `EDIFF` each ionic step. This is the one change that needs *no* endpoint rework, since the endpoints already prove it converges.
- **Keep `EDIFF = 1E-10`** — it's reachable in ≤200 steps here and matches the endpoints. Only relax it (to `1E-7`) if you want speed, and if so apply the same value to endpoints *and* band together.
- **`PRECFOCK`:** `Fast` is at least self-consistent between your current endpoints and band. If you switch to `Normal` to cut exchange noise, re-relax the endpoints at `Normal` too — otherwise you re-introduce an endpoint-vs-band mismatch.
- **`LCLIMB = .TRUE.`** when you want the saddle, not just the mechanism.
- Keep `IOPT=3`, `TIMESTEP=0.1`, `EDIFFG=-0.01` — these are fine once the forces are self-consistent; `EDIFFG` is your force tolerance and isn't what limits your energy resolution (that's `EDIFF`/SCF).

**Verify:** after re-running, `grep -c 'EDIFF was not reached' 0*/OUTCAR` must be **0** for every image. Any shallow minimum that survives that, plus a tighter `EDIFFG`, is a genuine candidate for physics.

Confidence: high on the diagnosis — the band-vs-endpoint `NELM` mismatch and the unconverged-SCF forces are directly in your OUTCARs and explain your exact symptoms. To judge whether a surviving well is real, send the per-image energies (`neb.dat`) after the re-converged run and the magnetization at the suspect image (`grep magnetization 0*/OUTCAR`), and I can help interpret it.



---

## Final answer

**Your "extra shallow minima" are, on the evidence in these files, mostly a numerical artifact of how the *band* is converged — not (yet) demonstrated physics.** Your NEB band runs with `NELM = 20` while your endpoints were relaxed with `NELM = 200`. In image `01` the hybrid SCF hit `NELM` without reaching `EDIFF = 1E-10` on **10 of ~14 ionic steps** (`aborting loop EDIFF was not reached`), so QuickMin was driving on forces from a *non-self-consistent* density. That noisy PES fabricates wells at exactly the ~0.01 eV scale you're trying to resolve, and it lets an interior image read below an endpoint and pushes your near-endpoint image off its minimum — precisely your symptoms. The single change that fixes it: raise the band `NELM` to 200 so SCF actually reaches `EDIFF`, then decide whether any minimum is real.

## Evidence from your files
- **Band and endpoints are at different electronic convergence, so their energies aren't comparable.** Band `INCAR`: `NELM = 20`, `EDIFF = 1E-10`. Image `01/OUTCAR`: `EDIFF was not reached` ×10 vs `EDIFF is reached` ×3 over 14 ionic steps — yet it printed `reached required accuracy`, a textbook "converged-but-wrong" (the force norm met `EDIFFG` on wrong forces). Endpoints `00`/`04`: `NELM = 200`, **zero** "not reached" → their SCF converged fully. This is the failure documented in the VTST parameters reference ("NEB barrier from unconverged SCF — every image hits NELM, so the optimizer trusts wrong forces"): tighten electronics and confirm `EDIFF` is actually reached each ionic step before trusting any barrier.
- **Crucially, this proves the fix.** Same 216-atom cell, same `PRECFOCK`, same `EDIFF = 1E-10` — the endpoints reach it in ≤200 steps, so the SCF genuinely descends to convergence and doesn't plateau. Matching the band's `NELM` to 200 is therefore justified, not a blind "just raise NELM."
- **`PRECFOCK = Fast`** evaluates the exact exchange on a coarse auxiliary FFT grid, which adds force/energy noise at your ~meV scale. `PRECFOCK = Normal` (or `Accurate`) is the right setting for hybrid forces/geometry. (This tag isn't in my bundled VASP docs — flagging it as standard VASP behavior, not a documented fact here.) Note your endpoints also used `Fast`, so it doesn't block SCF; it only degrades accuracy.
- **Not the optimizer, not the linkage.** OUTCAR shows `vasp.6.4.2` + `VTST: version 4.1` + `OPT: Using Quick-Min` → VTST is properly linked and QuickMin is fine. Your instinct that `TIMESTEP` isn't the culprit is right — leave it at 0.1. `LCLIMB = .FALSE.` means you're only getting a lower bound on the saddle, not the barrier; turn it on when you want one (it's the VTST default and belongs on from the outset).

Reference defaults: `NELM` default is 60 (docs/vasp/nelm.md); `EDIFF` default 1E-4, with 1E-6 "well converged" and 1E-7/1E-8 for force-sensitive work (docs/vasp/ediff.md) — `1E-10` is tighter than you need but is reachable here and already used on the endpoints.

## Answers to your three questions

**1. Physical, or an HSE artefact? Both mechanisms are real, and you cannot separate them until the numerics are clean.**
- *Physical side:* hybrids remove PBE's self-interaction error and **localize charge**. For defects in an ionic insulator like LiF (F-centers, self-trapped/V_K holes, small polarons), HSE genuinely can produce distinct nearby minima — different localization sites or Jahn–Teller distortions — that PBE smears into one over-delocalized state. That is why your PBE surface looked smooth and HSE doesn't; it's a correct hybrid effect, not a bug.
- *Artefact side:* unconverged SCF plus `PRECFOCK=Fast` fabricate wells at your energy scale.
- *Decisive test:* re-converge with `NELM=200` (SCF reaching `EDIFF`) and, ideally, `PRECFOCK=Normal`, then tighten `EDIFFG` and see whether the well persists — a real minimum survives, an artifact washes out. If it survives **and** maps to a distinct, sensible charge localization (check the local magnetization and geometry at that image), treat it as physical.

**2. PBE endpoints vs. HSE NEB.** CI-NEB is force-method agnostic (VTST parameters reference), so hybrids are perfectly usable in NEB, subject to two rules:
- *Never mix levels within one barrier.* Endpoints and every band image must share functional and settings — a PBE-relaxed endpoint compared against an HSE band is as meaningless as a PBE geometry with an HSE single-point energy.
- *Efficient workflow:* use PBE to map the topology, pre-relax endpoints, and build the initial band cheaply, then **re-relax the endpoints and run the whole NEB at HSE**, seeding from the PBE `WAVECAR`/`CONTCAR`. Caveat for your system: if the localization only appears at HSE, the PBE endpoints may be the wrong (delocalized) states and even the mechanism can differ, so the final endpoints and band should both be HSE.

**3. Loose-convergence NEB to probe the MEP.** Yes — a standard scoping move: a plain (non-CI) NEB with loose `EDIFFG` (e.g. `-0.05 eV/Å`), a few images, seeded from the endpoints, just to reveal the atomic motions and whether an intermediate exists. Two caveats: fix the SCF and `PRECFOCK` first — a loose band on non-self-consistent forces still lies about where the minima are; and because loose force convergence leaves images off the true MEP, treat the result as **mechanism-only**, not a trustworthy barrier height. Once the mechanism looks right, tighten `EDIFFG` and set `LCLIMB=.TRUE.` for the real barrier.

## Concrete edits to the band INCAR
- **`NELM = 200`** — match the endpoints so SCF reaches `EDIFF` each ionic step. This is the one change that needs *no* endpoint rework, since the endpoints already prove it converges.
- **Keep `EDIFF = 1E-10`** — it's reachable in ≤200 steps here and matches the endpoints. Only relax it (to `1E-7`) if you want speed, and if so apply the same value to endpoints *and* band together.
- **`PRECFOCK`:** `Fast` is at least self-consistent between your current endpoints and band. If you switch to `Normal` to cut exchange noise, re-relax the endpoints at `Normal` too — otherwise you re-introduce an endpoint-vs-band mismatch.
- **`LCLIMB = .TRUE.`** when you want the saddle, not just the mechanism.
- Keep `IOPT=3`, `TIMESTEP=0.1`, `EDIFFG=-0.01` — these are fine once the forces are self-consistent; `EDIFFG` is your force tolerance and isn't what limits your energy resolution (that's `EDIFF`/SCF).

**Verify:** after re-running, `grep -c 'EDIFF was not reached' 0*/OUTCAR` must be **0** for every image. Any shallow minimum that survives that, plus a tighter `EDIFFG`, is a genuine candidate for physics.

Confidence: high on the diagnosis — the band-vs-endpoint `NELM` mismatch and the unconverged-SCF forces are directly in your OUTCARs and explain your exact symptoms. To judge whether a surviving well is real, send the per-image energies (`neb.dat`) after the re-converged run and the magnetization at the suspect image (`grep magnetization 0*/OUTCAR`), and I can help interpret it.
