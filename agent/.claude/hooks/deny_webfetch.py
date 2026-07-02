#!/usr/bin/env python3
"""PreToolUse hook: block WebFetch (no direct web egress in this environment).

Exit 2 = block (stderr is shown to the model so it adapts).
"""
import sys

sys.stdin.read()                     # drain the hook payload
sys.stderr.write('Blocked: WebFetch is unavailable here (no direct web egress). '
                 'Use WebSearch for web lookups, lean on your skills/docs as the '
                 'primary source, and if you need a specific file ask the user to '
                 'upload it.\n')
sys.exit(2)
