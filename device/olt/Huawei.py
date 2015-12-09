#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import sys
import re

hw_prompt = "#"
hw_pager = "---- More.*----"
logfile = sys.stdout


def telnet(ip="", username='', password=''):
    child = pexpect.spawn('telnet {0}'.format(ip), encoding='ISO-8859-1')
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
    info = [x.replace('\x1b[37D', '').strip() for x in rslt if 'QinQ' in x]
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
        child.sendline("display cu section bbs-config | in link-aggregation")
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

    return ['success', rec, ip]


def main():
    pass


if __name__ == '__main__':
    main()
