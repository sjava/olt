#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
username = config.get('switch', 'username')
password = config.get('switch', 'passwd')
super_password = config.get('switch', 'super_passwd')

s93_pager = "---- More ----"
logfile = sys.stdout


def telnet_s89t64g(ip,
                   username=username,
                   password=password,
                   super_password=super_password):
    child = pexpect.spawn('telnet {0}'.format(ip))
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


def telnet_s85(ip,
               username=username,
               password=password,
               super_password=super_password):
    child = pexpect.spawn('telnet {0}'.format(ip))
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


def telnet_s93(ip,
               username=username,
               password=password,
               super_password=super_password):
    child = pexpect.spawn('telnet {0}'.format(ip))
    child.logfile = logout

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


def s93_card_check(ip):
    try:
        result = []
        child = telnet_s93(ip)
        child.sendline('display dev')
        while True:
            index = child.expect([']', s93_pager], timeout=120)
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
    card1 = [(x[0], x[2]) for x in info if not x[0].Isdigit()]
    card2 = [('x', x[0]) for x in info if x[0].Isdigit()]
    return card1 + card2


def main():
    pass


if __name__ == '__main__':
    main()
