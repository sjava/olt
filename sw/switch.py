#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import pexpect

config = ConfigParser.ConfigParser()
config.read('config.ini')
username = config.get('switch', 'username')
passwd = config.get('switch', 'passwd')
super_passwd = config.get('switch', 'super_passwd')


def telnet_s93(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    child = pexpect.spawn('telnet {0}'.format(ip))
    fout = file('out.log', 'w')
    child.logfile = fout

    index = child.expect(['Username:', pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        child.close(force=True)
        return None
    child.sendline(username)

    index = child.expect(['Password:', pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        child.close(force=True)
        return None
    child.sendline(passwd)
    child.expect('>')
    child.sendline('super')

    index = child.expect(['Password:', pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        child.close(force=True)
        return None
    child.sendline(super_passwd)
    child.expect('>')
    child.sendline('sys')
    child.expect(']')

    result = []
    child.sendline('disp cu interface Eth-Trunk')
    while True:
        index = child.expect([']', '---- More ----', pexpect.EOF,
                              pexpect.TIMEOUT])
        if index == 0:
            result.append(child.before)
            child.sendline('quit')
            child.sendline('quit')
            child.close()
            return result
        elif index == 1:
            result.append(child.before)
            child.send(' ')
        else:
            child.close(force=True)
            return None
    return result


def main():
    pass


if __name__ == '__main__':
    main()
