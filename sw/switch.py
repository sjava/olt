#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import pexpect

config = ConfigParser.ConfigParser()
config.read('config.ini')
username = config.get('switch', 'username')
passwd = config.get('switch', 'passwd')
super_passwd = config.get('switch', 'super_passwd')


def telnet_s85(ip, username=username, passwd=passwd, super_passwd=super_passwd):
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
    child.sendline('disp cu | in link-aggregation group .* mode')
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


def s93(ip):
    """TODO: Docstring for s93.

    :ip: TODO
    :returns: TODO

    """
    result = telnet_s93(ip)
    if result is None:
        return 'fail', result
    else:
        result = ''.join(result)
        result = result.replace('\x1b[42D', '')
        result = result.split('#')
        result = result[1:-1]
        result = [x for x in result if 'mode lacp-static' not in x]
        return 'success', result


def s85(ip):
    """TODO: Docstring for s93.

    :ip: TODO
    :returns: TODO

    """
    result = telnet_s85(ip)
    if result is None:
        return 'fail', result
    else:
        result = ''.join(result)
        result = result.replace('\x1b[42D', '')
        result = result.split('\r\n')
        result = result[1:-1]
        result = [x for x in result if 'mode manual' in x]
        return 'success', result


def main():
    pass


if __name__ == '__main__':
    main()
