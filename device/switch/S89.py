#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
from . import T64
import sys
import re
from toolz import partition, partitionby
from itertools import product
from functools import reduce

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
    return rslt.replace(command + '\r\n', '', 1)


def card_check(ip='', username='', password='', super_password=''):
    return T64.card_check(ip, username, password, super_password)


def get_interface(ip='', username='', password='', super_password=''):
    def port(rec):
        name, state = re.findall(r'^([xgs]\S+) is (.*),', rec)[0]
        description = re.findall(r'Description is (.+)\r\n', rec)[0]
        bw = re.findall(r'BW\s+(\d+)\s+Kbits', rec)
        if bw:
            bw = int(bw[0]) / 1000
        else:
            bw = 0

        traffic = re.findall(
            r'utilization:\s+input\s+(\d+)%,\s+output\s+(\d+)%', rec)
        if traffic:
            in_traffic, out_traffic = traffic[0]
            in_traffic = round(float(in_traffic) / 100, 2)
            out_traffic = round(float(out_traffic) / 100, 2)
        else:
            in_traffic = 0
            out_traffic = 0
        if name.startswith('smartgroup'):
            logical = 'yes'
        else:
            logical = 'no'
        return dict(name=name, state=state, bw=bw, logical=logical,
                    in_traffic=in_traffic, out_traffic=out_traffic, description=description)

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
                port['linkaggs'] = pt
                temp = [x for x in ports if x['name'] in pt]
                in_sum = lambda x, y: x + y['in_traffic'] * y['bw']
                out_sum = lambda x, y: x + y['out_traffic'] * y['bw']
                if port['bw']:
                    in_traffic = reduce(in_sum, temp, 0) / port['bw']
                    out_traffic = reduce(out_sum, temp, 0) / port['bw']
                else:
                    in_traffic = 0
                    out_traffic = 0
                port['in_traffic'] = round(in_traffic, 2)
                port['out_traffic'] = round(out_traffic, 2)
            return port

        ports1 = [linkagg(x) for x in ports]

        child.sendline('exit')
        child.close()
    except Exception as e:
        return ('fail', None, ip)
    return ('success', ports1, ip)
