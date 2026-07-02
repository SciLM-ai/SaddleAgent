# SaddleAgent

**A VASP / VTST transition-state-search debugging agent you run yourself.**

SaddleAgent points a coding agent (the [Claude Code](https://docs.claude.com/en/docs/claude-code)
CLI) at a directory of your VASP files and returns a specific diagnosis and fix
for a stuck or misbehaving saddle-point search: NEB / CI-NEB, dimer, Lanczos, and
the frequency check that confirms a saddle. It reads your files the way an expert
would (targeted greps, not whole-file dumps), checks its claims against a bundled
VASP/VTST reference library, and answers with exact `INCAR` tags, values, file
names, and commands.

The agent that ships here is the same one behind the *SaddleAgent* poster at
**ChemAI NYC 2026** (Henkelman Group, UT Austin). This repository is
self-contained: clone it, point it at your run, and it works with your own Claude
subscription. Nothing is sent anywhere except to the model you choose; the agent
only ever **reads** the files you hand it.

---

## The idea in one paragraph

The intelligence is not a fine-tuned model. It is a **skill**: a compact
debugging doctrine plus an authoritative VASP/VTST reference library, distilled
from **483 expert threads** on the Henkelman Group's support forum. That skill is
just files, so you can pair it with almost any capable model and get similar
results. In our evaluation the skill barely moved across a model generation
(87% correct-or-better on Opus 4.6, 91% on Opus 4.8), which is the whole point:
**the skill carries the score, so the model is swappable.** Because it never needs
the web, it fits private or regulated work a public chatbot cannot reach, and it
runs equally well on a safe local open-weight model.

---

## Requirements

- **Claude Code CLI** (`claude`) on your `PATH`, with an active Claude
  subscription or API key.
  Install: <https://docs.claude.com/en/docs/claude-code>
- **Python 3.8+** (standard library only; no `pip install` needed to run).

Check your setup:
```bash
claude --version      # any recent 2.x
python3 --version     # 3.8 or newer
```

## Quickstart

```bash
git clone <your-fork-url> saddleagent
cd saddleagent

# Debug your own run:
./saddleagent -d /path/to/your/neb_run \
  -q "My CI-NEB stalls at 0.3 eV/A after 200 steps and the path looks kinked. Why?"

# Or try the bundled illustrative example:
./saddleagent -d examples/neb_images_mismatch \
  -q "My CI-NEB won't start correctly and behaves as if the image count is wrong."
```

You will see a live trace of what the agent greps and reads, then the final
answer. A real run is roughly 3 to 6 minutes and a couple of dollars of usage at
the default `claude-opus-4-8` / `xhigh` settings.

### Usage

```
./saddleagent -d DIR -q "your question"      # files + question
./saddleagent -d DIR -f question.txt          # question from a file
echo "why won't this converge?" | ./saddleagent -d DIR
./saddleagent -q "what INCAR tags select the dimer method?"   # no files
```

| flag | meaning |
|---|---|
| `-d, --files DIR` | directory of your VASP input/output files |
| `-q, --question TEXT` | the problem to solve |
| `-f, --question-file FILE` | read the question from a file (`-` = stdin) |
| `-o, --output FILE` | write the answer to a file instead of stdout |
| `--model NAME` | base model (default `claude-opus-4-8`) |
| `--effort LEVEL` | reasoning effort: `low`..`max` (default `xhigh`) |
| `--no-precheck` | skip the deterministic prechecks |
| `--quiet` | suppress the live tool trace |

The live trace prints on **stderr** and the answer on **stdout**, so
`./saddleagent -d run -q "..." > answer.md` still shows progress while saving a
clean answer.

---

## Swapping the model

The whole point of the skill is that it is model-agnostic. Set `--model` (or the
`SADDLEAGENT_MODEL` env var) to any model your `claude` CLI can reach:

```bash
# a different Claude tier
./saddleagent --model claude-opus-4-6 -d run -q "..."

# a local / open-weight model served through an Anthropic-compatible endpoint
export ANTHROPIC_BASE_URL=http://localhost:8000   # your gateway
export SADDLEAGENT_MODEL=your-local-model-name
./saddleagent -d run -q "..."
```

Open-weight models have caught up: a frontier open-weight build in the Opus-4.6
class, driven by this same skill, should land near the same score, entirely on
your own hardware with no web access. That is exactly the setting a public
chatbot cannot serve.

---

## How it works

```
   your files (read-only)              bundled with the repo
   INCAR OUTCAR POSCAR ...        ts-debug skill  +  VASP/VTST/ASE docs
          |                                   |
          v                                   v
   +----------------------------------------------------------+
   |  deterministic PRECHECKS  ->  raw facts injected up top   |
   +----------------------------------------------------------+
          |
          v
   +----------------------------------------------------------+
   |  claude -p   (Read / Grep / Glob / Bash only)             |
   |  loop: hypothesize -> inspect (cheapest first) ->         |
   |        re-assess -> fix -> verify                         |
   |  five hooks keep it inspect-only and inside your dir      |
   |  a Stop hook forces a self-audit before it finishes       |
   +----------------------------------------------------------+
          |
          v
      diagnosis + concrete fix
```

**The skill (`agent/.claude/skills/ts-debug/`).** `SKILL.md` is the cross-cutting
doctrine: a triage table, the diagnostic loop, and version reflexes. It loads on
demand and carries two ground-truth stores it is told to consult rather than
answer from memory:
- `reference/*.md` - debugging judgement (NEB and dimer diagnostics, parameter
  lore, workflows).
- `docs/` - authoritative VASP/VTST/ASE facts (per-tag `INCAR` cards under
  `docs/vasp/`, methods and scripts under `docs/vtst/`, ASE under `docs/ase/`).

**Prechecks (`prechecks/precheck.py`).** Before the model runs, a deterministic
pass over your files surfaces raw facts it should never miss: `IMAGES` vs the
actual image-directory count, whether the VTST startup banner is present in the
`OUTCAR`s, endpoint atom-order sanity, convergence state, and more. These are
**facts, not conclusions** (an ABSENT signal is itself a finding), and they are
prepended to the task so the hard evidence sits up front where the model will not
overlook it. Prechecks can never block a run: any failure degrades silently to no
report.

**The sandbox (`agent/.claude/hooks/`).** Five PreToolUse/Stop hooks enforce the
box, so pointing the agent at a run cannot change anything on your machine:
- `deny_write.py` - no `Edit`/`Write`/`NotebookEdit`/`MultiEdit` (inspect-only).
- `deny_unsafe.py` - `Bash` restricted to a read-only allowlist (`grep`, `cat`,
  `head`, `tail`, `awk`, ...); no `rm`/`mv`/`cp`, Slurm, or network commands.
- `deny_webfetch.py` - no `WebFetch` (no network egress).
- `deny_jail.py` - file access confined to your files directory plus the runtime.
- `audit_stop.py` - a one-time **Stop hook** that makes the model re-check its
  draft against the diagnostic loop (every VASP/VTST claim backed by a doc it
  actually opened, every precheck line addressed) before it is allowed to finish.

The prechecks and the Stop hook exist for the same reason: as a session grows,
the skill's guidance falls far back in the context and the agent can drift.
Two cheap, deterministic nudges pull it back - the precheck hands it the hard
facts up front, and the Stop hook forces a verification pass at the end, exactly
when that guidance is buried deepest.

---

## Repository layout

```
saddleagent                 the CLI entrypoint (Python, stdlib only)
agent/                       the runtime (cwd for `claude -p`)
  CLAUDE.md                  the agent's system prompt / persona
  inject_system_prompt.md    appended answer-style guidance
  .claude/
    settings.example.json    reference config for running `claude` by hand
    skills/ts-debug/         SKILL.md + reference/*.md + docs/**
    hooks/                   the five sandbox hooks
prechecks/
  precheck.py                deterministic file prechecks (also a CLI)
  test_precheck.py           its test suite (pytest)
examples/
  neb_images_mismatch/       a small illustrative CI-NEB case to try
```

Run the precheck tests:
```bash
python3 -m pytest prechecks/test_precheck.py -q
```

Inspect the prechecks on any run directly:
```bash
python3 prechecks/precheck.py /path/to/your/run
```

---

## Notes and limits

- The agent **reads**; it does not run VASP, submit jobs, or edit files. It tells
  you what to change and why; you make the change and rerun.
- Give it the actual files. With no files it will answer from the question text
  and its own knowledge, and it will say so and ask for the specific file that
  would settle the question.
- Answers are only as good as the evidence. If a needed `OUTCAR`/`OSZICAR` was
  not shared, the agent is told to lower its confidence and ask, not to guess.
- The bundled `examples/` geometry is synthetic and illustrative. No VASP
  `POTCAR` files are distributed (they are licensed); the agent does not need
  them to diagnose a setup.

## Attribution

SaddleAgent - Sung Hoon Jung, Ilgar Baghishov, and Graeme Henkelman,
Henkelman Group, Department of Chemistry and the Oden Institute, The University
of Texas at Austin. Presented at ChemAI NYC 2026.

Licensed under the MIT License (see [LICENSE](LICENSE)).
