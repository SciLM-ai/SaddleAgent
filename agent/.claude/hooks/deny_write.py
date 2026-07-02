#!/usr/bin/env python3
"""PreToolUse hook: block file-mutating tools. This agent is inspect-only.

Exit 2 = block (stderr is shown to the model so it adapts).
"""
import sys

sys.stdin.read()                     # drain the hook payload
sys.stderr.write('Blocked: this agent is inspect-only and may not modify files. '
                 'Do not use Edit/Write/NotebookEdit/MultiEdit; inspect with '
                 'Read/Grep/Bash (grep/cat/head/tail) instead.\n')
sys.exit(2)
