#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser

config = configparser.ConfigParser()
config.read('../config.ini')
zte_olt_username = config.get('olt', 'zte_username')
zte_olt_password = config.get('olt', 'zte_password')

hw_olt_username = config.get('olt', 'hw_username')
hw_olt_password = config.get('olt', 'hw_password')

zte_prompt = "#"
zte_pager = "--More--"
hw_prompt = "#"
hw_pager = "---- More.*----"
logfile = sys.stdout


def telnet_zte(ip="", username=zte_olt_username, password=zte_olt_password):
    child = pexpect.spawnu("telnet {0}".format(ip, ))
    child.logfile = logfile

    child.expect("[uU]sername:")
    child.sendline(username)
    child.expect("[pP]assword:")
    child.sendline(password)
    child.expect(zte_prompt)
    return child


def telnet_hw(ip="", username=hw_olt_username, password=hw_olt_password):
    child = pexpect.spawnu("telnet {0}".format(ip, ))
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


def zte_cards(ip):
    try:
        result = []
        child = telnet_zte(ip)
        child.sendline("show card")
        while True:
            index = child.expect([zte_prompt, zte_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('exit')
                break
            else:
                result.append(child.before)
                child.send(' ')
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    cards = [x.split() for x in rslt if 'INSERVICE' in x or 'STANDBY' in x]
    return ['success', [(x[2], x[4]) for x in cards]]


def zte_get_info(ip="", username="", password="", command=""):
    try:
        result = []
        child = telnet_zte(ip, username, password)
        child.sendline(command)
        while True:
            index = child.expect([zte_prompt, zte_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('exit')
                break
            elif index == 1:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    return ['success', zte_card_info(rslt)]


def zte_card_info(result):
    rslt = [x.split() for x in result if 'INSERVICE' in x or 'STANDBY' in x]
    return [(x[2], x[4]) for x in rslt]


def hw_get_info(ip="", username="", password="", command=""):
    try:
        result = []
        child = telnet_hw(ip, username, password)
        child.sendline(command)
        while True:
            index = child.expect([hw_prompt, hw_pager], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.expect(':')
                child.sendline('y')
                break
            elif index == 1:
                result.append(child.before)
                child.send(" ")
                continue
    except (pexpect.EOF, pexpect.TIMEOUT) as e:
        return ['fail', None]
    rslt = ''.join(result).split('\r\n')[1:-1]
    return ['success', hw_card_info(rslt)]


def hw_card_info(result):
    rslt = [x.split() for x in result if 'Normal' in x or 'normal' in x]
    return [(x[0], x[1]) for x in rslt]


def main():
    pass


if __name__ == '__main__':
    main()
