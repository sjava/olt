#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
from . import T64
import sys
import re
from toolz import partition, partitionby
from itertools import product

pager = "--More--"
prompt = "#"
logfile = sys.stdout


def telnet(ip, username, password, super_password):
    child = pexpect.spawn(
        'telnet {0}'.format(ip), encoding='ISO-8859-1')
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


def doSome(child, command):
    result = []
    child.sendline(command)
    while True:
        index = child.expect([prompt, pager], timeout=120)
        if index == 0:
            result.append(child.before)
            break
        else:
            result.append(child.before)
            child.send(' ')
            continue
    rslt = ''.join(result).replace('\x08', '')
    return rslt.strip(command + '\r\n')


def card_check(ip='', username='', password='', super_password=''):
    return T64.card_check(ip, username, password, super_password)


def get_interface(ip='', username='', password='', super_password=''):
    def port(rec):
        name, state = re.findall(r'^([xgs]\S+) is (.*),', rec)[0]
        description = re.findall(r'Description is (.+)\r\n', rec)[0]
        return dict(name=name, state=state, description=description)

    try:
        child = telnet(ip, username, password, super_password)
        rslt = doSome(child, 'show interface')
        rec1 = re.split(r'\r\n +\r\n *', rslt)[:-1]
        rec2 = [x for x in rec1 if re.search(
            r'^[xgs]\S+ is .*,', x)]
        ports = [port(x) for x in rec2]

        def linkagg(port):
            if port["name"].startswith('smartgroup'):
                id = port["name"].replace('smartgroup', '')
                rslt = doSome(
                    child, 'show lacp {id} internal'.format(id=id))
                rslt1 = rslt.split('\r\n')
                pt = [x.split()[0] for x in rslt1 if 'active' in x]
                if pt:
                    port['linkaggs'] = pt
            return port

        ports1 = [linkagg(x) for x in ports]

        child.sendline('exit')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ('fail', None, ip)
    return ('success', ports1, ip)
