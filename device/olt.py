#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import sys

zte_prompt = "#"
zte_pager = "--More--"
hw_prompt = "#"
hw_pager = "---- More.*----"
logfile = sys.stdout


def telnet_zte(ip, username, password):
    child = pexpect.spawnu("telnet {0}".format(ip, ))
    child.logfile = logfile

    child.expect("[uU]sername:")
    child.sendline(username)
    child.expect("[pP]assword:")
    child.sendline(password)
    child.expect(zte_prompt)
    return child


def telnet_hw(ip, username, password):
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


def zte_get_info(ip, username, password, command):
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
        child.close(force=True)
        return 'fail', []
    result = ''.join(result)
    result = result.split('\r\n')[1:-1]
    return 'success', result


def main():
    pass


if __name__ == '__main__':
    main()
