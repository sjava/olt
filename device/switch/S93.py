#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser
import re

#  config = configparser.ConfigParser()
#  config.read('config.ini')
#  username = config.get('switch', 'username')
#  password = config.get('switch', 'passwd')
#  super_password = config.get('switch', 'super_passwd')

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
            for x in rslt if 'Present' in x and 'PowerOn' in x]
    card1 = [(x[0], x[2]) for x in info if x[0].isdigit()]
    card2 = [('x', x[0]) for x in info if not x[0].isdigit()]
    return ['success'] + [card1 + card2]


def main():
    pass


if __name__ == '__main__':
    main()
