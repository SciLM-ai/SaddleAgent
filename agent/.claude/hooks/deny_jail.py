#!/usr/bin/env python3
"""PreToolUse hook: confine all file access to the CURRENT case's work area.

Allowed roots:
  * this hook's runtime dir  (agent/ — CLAUDE.md + the ts-debug skill)
  * the case's files dir in $SADDLEAGENT_FILES_DIR (empty if the run passed no
    files -> the agent must answer from the question text alone)
  * temp dirs ($TMPDIR, /tmp)

Read/Grep/Glob: path args are realpath-checked (robust). Bash: best-effort -
the command is split on shell operators; in each segment every absolute-path
token must resolve under a root, '..' is blocked, and `cd` may not leave the
area (bare `cd`, ~, $HOME, - all escape to $HOME). Exit 0 = allow; 2 = block.
"""
import json
import os
import re
import shlex
import sys

_HOOK = os.path.realpath(__file__)
RUNTIME = os.path.dirname(os.path.dirname(os.path.dirname(_HOOK)))  # <rt>/.claude/hooks/x.py


def _roots():
    out = []
    for c in (RUNTIME, '/tmp', os.environ.get('TMPDIR') or '',
              os.environ.get('SADDLEAGENT_FILES_DIR') or ''):
        if not c:
            continue
        try:
            out.append(os.path.realpath(c))
        except Exception:
            pass
    return out


ROOTS = _roots()


def _under(path):
    try:
        rp = os.path.realpath(path)
    except Exception:
        return False
    return any(rp == r or rp.startswith(r + os.sep) for r in ROOTS)


def block(msg):
    fd = os.environ.get('SADDLEAGENT_FILES_DIR') or '(this run passed no files)'
    sys.stderr.write(
        "Blocked: %s. You may ONLY read the CURRENT case's files. Work area: %s . "
        "Use absolute paths under that directory; '..', other directories, $HOME, "
        "and searches outside the work area are off-limits. If there are no files, "
        "answer from the question text and your own knowledge.\n" % (msg, fd))
    sys.exit(2)


def _static_prefix(p):                       # glob/path up to the first wildcard
    return re.split(r'[*?\[]', p, 1)[0]


try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)                              # unparseable -> let other hooks decide
name = payload.get('tool_name', '')
ti = payload.get('tool_input', {}) or {}

if name in ('Read', 'Grep', 'Glob'):
    cands = [ti.get('file_path'), ti.get('path')]
    pat = ti.get('pattern') or ''
    if name == 'Glob' and pat.startswith('/'):
        cands.append(_static_prefix(pat))
    for p in cands:
        if p and not _under(p):
            block("path '%s' is outside your work area" % p)
    sys.exit(0)

if name == 'Bash':
    cmd = ti.get('command', '') or ''
    for seg in re.split(r'&&|\|\||[;&|\n]', cmd):    # analyze each sub-command
        seg = seg.strip()
        if not seg:
            continue
        try:
            toks = shlex.split(seg, posix=True)
        except Exception:
            toks = seg.split()
        if not toks:
            continue
        for t in toks:                               # no parent-dir traversal
            if re.search(r'(^|/)\.\.(/|$)', t):
                block("the command uses '..' (parent-directory traversal)")
        for t in toks:                               # absolute paths must be in-area
            if t.startswith('/') and not _under(os.path.normpath(t)):
                block("absolute path '%s' is outside your work area" % t)
        if toks[0] == 'cd':                          # cd must not escape to $HOME/etc
            tgt = toks[1] if len(toks) > 1 else ''
            if (not tgt) or tgt in ('-', '~') or tgt.startswith('~') or '$HOME' in tgt \
               or tgt.startswith('$'):
                block("`cd %s` leaves the work area" % (tgt or '(home)'))
    sys.exit(0)

sys.exit(0)
