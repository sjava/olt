#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import pexpect
import csv

config = ConfigParser.ConfigParser()
config.read('config.ini')
username = config.get('switch', 'username')
passwd = config.get('switch', 'passwd')
super_passwd = config.get('switch', 'super_passwd')


def telnet_s89t64g(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    try:
        child = pexpect.spawn('telnet {0}'.format(ip))
        fout = file('out.log', 'w')
        child.logfile = fout

        child.expect('Username:')
        child.sendline(username)

        child.expect('Password:')
        child.sendline(passwd)
        index = child.expect(['>', '#'])
        if index == 0:
            child.sendline('enable')
            index = child.expect('Password:')
            child.sendline(super_passwd)
            child.expect('#')

        result = []
        child.sendline('show run | in smartgroup [0-9]+ mode')
        while True:
            index = child.expect(["#", '--More--', pexpect.EOF, pexpect.TIMEOUT], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('exit')
                child.close()
                return result
            elif index == 1:
                result.append(child.before)
                child.send(' ')
                continue
            else:
                child.close(force=True)
                return None
        return result
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return None


def telnet_s85(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    try:
        child = pexpect.spawn('telnet {0}'.format(ip))
        fout = file('out.log', 'w')
        child.logfile = fout

        child.expect('Username:')
        child.sendline(username)

        child.expect('Password:')
        child.sendline(passwd)
        child.expect('>')
        child.sendline('super')
        child.expect('Password:')
        child.sendline(super_passwd)
        child.expect('>')
        child.sendline('sys')
        child.expect(']')

        result = []
        child.sendline('disp cu | in link-aggregation group .* mode')
        while True:
            index = child.expect([']', '---- More ----', pexpect.EOF,
                                  pexpect.TIMEOUT], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.sendline('quit')
                child.close()
                return result
            elif index == 1:
                result.append(child.before)
                child.send(' ')
                continue
            else:
                child.close(force=True)
                return None
        return result
    except (pexpect.EOF, pexpect, TIMEOUT):
        child.close(force=True)
        return None


def telnet_s93(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    try:
        child = pexpect.spawn('telnet {0}'.format(ip))
        fout = file('out.log', 'w')
        child.logfile = fout

        child.expect('Username:')
        child.sendline(username)

        child.expect('Password:')
        child.sendline(passwd)
        child.expect('>')
        child.sendline('super')
        index = child.expect(['Password:', '>'])
        if index == 0:
            child.sendline(super_passwd)
            child.expect('>')
            child.sendline('sys')
        else:
            child.sendline('sys')
        child.expect(']')

        result = []
        child.sendline('disp cu interface Eth-Trunk')
        while True:
            index = child.expect([']', '---- More ----', pexpect.EOF,
                                  pexpect.TIMEOUT], timeout=120)
            if index == 0:
                result.append(child.before)
                child.sendline('quit')
                child.sendline('quit')
                child.close()
                return result
            elif index == 1:
                result.append(child.before)
                child.send(' ')
                continue
            else:
                child.close(force=True)
                return None
        return result
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return None


def s93(ip):
    result = telnet_s93(ip)
    if result is None:
        return 'fail', result
    else:
        result = ''.join(result)
        result = result.replace('\x1b[42D', '')
        result = result.split('#')
        result = result[1:-1]
        result = [x.strip() for x in result if 'mode lacp' not in x]
        return 'success', result


def s85(ip):
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


def s89t64g(ip):
    result = telnet_s89t64g(ip)
    if result is None:
        return 'fail', result
    else:
        result = ''.join(result).split('\r\n')
        result = result[1:-1]
        result = [x.strip(' \x08') for x in result]
        result = set(result)
        result = [x for x in result if 'mode on' in x]
        return 'success', result


def test():
    functions = dict(s8505=s85,
                     s85=s85,
                     s8508=s85,
                     s9306=s93,
                     s8905=s89t64g,
                     t64g=s89t64g)
    with open('switch.csv', 'rb') as fp:
        reader = csv.reader(fp)
        for area, ip, name, model in reader:
            try:
                mark, reslult = functions[model.strip().lower()](ip.strip())
            except KeyError as e:
                with open('fail.txt', 'a') as flog:
                    flog.write('{0},{1},{2},{3}:model fail\n'.format(
                        area, ip, name, model))
            else:
                if mark == 'fail':
                    with open('fail.txt', 'a') as flog:
                        flog.write('{0},{1},{2},{3}:fail\n'.format(
                            area, ip, name, model))
                else:
                    with open('success.txt', 'a') as fsuccess:
                        fsuccess.write('{0},{1},{2},{3}:\n'.format(
                            area, ip, name, model))
                        for i in reslult:
                            fsuccess.write(i + '\n\n')
                        fsuccess.write('-' * 80 + '\n')


def main():
    pass


if __name__ == '__main__':
    main()
