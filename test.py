#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect

ip="61.147.42.81"
username="zte"
passwd="zteqsc"

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
                child.close(force=True)
                break
    else:
        child.close(force=True)
else:
    child.close(force=True)


temp=result.split('\r\n')
lrslt=[x.strip(' \x08') for x in temp if x.strip(' \x08').startswith('epon')]

print lrslt
