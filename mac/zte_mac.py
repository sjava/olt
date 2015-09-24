#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import re
import os


def zte_telnet(ip, username='', passwd=''):
    """TODO: Docstring for zte_telnet.

    :ip: TODO
    :username: TODO
    :passwd: TODO
    :returns: TODO

    """
    child = pexpect.spawn("telnet %s" % ip)
    fout = file('1.log', 'w')
    child.logfile = fout

    try:
        child.expect("[uU]sername:")
        child.sendline(username)
        child.expect("[pP]assword:")
        child.sendline(passwd)
        child.expect(".*#")
    except (pexpect.EOF, pexpect.TIMEOUT):
        print "%s:telnet fail" % ip
        child.close(force=True)
        return None
    return child


def mac(record):
    """TODO: Docstring for mac.

    :record: TODO
    :returns: TODO

    """
    try:
        ip = record.split(',')[0].strip()
        child = zte_telnet(ip)
        if child is None:
            return 'fail'
        else:
            child.sendline('conf t')
            child.expect('#')
            child.sendline('security mac-spoofing-trap enable')
            child.expect('#')
            child.sendline('security mac-anti-spoofing enable')
            child.expect('#')
            child.sendline('exit')
            child.expect('#')
            child.sendline('exit')
            child.close()
            return 'success'
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return 'fail'


def zte_mac_anti(olts='zte.txt'):
    result_file = 'result/zte.log'
    if os.path.exists(result_file):
        os.remove(result_file)
    os.mknod(result_file)

    with open(olts) as folts:
        for x in folts:
            print x
            mark = mac(x)
            if mark == 'success':
                with open(result_file, 'a') as fresult:
                    fresult.write('%s:success\n' % x.strip())
            else:
                with open(result_file, 'a') as fresult:
                    fresult.write('%s:fail\n' % x.strip())
