#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import pexpect
import sqlite3
import sys
import csv

config = ConfigParser.ConfigParser()
config.read('config.ini')
username = config.get('switch', 'username')
passwd = config.get('switch', 'passwd')
super_passwd = config.get('switch', 'super_passwd')

logout = sys.stdout


def telnet_s89t64g(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    try:
        child = pexpect.spawn('telnet {0}'.format(ip))
        child.logfile = logout

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

    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        child = None
    finally:
        return child


def telnet_s85(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    try:
        child = pexpect.spawn('telnet {0}'.format(ip))
        child.logfile = logout

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
    except (pexpect.EOF, pexpect, TIMEOUT):
        child.close(force=True)
        child = None
    finally:
        return child


def telnet_s93(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    try:
        child = pexpect.spawn('telnet {0}'.format(ip))
        child.logfile = logout

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

    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        child = None
    finally:
        return child


def s93_lacp_check(ip):
    child = telnet_s93(ip)
    if child is None:
        return 'fail', None

    result = []
    child.sendline('disp cu interface Eth-Trunk')
    while True:
        index = child.expect([']', '---- More ----', pexpect.EOF,
                              pexpect.TIMEOUT],
                             timeout=120)
        if index == 0:
            result.append(child.before)
            child.sendline('quit')
            child.sendline('quit')
            child.close()
            break
        elif index == 1:
            result.append(child.before)
            child.send(' ')
            continue
        else:
            child.close(force=True)
            return 'fail', None

    result = ''.join(result)
    result = result.replace('\x1b[42D', '')
    result = result.split('#')
    result = result[1:-1]
    result = [x.strip() for x in result if 'mode lacp' not in x]
    return 'success', result


def s85_lacp_check(ip):
    child = telnet_s85(ip)
    if child is None:
        return 'fail', None

    result = []
    child.sendline('disp cu | in link-aggregation group .* mode')
    while True:
        index = child.expect([']', '---- More ----', pexpect.EOF,
                              pexpect.TIMEOUT],
                             timeout=120)
        if index == 0:
            result.append(child.before)
            child.sendline('quit')
            child.sendline('quit')
            child.close()
            break
        elif index == 1:
            result.append(child.before)
            child.send(' ')
            continue
        else:
            child.close(force=True)
            return 'fail', None

    result = ''.join(result)
    result = result.replace('\x1b[42D', '')
    result = result.split('\r\n')
    result = result[1:-1]
    result = [x for x in result if 'mode manual' in x]
    return 'success', result


def s89t64g_lacp_check(ip):
    child = telnet_s89t64g(ip)
    if child is None:
        return 'fail', None

    result = []
    child.sendline('show run | in smartgroup [0-9]+ mode')
    while True:
        index = child.expect(["#", '--More--', pexpect.EOF, pexpect.TIMEOUT],
                             timeout=120)
        if index == 0:
            result.append(child.before)
            child.sendline('exit')
            child.close()
            break
        elif index == 1:
            result.append(child.before)
            child.send(' ')
            continue
        else:
            child.close(force=True)
            return 'fail', None

    result = ''.join(result).split('\r\n')
    result = result[1:-1]
    result = [x.strip(' \x08') for x in result]
    result = set(result)
    result = [x for x in result if 'mode on' in x]
    return 'success', result


def sw_lacp_check():
    functions = dict(s8505=s85_lacp_check,
                     s8508=s85_lacp_check,
                     s9306=s93_lacp_check,
                     s9303=s93_lacp_check,
                     s8905=s89t64g_lacp_check,
                     t64g=s89t64g_lacp_check)
    with open('switch.csv', 'rb') as fp:
        reader = csv.reader(fp)
        for area, ip, name, model in reader:
            try:
                mark, reslult = functions[model.strip().lower()](ip.strip())
            except KeyError as e:
                with open('fail.txt', 'a') as ffail:
                    ffail.write('{0},{1},{2},{3}:model fail\n'.format(
                        area, ip, name, model))
            else:
                if mark == 'fail':
                    with open('fail.txt', 'a') as ffail:
                        ffail.write('{0},{1},{2},{3}:fail\n'.format(
                            area, ip, name, model))
                else:
                    with open('success.txt', 'a') as fsuccess:
                        fsuccess.write('{0},{1},{2},{3}:\n'.format(
                            area, ip, name, model))
                        for i in reslult:
                            fsuccess.write(i + '\n\n')
                        fsuccess.write('-' * 80 + '\n')

####################sw check####################


def s93_check(ip, command):
    child = telnet_s93(ip)
    if child is None:
        return 'fail', None

    result = []
    child.sendline(command)
    while True:
        index = child.expect([']', '---- More ----', pexpect.EOF,
                              pexpect.TIMEOUT],
                             timeout=120)
        if index == 0:
            result.append(child.before)
            child.sendline('quit')
            child.expect('>')
            child.sendline('quit')
            child.close()
            break
        elif index == 1:
            result.append(child.before)
            child.send(' ')
            continue
        else:
            child.close(force=True)
            return 'fail', None

    result = ''.join(result)
    result = result.replace('\x1b[42D', '')
    result = result.split('\r\n')[1:-1]
    result = [x.strip() for x in result if x.strip() != '']
    return 'success', result


def s85_check(ip, command):
    child = telnet_s85(ip)
    if child is None:
        return 'fail', None

    result = []
    child.sendline(command)
    while True:
        index = child.expect([']', '---- More ----', pexpect.EOF,
                              pexpect.TIMEOUT],
                             timeout=120)
        if index == 0:
            result.append(child.before)
            child.sendline('quit')
            child.expect('>')
            child.sendline('quit')
            child.close()
            break
        elif index == 1:
            result.append(child.before)
            child.send(' ')
            continue
        else:
            child.close(force=True)
            return 'fail', None

    result = ''.join(result)
    result = result.replace('\x1b[42D', '')
    result = result.split('\r\n')[1:-1]
    result = [x.strip() for x in result]
    return 'success', result


def s89t64g_check(ip, command):
    child = telnet_s89t64g(ip)
    if child is None:
        return 'fail', None

    result = []
    child.sendline(command)
    while True:
        index = child.expect(["#", '--More--', pexpect.EOF, pexpect.TIMEOUT],
                             timeout=120)
        if index == 0:
            result.append(child.before)
            child.sendline('exit')
            child.close()
            break
        elif index == 1:
            result.append(child.before)
            child.send(' ')
            continue
        else:
            child.close(force=True)
            return 'fail', None

    result = ''.join(result).split('\r\n')[1:-1]
    result = [x.strip(' \x08') for x in result]
    return 'success', result


def sw_check():
    functions = dict(s8505=s85_check,
                     s8508=s85_check,
                     s9306=s93_check,
                     s9303=s93_check,
                     s8905=s89t64g_check,
                     t64g=s89t64g_check)

    commands = dict(s8505='disp cu | in ^interface (XG|G)igabitEthernet',
                    s8508='disp cu | in ^interface (XG|G)igabitEthernet',
                    s9306='disp cu | in ^interface (XG|G)igabitEthernet',
                    s9303='disp cu | in ^interface (XG|G)igabitEthernet',
                    s8905='show run | in ^interface (xg|g)ei_',
                    t64g='show run | in ^interface (xg|g)ei_', )

    with open('switch.csv', 'rb') as fp:
        reader = csv.reader(fp)
        for area, ip, name, model in reader:
            area, ip, name, model = [x.strip() for x in (area, ip, name, model)
                                     ]
            try:
                f = functions[model.lower()]
                c = commands[model.lower()]
                mark, result = f(ip.strip(), c)
            except KeyError as e:
                with open('fail.txt', 'a') as ffail:
                    ffail.write('{0},{1},{2},{3}:model fail\n'.format(
                        area, ip, name, model))
            else:
                if mark == 'fail':
                    with open('fail.txt', 'a') as ffail:
                        ffail.write('{0},{1},{2},{3}:fail\n'.format(
                            area, ip, name, model))
                else:
                    con = sqlite3.connect('sw.db')
                    con.text_factory = str
                    with con:
                        for i in result:
                            con.execute(
                                "insert into sw (area,ip,name,model,interface) values (?,?,?,?,?)",
                                (area, ip, name, model, i.split()[1]))
                    con.close()

                    # with open('success.txt', 'a') as fsuccess:
                    #     fsuccess.write('{0},{1},{2},{3}:\n'.format(
                    #         area, ip, name, model))
                    #     for i in reslult:
                    #         fsuccess.write(i + '\n\n')
                    #     fsuccess.write('-' * 80 + '\n')

                    ####################################sw config##################################################


def s89t64g_conf(ip):
    child = telnet_s89t64g(ip)
    if child is None:
        return 'fail', None
    try:
        child.sendline('conf t')
        child.expect('#')
        child.sendline('enable secret level 15 wangwei2015!)')
        child.expect('#')
        child.sendline('exit')
        child.expect('#')
        child.sendline('write')
        child.expect('#')
        child.sendline('exit')
        child.close()
        return 'success', []
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return 'fail', None


def s93_conf(ip):
    child = telnet_s93(ip)
    if child is None:
        return 'fail', None
    try:
        child.sendline('super password level 3 cipher wangwei2015!)')
        child.expect(']')
        child.sendline('quit')
        child.expect('>')
        child.sendline('sa')
        child.expect('N]:?')
        child.sendline('y')
        child.expect('>', timeout=120)
        child.sendline('quit')
        child.close()
        return 'success', []
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return 'fail', None


def s85_conf(ip):
    child = telnet_s85(ip)
    if child is None:
        return 'fail', None

    try:
        child.sendline('super password level 3 cipher wangwei2015!)')
        child.expect(']')
        child.sendline('quit')
        child.expect('>')
        child.sendline('sa')
        child.expect('N]')
        child.sendline('y')
        child.expect('>', timeout=120)
        child.sendline('quit')
        child.close()
        return 'success', []
    except (pexpect.EOF, pexpect.TIMEOUT):
        child.close(force=True)
        return 'fail', None


def sw_conf():
    functions = dict(s8505=s85_conf,
                     s8508=s85_conf,
                     s9306=s93_conf,
                     s9303=s93_conf,
                     s8905=s89t64g_conf,
                     t64g=s89t64g_conf)
    with open('switch.csv', 'rb') as fp:
        reader = csv.reader(fp)
        for area, ip, name, model in reader:
            try:
                mark, reslult = functions[model.strip().lower()](ip.strip())
            except KeyError as e:
                with open('fail.txt', 'a') as ffail:
                    ffail.write('{0},{1},{2},{3}:model fail\n'.format(
                        area, ip, name, model))
            else:
                if mark == 'fail':
                    with open('fail.txt', 'a') as ffail:
                        ffail.write('{0},{1},{2},{3}:fail\n'.format(
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
