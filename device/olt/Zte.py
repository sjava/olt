#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser
from itertools import product
from toolz import unique
import re

zte_prompt = "#"
zte_pager = "--More--"
logfile = sys.stdout


def telnet(ip="", username="", password=""):
    child = pexpect.spawn('telnet {0}'.format(ip), encoding='ISO-8859-1')
    child.logfile = logfile

    child.expect("[uU]sername:")
    child.sendline(username)
    child.expect("[pP]assword:")
    child.sendline(password)
    child.expect(zte_prompt)
    return child


def card_check(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("show card")
        while True:
            index = child.expect([zte_prompt, zte_pager], timeout=120)
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
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    cards = [x.replace('\x08', '').strip().split()
             for x in rslt if 'INSERVICE' in x or 'STANDBY' in x]
    return ['success', [(x[2], x[3]) for x in cards]]


def epon_svlan(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("show vlan-smart-qinq")
        while True:
            index = child.expect([zte_prompt, zte_pager], timeout=120)
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
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    records = [x.replace('\x08', '').strip().split() for x in rslt
               if 'OK' in x]
    return ['success', [(x[0], x[5]) for x in records]]


def gpon_svlan(ip='', username='', password='', slots=None):
    ports = product(slots, range(1, 9))
    cmds = map(
        lambda x: "show service-port interface gpon-olt_1/{0}/{1}".format(x[0], x[1]),
        ports)
    try:
        svlan = []
        child = telnet(ip, username, password)
        for cmd in cmds:
            result = []
            child.sendline(cmd)
            while True:
                index = child.expect([zte_prompt, zte_pager], timeout=120)
                if index == 0:
                    result.append(child.before)
                    break
                else:
                    result.append(child.before)
                    child.send(' ')
                    continue
            r = ''.join(result).split('\r\n')[1:-1]
            v = [x.replace('\x08', '').strip().split()[1]
                 for x in r if 'OK' in x and 'YES' in x]
            v1 = [x for x in v if x.isdigit()]
            p = re.findall(r'\d/\d{1,2}/\d', cmd)
            svlan += product(p, unique(v1))
        child.sendline('exit')
        child.close()
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]

    return ['success', svlan, ip]


def hostname(ip='', username='', password=''):
    try:
        result = []
        child = telnet(ip, username, password)
        child.sendline("")
        while True:
            index = child.expect([zte_prompt, zte_pager], timeout=120)
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
    return ['success', result[0].strip(), ip]


def main():
    pass


if __name__ == '__main__':
    main()
