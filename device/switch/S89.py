#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
from . import T64
import sys
import re
from toolz import partition, partitionby
from itertools import product

pager = "--More--"
logfile = sys.stdout


def telnet(ip, username, password, super_password):
    child = pexpect.spawn('telnet {0}'.format(ip), encoding='ISO-8859-1')
    child.logfile = logfile

    child.expect('Username:')
    child.sendline(username)
    child.expect('Password:')
    child.sendline(password)
    index = child.expect(['>', '#'])
    if index == 0:
        child.sendline('enable')
        child.expect('Password:')
        child.sendline(super_password)
        child.expect('#')
    return child


def card_check(ip='', username='', password='', super_password=''):
    return T64.card_check(ip, username, password, super_password)


def get_etrunk(ip='', username='', password='', super_password=''):
    try:
        result = []
        child = telnet(ip, username, password, super_password)
        child.sendline('show lacp internal')
        while True:
            index = child.expect(['#', pager])
            if index == 0:
                result.append(child.before)
                child.sendline('exit')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(' ')
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None, ip]
    rslt = ''.join(result).split('\r\n')[1:-1]
    rec = [x.replace('\x08', '').strip()
           for x in rslt if 'Smartgroup' in x or 'active' in x]

    def ff(x):
        if 'Smartgroup:' in x:
            return re.findall(r'Smartgroup:(\d+)', x)[0]
        else:
            return x.split()[0]

    rec1 = partitionby(lambda x: x.isdigit(), map(ff, rec))
    rec2 = partition(2, rec1)
    rec3 = [product(x[0][-1:], x[1]) for x in rec2]
    return ['success', rec3, ip]
