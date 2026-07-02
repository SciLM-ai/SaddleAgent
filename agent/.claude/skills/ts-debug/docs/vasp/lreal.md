# LREAL

> Source: <https://www.vasp.at/wiki/index.php/LREAL>

**Allowed:** `.FALSE. | Auto (A) | On (O) | .TRUE.` · **Default:** `.FALSE.`

Whether the non-local PAW projectors are evaluated in real or reciprocal space. Real space scales with system size (not basis size), so it is much faster for large cells.

| Value | Behavior |
|---|---|
| `.FALSE.` | Reciprocal space — most accurate; **small cells**. |
| `Auto` / `A` | Real space, auto-optimized projectors — **large cells** (recommended). |
| `On` / `O` | Real space, re-optimized (not recommended). |
| `.TRUE.` | Real space from file projectors (not recommended). |

**Recommendations:** small cells (≲30 atoms) → `.FALSE.`; large cells (≳30 atoms) → `Auto`. Real space adds a small systematic error — keep the setting **consistent** across compared calculations; consider a final `.FALSE.` energy. Fine-tune with `ROPT`.

**Related:** ROPT, PREC, ENCUT.
