**Root cause: the POTCAR in your NEB directory lists the two species in the opposite order from your POSCARs (and from your endpoint runs), so for the band images VASP put the F pseudopotential on the Li sublattice and Li_sv on the F sublattice.** VASP builds the POTCAR as one block per species *in the same order the species appear in the POSCAR*, and it matches those blocks to the POSCAR atom blocks positionally. Your POSCARs are all `Li F / 108 108` (Li block first), but the band's POTCAR is concatenated `F` then `Li_sv`. Because both blocks hold 108 atoms and the total electron count is unchanged (108·7 + 108·3 = 108·3 + 108·7 = 1080), VASP throws no error — it just silently computes a different, physically meaningless crystal whose absolute energy happens to land ~8–13 eV below your true endpoints.

### Evidence

The species-to-block mapping is printed in each OUTCAR and it flips between the two groups:

| | POTCAR order (TITEL) | Block-1 species (POMASS / ZVAL) | NBANDS | VTST banner |
|---|---|---|---|---|
| Endpoints `OUTCAR00`, `OUTCAR08` | Li_sv, F | Li (7.01 / 3.00) ✅ | 758 | absent (plain relaxations) |
| Band `OUTCAR01–07` | **F, Li_sv** | **F (19.00 / 7.00)** ❌ | 757 | VTST 4.1 |

So in the band, block 1 — the 108 Li lattice sites — carries `POMASS=19.00, ZVAL=7.00` (fluorine), and the F sites carry Li_sv. Everything else you checked genuinely does match across all nine runs: ENCUT 400, single Γ-point, PBE (`LEXCH=PE`), `ISPIN=2`, 216 ions, `NELECT=1080`, cubic 12.079 Å cell, VASP 6.4.2. That is exactly why your consistency check passed — POTCAR *species order* is the one axis it didn't cover.

The energies confirm the swap rather than any real physics. `neb.dat`: endpoint 0 = 0.00, endpoint 8 = **+4.83 eV** — a sensible F Frenkel-pair formation energy — while interior images 1–7 sit at **−5.7 to −8.4 eV**. In absolute terms the interior images (−1053.9 to −1056.7 eV) fall *below the near-perfect endpoint* (−1048.24 eV). A defected, mid-migration configuration cannot be more stable than the intact crystal; an interior image below both endpoints is the diagnostic fingerprint of an endpoints↔band input mismatch, independent of how cleanly the band converged. VASP still located a maximum because forces still vary *within* this internally-consistent-but-wrong band.

### Fix

1. Rebuild the NEB POTCAR in the **same order as the POSCAR** (Li first), the order your endpoints already used:
   ```
   cat <potpath>/Li_sv/POTCAR <potpath>/F/POTCAR > POTCAR
   grep TITEL POTCAR      # must read Li_sv, then F
   ```
2. Don't reuse images 01–07 — they relaxed under the wrong forces. Regenerate the band from your relaxed endpoints and rerun (identical CLI for either script; `nebmake.py` additionally applies IDPP interpolation by default):
   ```
   nebmake.pl 00/POSCAR 08/POSCAR 7      # 7 = number of interior images
   ```
   Keep `00/` and `08/` as-is — those endpoints were computed with the correct ordering. Copy your endpoint INCAR verbatim and append only the NEB-control tags; don't post-hoc "correct" energies.
3. Close the remaining consistency gap: your endpoints were run with a non-VTST build (`May 29 2025`) and the band with the VTST-patched build (`Jun 3 2025`). Both are VASP 6.4.2/PBE so this is secondary to the POTCAR swap, but for a clean energy scale run (or re-single-point) the endpoints with the same binary and confirm the two endpoint OUTCARs agree with each other on every DFT tag.
4. Sanity check after the first ionic step: `grep 'POMASS\|ZVAL' OUTCAR01` should now read `7.01 19.00` / `3.00 7.00`, and every interior energy should fall **between** 0 and ~+4.8 eV, not below.

**Confidence: very high** — the POMASS/ZVAL swap in the OUTCARs is direct proof and explains both the magnitude and the sign of the shift. Two notes on scope: the automated precheck reported "no files" only because yours are named non-standardly (`POSCARxx.vasp`, `OUTCARxx` under `u0/`), so its endpoint-vs-band consistency check never ran — it isn't a clean bill of health. And no INCAR was included; I didn't need it here (the band's VTST 4.1 banner confirms the NEB machinery ran), but if the corrected run misbehaves, send the INCAR and I'll check the IOPT/SPRING/EDIFFG/IMAGES deck. One thing to verify on your side: that the image POSCARs you actually submitted were Li-first (the copies on disk are) — if any dir paired an F-first POSCAR with the F-first POTCAR, the chemistry there would be right but its atom ordering would then mismatch the endpoints. Either way the cure is one consistent Li-then-F ordering across POTCAR, POSCAR, and both endpoints.
