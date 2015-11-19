#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser
import re

pager = "---- More ----"
logfile = sys.stdout


def telnet(ip, username, password, super_password):
    child = pexpect.spawn('telnet {0}'.format(ip), encoding='ISO-8859-1')
    child.logfile = logfile

    child.expect('Username:')
    child.sendline(username)
    child.expect('Password:')
    child.sendline(password)
    child.expect('>')
    child.sendline('super')
    child.expect('Password:')
    child.sendline(super_password)
    child.expect('>')
    child.sendline('sys')
    child.expect(']')
    return child


def card_check(ip='', username='', password='', super_password=''):
    try:
        result = []
        power = []
        child = telnet(ip, username, password, super_password)
        child.sendline('display power')
        child.expect(']')
        power.append(child.before)
        child.sendline('display dev')
        while True:
            index = child.expect([']', pager])
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect('>')
                child.sendline('quit')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(' ')
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    power = ''.join(power).split('\r\n')[1:-1]
    power = [x.replace('\x1b[37D', '').strip().split()
             for x in power if 'Normal' in x]
    power = [('x', x[0]) for x in power]

    rslt = ''.join(result).split('\r\n')[1:-1]
    info = [x.replace('\x1b[37D', '').strip().split()
            for x in rslt if 'Slave' in x or 'Master' in x or 'Normal' in x]
    card = [(x[0], x[1]) for x in info]
    return ['success'] + [card + power]


def main():
    pass


if __name__ == '__main__':
    main()
