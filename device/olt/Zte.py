#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser

# config = configparser.ConfigParser()
# config.read('config.ini')
# zte_olt_username = config.get('olt', 'zte_username')
# zte_olt_password = config.get('olt', 'zte_password')

# hw_olt_username = config.get('olt', 'hw_username')
# hw_olt_password = config.get('olt', 'hw_password')

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


def main():
    pass


if __name__ == '__main__':
    main()
