#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import collections
import re
import os


def hw_telnet(ip, username='', passwd=''):
    child = pexpect.spawn("telnet %s" % ip)
    fout = file("1.log", "w")
    child.logfile = fout
    try:
        child.expect("User name:")
        child.sendline(username)
        child.expect('User password:')
        child.sendline(passwd)
        index = child.expect(['>', '---- More.*----'])
        if index == 1:
            child.send(' ')
            child.expect('>')
        child.sendline('enable')
        child.expect('#')
        child.sendline('undo terminal monitor')
        child.expect('#')
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return None
    return child


def hw_mac(ip):
    """TODO: Docstring for hw_mac.

    :ip: TODO
    :returns: TODO

    """
    result = ''
    child = hw_telnet(ip)
    if child is None:
        return 'fail'
    try:
        child.sendline('display security mac-filter source')
        while True:
            index = child.expect(["---- More.*----", "#"])
            if index == 0:
                result += child.before
                child.send(" ")
                continue
            elif index == 1:
                result += child.before
                break
        print result

        if 'Total:' in result:
            return 'success'
        result = ''
        child.sendline('display mac-address all | in eth')
        while True:
            index = child.expect(["---- More.*----", "#"])
            if index == 0:
                result += child.before
                child.send(" ")
                continue
            elif index == 1:
                result += child.before
                break

        result = result.replace('\x1b[37D', '')
        result = result.split('\r\n')
        result = [x.strip() for x in result
                  if 'eth' in x and 'dynamic' in x]
        result = [x.split()[1] for x in result]
        mac_list = collections.Counter(result).most_common(4)

        child.sendline('conf')
        child.expect('#')
        for x in mac_list:
            child.sendline('security mac-filter source %s' % x[0])
            child.expect('#')

        child.sendline('quit')
        child.expect('#')
        child.sendline('quit')
        child.expect(':')
        child.sendline('y')
        child.close()
        return 'success'
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return 'fail'


def hw_mac_anti(olts='hw.txt'):
    result_file = 'result/hw.log'
    if os.path.exists(result_file):
        os.remove(result_file)
    os.mknod(result_file)

    with open(olts) as folts:
        for x in folts:
            print x
            mark = hw_mac(x.split(',')[0].strip())
            if mark == 'success':
                with open(result_file, 'a') as fresult:
                    fresult.write('%s:success\n' % x.strip())
            else:
                with open(result_file, 'a') as fresult:
                    fresult.write('%s:fail\n' % x.strip())
