#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import re
from toolz import partitionby, partition
from itertools import product

pager = "---- More ----"
prompter = "]"
logfile = sys.stdout


def telnet(ip, username, password, super_password):
    child = pexpect.spawn(
        'telnet {0}'.format(ip), encoding='ISO-8859-1')
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


def doSome(child, command):
    result = []
    child.sendline(command)
    while True:
        index = child.expect([prompter, pager], timeout=120)
        if index == 0:
            result.append(child.before)
            break
        else:
            result.append(child.before)
            child.send(" ")
            continue
    rslt = ''.join(result).replace('\x1b[42D', '')
    return rslt.replace(command + '\r\n', '', 1)


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


def get_interface(ip='', username='', password='', super_password=''):
    def port(record):
        rr = record.split()
        name, state = rr[:2]
        in_traffic, out_traffic = rr[3:5]
        in_traffic = float(in_traffic.replace('%', '')) / 100
        in_traffic = round(in_traffic, 2)
        out_traffic = float(out_traffic.replace('%', '')) / 100
        out_traffic = round(out_traffic, 2)
        logical = 'yes' if name.startswith('Eth-Trunk') else 'no'
        if name.startswith('XGiga'):
            bw = 10000
        elif name.startswith('Giga'):
            bw = 1000
        else:
            bw = 0
        return dict(name=name, state=state.upper(), bw=bw, logical=logical, in_traffic=in_traffic, out_traffic=out_traffic)

    try:
        child = telnet(ip, username, password, super_password)
        rslt = doSome(child, 'disp interface brief')
        rec = re.split(r'\r\n *', rslt)
        rec1 = [x for x in rec if re.match(r'(XGiga|Giga|Eth-)', x)]
        rec2 = [port(x) for x in rec1]

        def desc_linkagg(record):
            rslt = doSome(child, 'disp interface {name}'.format(
                name=record['name']))
            description = re.findall(r'Description:(.*)\r\n', rslt)[0]
            record['description'] = description
            if record['name'].startswith('Eth-Trunk'):
                links = re.findall(r'(X?Gigabit\S+)', rslt)
                record['linkaggs'] = links
                bw = 0
                for x in links:
                    if x.startswith('XGiga'):
                        bw = bw + 10000
                    else:
                        bw = bw + 1000
                record['bw'] = bw
            return record

        rec3 = [desc_linkagg(x) for x in rec2]
        child.sendline('quit')
        child.expect('>')
        child.sendline('quit')
        child.close()
    except Exception as e:
        return ('fail', None, ip)
    return ('success', rec3, ip)


def main():
    pass


if __name__ == '__main__':
    main()
