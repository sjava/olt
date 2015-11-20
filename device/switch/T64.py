#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser
import re

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
    try:
        result = []
        power = []
        child = telnet(ip, username, password, super_password)
        child.sendline('show power')
        child.expect('#')
        power.append(child.before)
        child.sendline('show version')
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
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    info = [x.replace('\x08', '').strip()
            for x in rslt if 'Board Name' in x or '[' in x]
    slot = [re.findall(r'panel (\d+)', x)[0] for x in info if '[' in x]
    card = [x.split(':')[1].strip() for x in info if 'Board Name' in x]

    rslt1 = ''.join(power).split('\r\n')[1:-1]
    power1 = [(re.findall(r'\d+', x)[0], 'Power') for x in rslt1 if 'Work' in x and 'Power' in x]
    return ['success'] + [power1 + list(zip(slot, card))]


def main():
    pass


if __name__ == '__main__':
    main()
