#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect

ip=""
username=""
passwd=""

result=""

child=pexpect.spawn("telnet %s" % ip)
index=child.expect(["[uU]sername:",pexpect.EOF,pexpect.TIMEOUT])
if index==0:
    child.sendline(username)
    index=child.expect(["[pP]assword:",pexpect.EOF,pexpect.TIMEOUT])
    child.sendline(passwd)
    index=child.expect([".*#",pexpect.EOF,pexpect.TIMEOUT])
    if index==0:
        child.sendline("show vlan-smart-qinq")
        child.expect("show vlan-smart-qinq")
        while True:
            index=child.expect(["--More--","#",pexpect.EOF,pexpect.TIMEOUT])
            if index==0:
                result += child.before
                child.sendline(" ")
            elif index==1:
                result += child.before
                child.close(force=True)
                break
            else:
                print "fail"
                child.close(force=True)
                break
    else:
        child.close(force=True)
else:
    child.close(force=True)

print result
