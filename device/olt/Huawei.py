#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import sys
import re
from toolz import cons, concat, unique, merge_with, compose
from functools import reduce, partial

hw_prompt = "#"
hw_pager = "---- More.*----"
prompter = "#"
pager = "---- More.*----"
logfile = sys.stdout


def telnet(ip="", username='', password=''):
    child = pexpect.spawn(
        'telnet {0}'.format(ip), encoding='ISO-8859-1')
    child.logfile = logfile
    child.expect("User name:")
    child.sendline(username)
    child.expect("User password:")
    child.sendline(password)
    index = child.expect(['>', hw_pager])
    if index == 1:
        child.send(' ')
        child.expect('>')
    child.sendline('enable')
    child.expect(hw_prompt)
    child.sendline('undo terminal monitor')
    child.expect(hw_prompt)
    return child


def doSome(child, command):
    result = []
    child.sendline(command)
    while True:
        index = child.expect([prompter, pager], timeout=120)
        result.append(child.before)
        if index == 0:
            break
        else:
            child.send(' ')
            continue
    rslt = ''.join(result).replace('\x1b[37D', '')
    return rslt.replace(command + '\r\n', '', 1)


def card_check(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("display board 0")
        while True:
            index = child.expect([hw_prompt, hw_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect(':')
                child.sendline('y')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    cards = [x.replace('\x1b[37D', '').strip().split()
             for x in rslt if 'Normal' in x or 'normal' in x]
    return ['success', [(x[0], x[1]) for x in cards]]


def power_check(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("config")
        child.expect(hw_prompt)
        child.sendline("interface emu 0")
        child.expect(hw_prompt)
        child.sendline("display fan alarm")
        child.expect(hw_prompt)
        result.append(child.before)
        child.sendline("quit")
        child.expect(hw_prompt)
        child.sendline("quit")
        child.expect(hw_prompt)
        child.sendline("quit")
        child.expect(':')
        child.sendline('y')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    powerInfo = [x.replace('\x1b[37D', '').strip().split()
                 for x in rslt if 'Power fault' in x]
    return ['success', [x[2] for x in powerInfo]]


def svlan(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("display service-port all | include QinQ")
        while True:
            index = child.expect([hw_prompt, hw_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect(':')
                child.sendline('y')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    info = [x.replace('\x1b[37D', '').strip()
            for x in rslt if 'QinQ' in x]
    records = list(map(
        lambda x: re.findall(r'\s(\d+)\sQinQ.*pon\s(\d/.*/\d)\s', x)[0], info))
    svlan = [(x[1], x[0]) for x in set(records)]
    return ['success', svlan]


def hostname(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("")
        while True:
            index = child.expect([hw_prompt, hw_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect(':')
                child.sendline('y')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None, ip]
    return ['success', result[0].strip(), ip]


def zhongji(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline(
            "display cu section bbs-config | in link-aggregation")
        while True:
            index = child.expect([hw_prompt, hw_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect(':')
                child.sendline('y')
                child.close()
                break
            else:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None, ip]
    rslt = ''.join(result).split('\r\n')[1:-1]
    rec = [x.replace('\x1b[37D', '').strip().split()[2:]
           for x in rslt if 'add-member' in x]

    def port(x):
        p = x[2].split(',')
        p1 = ['/'.join((x[1], y)) for y in p]
        return list(cons(x[0], p1))

    ff = lambda x, y: merge_with(compose(unique, concat), x, y)
    rec1 = [port(x) for x in rec]
    rec2 = [{x[0]: x} for x in rec1]
    rec3 = reduce(ff, rec2, dict())
    return ['success', rec3, ip]


def get_port_traffic(child, port):
    s, p = port.rsplit('/', 1)
    child.sendline('conf')
    child.expect(prompter)
    child.sendline('interface giu {slot}'.format(slot=s))
    child.expect(prompter)
    temp = child.before
    if 'Failure:' in temp:
        child.sendline('interface eth {slot}'.format(slot=s))
        child.expect(prompter)
    rslt = doSome(child, 'disp port traffic {port}'.format(port=p))
    child.expect(prompter)
    child.sendline('quit')
    child.expect(prompter)
    child.sendline('quit')
    child.expect(prompter)
    rslt1 = rslt.split('\r\n')
    rec = [x.strip().split('=')[1] for x in rslt1 if 'octets' in x]
    rec1 = [round(int(x) * 8 / 1000000, 1) for x in rec]
    return dict(name=port, in_traffic=rec1[0], out_traffic=rec1[1])


def get_traffics(ip='', username='', password='', ports=None):
    try:
        child = telnet(ip, username, password)
        gpt = partial(get_port_traffic, child)
        traffics = [gpt(x) for x in ports]
        child.sendline('quit')
        child.expect(':')
        child.sendline('y')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None, ip]

    return ['success', traffics, ip]


def doSomething(ip='', username='', password='', command=''):
    try:
        child = telnet(ip, username, password)
        child.sendline('conf')
        child.expect(hw_prompt)
        child.sendline(command)
        index = child.expect(['n]:', hw_prompt])
        if index == 0:
            child.sendline('y')
            child.expect(hw_prompt)
        child.sendline('quit')
        child.expect(hw_prompt)
        child.sendline('quit')
        child.expect(':')
        child.sendline('y')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', ip]
    return ['success', ip]


def main():
    pass


if __name__ == '__main__':
    main()
