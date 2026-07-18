# Topic 15777 — Cores for NEB

Graeme Henkelman (the expert who answered the original thread) reviewed SaddleAgent's answer to this question and left a grader note. This example pairs that note with the exact answer it grades, the original question, and the true expert answer.

- **Graded answer:** `SaddleAgent (with Opus 4.8)`  ·  generated 2026-06-17
- **Grader:** Graeme Henkelman

## Graeme's grader note

> AI response is accurate.

## Original question

**anirudhnk2** (2024-02-13 15:50):

Hello,

Does an NEB job need all cores to be run on different nodes? Or can it run on a single node? Since the supercomputer that I work with prefers all the work to not be distributed....

---

**anirudhnk2** (2024-02-13 18:27):

Thank you for your reply.

## Expert answer (forum ground truth)

**graeme** (2024-02-13 18:00):

either is fine

## The graded AI answer (SaddleAgent (with Opus 4.8))

## Bottom line

**A single node is completely fine — NEB has no "must span nodes" rule.** VASP parallelizes the images *internally* over MPI ranks; the only hard constraint is that **`IMAGES` must divide your total MPI rank count** (≥1 rank per image). Where those ranks physically sit — one node or many — is free, so pack the whole band onto one node exactly the way your cluster prefers.

## What's actually going on

NEB is not "one independent job per image that you scatter across nodes." All images are **one tightly MPI-coupled VASP process** that advances every image together each ionic step. You reuse your **single-point submit script unchanged** — the only required edit is adding `IMAGES=N` to the INCAR (N = interior images). VASP reads that and distributes the images itself across whatever ranks the scheduler gave you (per `docs/vtst/neb.md` + `reference/workflows.md`).

So "don't distribute the work" is not a problem — it's the easy case.

## The one rule you must satisfy

**Total MPI ranks = k × `IMAGES`** (integer k ≥ 1). Examples on a single node:

- 64-core node, `IMAGES=4` → 64/4 = 16 cores per image. ✅

- 64-core node, `IMAGES=5` → 64 not divisible by 5 → surplus image dirs never populate. ❌ Use `IMAGES=4` or `IMAGES=8`, or request 60/65 cores.

`NPAR`/`NCORE`/`KPAR` only partition cores *within* an image — they do **not** set the image count, so raising them adds no images (`docs/vasp/npar.md`). Only matching total ranks to `IMAGES` does.

## Two things to confirm

1. **MPI build, launched under a launcher.** Use `vasp_std` (an MPI build), launched via `mpirun`/your scheduler's launcher — not a serial binary and not run bare. A serial binary can't form image teams (only one image runs, no per-image `OUTCAR`); an MPI binary launched without its launcher collapses every rank to one (`running on 1 nodes` in OUTCAR, `IMAGES` silently cut to 1).

2. **GPU only:** if you're on a GPU build, GPU VASP binds **one rank per GPU**, so you need `IMAGES ≤ #GPUs`. CPU runs can oversubscribe freely; GPU cannot. (Doesn't apply to a CPU build.)

Memory budget: ~1–2 GB/core covers a typical 50–200-atom NEB; only hybrids want more.

**Confidence: high.** If you tell me your node's core count and how many images you're running, I'll give you the exact `IMAGES` (and `NCORE`) values to put in the INCAR and the matching `#SBATCH` core request.
