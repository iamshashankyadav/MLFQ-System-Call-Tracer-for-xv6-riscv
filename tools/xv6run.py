#!/usr/bin/env python3
"""Boot xv6 in QEMU, run a list of shell commands, and capture the output.

usage: xv6run.py <xv6-dir> <cpus> <outfile> <cmd> [cmd ...]
"""
import sys, pexpect, time

xv6, cpus, out = sys.argv[1], sys.argv[2], sys.argv[3]
cmds = sys.argv[4:]
child = pexpect.spawn("make", ["qemu", f"CPUS={cpus}"], cwd=xv6,
                      encoding="utf-8", timeout=1800, codec_errors="replace")
log = open(out, "w")
child.logfile_read = log
child.expect(r"\$ ")
for c in cmds:
    child.sendline(c)
    child.expect(r"\n\$ ")
child.sendcontrol("a"); child.send("x")
child.expect(pexpect.EOF)
log.close()
