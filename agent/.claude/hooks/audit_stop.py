#!/usr/bin/env python3
"""Stop hook: one-time self-audit. Block once, inject an adherence checklist so
the model re-checks its draft against the diagnostic loop while it's still fresh;
stop_hook_active guards against re-firing. Fails OPEN (never wedges a run)."""
import sys, json
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)                                   # unreadable payload -> allow stop
if data.get("stop_hook_active"):                  # already audited this turn -> stop
    sys.exit(0)
CHECKLIST = (
    "SELF-AUDIT before you finish (diagnostic loop, step 5 -- do not skip):\n"
    "1. List every claim in your answer about a VASP/VTST tag, default, convergence "
    "criterion, method behavior, or script, and name the docs/ or reference/ file you "
    "opened that backs each. Any claim with no doc behind it: open the doc NOW and "
    "correct or drop it. Never assert a VASP/VTST fact from memory when a doc covers it.\n"
    "2. Name the triage row you used and the reference/*.md it points to; re-read it. "
    "If your conclusion contradicts that reference, the reference wins -- revise.\n"
    "3. EDIFFG (any negative force tolerance, eV/A) bounds FORCES, not energy resolution "
    "(that is EDIFF). Never use a force criterion to argue an energy difference is "
    "unresolved or 'noise'.\n"
    "4. If the work area had NO user files, your confidence is LOW: give the most likely "
    "simple cause and ASK for the specific files -- do not assert a particular tag or "
    "cause at high confidence.\n"
    "5. If a PRECHECK REPORT was provided (raw facts at the top of the task), confirm your "
    "answer accounts for every flagged anomaly AND every ABSENT/blank signal in it -- a "
    "blank/absent result (e.g. 'VTST banner ABSENT in all OUTCARs' while INCAR sets "
    "IOPT/IMAGES = VTST not linked) IS a finding, not 'no information'. Address any report "
    "line you skipped, or state why it is irrelevant; never silently ignore one.\n"
    "If all five already hold, the diagnosis stands as-is; otherwise correct it. Then "
    "OUTPUT ONLY the answer as your final message -- do NOT narrate this audit, keep no "
    "'self-audit' / 'audit results' preamble, and do not restate the checklist. Write a "
    "focused, well-structured essay: detailed where it matters, but cut repetition, "
    "redundant caveats, and bloat; once a point is made, move on."
)
print(json.dumps({"decision": "block", "reason": CHECKLIST}))
sys.exit(0)
