#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import re
from toolz import partitionby, partition
from itertools import product

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
    index = child.expect(['Password:', '>'])
    if index == 0:
        child.sendline(super_password)
        child.expect('>')
        child.sendline('sys')
    else:
        child.sendline('sys')
    child.expect(']')
    return child


def card_check(ip='', username='', password='', super_password=''):
    try:
        result = []
        child = telnet(ip, username, password, super_password)
        child.sendline('display dev')
        while True:
            index = child.expect([']', pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect('>')
                child.sendline('quit')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    info = [x.replace('\x1b[37D', '').strip().split()
            for x in rslt if 'Present' in x and 'Registered' in x]
    card1 = [(x[0], x[2]) for x in info if x[0].isdigit()]
    card2 = [('x', x[0]) for x in info if not x[0].isdigit()]
    return ['success'] + [card1 + card2]


def get_etrunk(ip='', username='', password='', super_password=''):
    try:
        result = []
        child = telnet(ip, username, password, super_password)
        child.sendline('display eth-trunk')
        while True:
            index = child.expect([']', pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect('>')
                child.sendline('quit')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None, ip]
    rslt = ''.join(result).split('\r\n')[1:-1]
    rec = [x.replace('\x1b[42D', '').strip()
           for x in rslt if 'LAG ID:' in x or 'Selected' in x]

    def ff(x):
        if 'LAG ID:' in x:
            return re.findall(r'LAG ID: (\d+)', x)[0]
        else:
            return x.split()[0]

    rec1 = partitionby(lambda x: x.isdigit(), map(ff, rec))
    rec2 = partition(2, rec1)
    rec3 = [product(x[0][-1:], x[1]) for x in rec2]
    return ['success', rec3, ip]


def main():
    pass


if __name__ == '__main__':
    main()
