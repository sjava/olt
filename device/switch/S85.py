#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import re
from toolz import concatv

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
    child.expect('Password:')
    child.sendline(super_password)
    child.expect('>')
    child.sendline('sys')
    child.expect(']')
    return child


def doSome(child, command):
    rslt = []
    child.sendline(command)
    while True:
        index = child.expect([prompter, pager], timeout=120)
        rslt.append(child.before)
        if index == 0:
            break
        else:
            child.send(' ')
            continue
    rslt1 = ''.join(rslt).replace(
        '\x1b[42D', '').replace(command + '\r\n', '', 1)
    return rslt1


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


def get_interface(ip='', username='', password='', super_password=''):
    def linkagg(record):
        name = re.findall(r'(Aggregation ID: \d+),', record)[0]
        description = re.findall(r'Description:(.*)\r\n', record)[0]
        links = re.findall(r'(X?Gigabit\S+)', record)
        return dict(name=name, description=description, linkaggs=links, state='UP')

    def port(record):
        name, state = re.findall(
            r'(X?Gigabit\S+).*current state : ?(.*)\r\n', record)[0]
        description = re.findall(r'Description: (.*)\r\n', record)
        desc = description[0] if description else 'none'
        return dict(name=name, state=state, description=desc)

    try:
        child = telnet(ip, username, password, super_password)
        rslt = doSome(child, 'disp link-aggregation verbose')
        rslt1 = re.split(r'\r\n *\r\n', rslt)
        rslt2 = [x for x in rslt1 if 'Aggregation ID:' in x]
        rslt3 = [linkagg(x) for x in rslt2]

        info = doSome(child, 'disp interface')
        info1 = re.split(r'\r\n *\r\n', info)
        info2 = [x for x in info1 if re.search(r'X?GigabitEthernet', x)]
        info3 = [port(x) for x in info2]

        child.sendline('quit')
        child.expect('>')
        child.sendline('quit')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ('fail', None, ip)
    return ('success', list(concatv(info3, rslt3)), ip)


def get_port_traffic(ip='', username='', password='', super_password='', port=''):
    try:
        child = telnet(ip, username, password, super_password)
        rslt = doSome(child, 'disp interface {port}'.format(port=port))
        in_traffic = re.findall(
            r'input:\s+\d+\s+packets/sec\s+(\d+)\s+bits/sec', rslt)[0]
        out_traffic = re.findall(
            r'output:\s+\d+\s+packets/sec\s+(\d+)\s+bits/sec', rslt)[0]

        child.sendline('quit')
        child.expect('>')
        child.sendline('quit')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return('fail', None, ip)
    return ('success', (in_traffic, out_traffic), ip)


def main():
    pass


if __name__ == '__main__':
    main()
