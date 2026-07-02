#!/usr/bin/env python3
"""PreToolUse hook (Bash tool): allow only read-only inspection commands.

Exit 0 = allow; exit 2 = block (stderr is shown to the model so it adapts).
"""
import json
import re
import shlex
import sys

ALLOW = {
    'grep', 'egrep', 'fgrep', 'rg', 'zgrep', 'cat', 'zcat', 'head', 'tail',
    'less', 'more', 'awk', 'sed', 'cut', 'tr', 'sort', 'uniq', 'wc', 'nl',
    'column', 'comm', 'paste', 'join', 'rev', 'tac', 'ls', 'find', 'file',
    'stat', 'du', 'df', 'basename', 'dirname', 'realpath', 'readlink', 'pwd',
    'cd', 'echo', 'printf', 'diff', 'cmp', 'md5sum', 'sha1sum', 'strings',
    'od', 'xxd', 'hexdump', 'date', 'true', 'false', 'test', '[', ':',
    'which', 'type', 'seq', 'expr', 'python3', 'python',
    # shell keywords (loops over image dirs etc.)
    'for', 'do', 'done', 'if', 'then', 'else', 'elif', 'fi', 'while', 'until',
    'case', 'esac', 'in', '!', '{', '}', 'break', 'continue',
}
WRAPPERS = {'timeout', 'nice', 'ionice', 'nohup', 'time', 'stdbuf', 'env',
            'command', 'xargs'}
DENY_RE = re.compile(
    r'\b(squeue|sbatch|scancel|scontrol|srun|salloc|sinfo|sacct|sacctmgr'
    r'|sbcast|sattach|sprio|sshare|sstat|sreport|sview|sdiag'
    r'|rm|rmdir|mv|cp|dd|mkfs|shred|truncate|mkdir|touch|ln|install|rsync'
    r'|chmod|chown|chgrp|tee|patch|curl|wget|scp|sftp|ssh|git|pip|pip3'
    r'|kill|pkill|killall)\b', re.I)


def block(msg):
    sys.stderr.write('Blocked: %s This agent is inspect-only — read files with '
                     'grep/cat/head/tail/awk; do not modify files, use Slurm, '
                     'or touch the network.\n' % msg)
    sys.exit(2)


def main():
    try:
        cmd = json.load(sys.stdin).get('tool_input', {}).get('command', '')
    except Exception:
        block('the hook payload could not be parsed.')
    if not cmd.strip():
        sys.exit(0)
    m = DENY_RE.search(cmd)
    if m:
        block("'%s' is on the deny list." % m.group(1))
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=';|&<>()')
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        block('the command could not be safely parsed.')

    expect_cmd = True          # next word token is in command position
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if t and all(c in ';|&<>()' for c in t):       # operator / redirect token
            if '>' in t:                               # output redirect
                tgt = toks[i + 1] if i + 1 < n else ''
                if t in ('>&', '>>&') and tgt.isdigit():
                    i += 2; continue                   # fd dup (2>&1)
                if tgt == '/dev/null':
                    i += 2; continue
                block("output redirection ('%s %s') writes a file." % (t, tgt))
            if '<' in t:                               # input redirect / heredoc
                i += 2; continue                       # skip the source word
            if any(c in ';|&' for c in t):
                expect_cmd = True                      # next word starts a command
            i += 1; continue                           # bare ( ) — no state change
        if expect_cmd:
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t):
                i += 1; continue                       # env assignment prefix
            word = t.rsplit('/', 1)[-1]
            if word in WRAPPERS:
                i += 1                                 # skip the wrapper itself…
                while i < n and (toks[i].startswith('-') or toks[i].isdigit()
                                 or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[i])):
                    i += 1                             # …and its flags/values
                continue                               # the next word is the real command
            if word not in ALLOW:
                block("'%s' is not an allowed read-only command." % word)
            if word == 'sed':                          # sed is read-only without -i
                j = i + 1
                while j < n and not all(c in ';|&<>()' for c in toks[j]):
                    if toks[j].startswith('-i'):
                        block("'sed -i' edits files in place.")
                    j += 1
            expect_cmd = False
        i += 1
    sys.exit(0)


main()
