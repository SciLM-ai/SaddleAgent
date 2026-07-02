# IVDW

> Source: <https://www.vasp.at/wiki/index.php/IVDW>

**Default:** `0` (no correction)

Selects a van der Waals **dispersion correction** (added to energy, forces, and stress — so relaxations/MD/vibrations work).

| Value | Method |
|---|---|
| `0` | None. |
| `1` / `10` | DFT-D2 (Grimme). |
| `11` | DFT-D3 (zero damping). |
| `12` | DFT-D3 (Becke-Johnson damping). |
| `13` | DFT-D4 (external package). |
| `4` | dDsC. |
| `2` / `20` | Tkatchenko-Scheffler (TS). |
| `21` | TS with iterative Hirshfeld. |
| `202` | Many-body dispersion (MBD@rsSCS). |
| `263` | MBD@rSC/FI. |

**Notes:** Common choices are `11` or `12` (DFT-D3). Not available for DFPT phonons. The legacy `LVDW=.TRUE.` implies `IVDW=1`. Some methods need extra parameters (e.g. `VDW_RADIUS`, `VDW_S6`).

**Related:** LVDW, VDW_* parameters, LUSE_VDW.
