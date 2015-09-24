#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import re
import os


def olt_svlan_check(olts_file='olt_test.txt', fail_file='result/fail.log',
                    result_file='result/olt.txt'):
    """TODO: Docstring for svlan.

    :olts_file: TODO
    :result_file: TODO
    :returns: TODO

    """
    for f in [fail_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)

    with open(olts_file) as olts:
        for olt in olts:
            mark = "fail"
            records = {}

            olt = olt.strip('\n')
            print olt
            ip, factory, area = [x.strip() for x in olt.split(',')]
            if factory.lower() == "zte":
                mark, records = zte(ip)
            elif factory.lower() == "hw":
                mark, records = huawei(ip)

            olt_check_out(olt, mark, records,
                          result_file=result_file, fail_file=fail_file)


def clear_zte_gpon(result, records):
    """TODO: Docstring for clear_zte_gpon.

    :result: TODO
    :returns: TODO

    """
    result = result.split('\r\n')
    result = [x.strip(' \x08') for x in result]
    result = result[1:-3]

    port = ''
    for x in result:
        if x.startswith('Interface'):
            port = x.replace('onu', 'olt').split(':')[0]
            continue
        if 'YES' in x:
            svlan = re.split('\s+', x)[1]
            if svlan.isdigit():
                records.setdefault(svlan, set()).add(port)
            continue
    return records


def zte_gpon(child, slots):
    """TODO: Docstring for zte_gpon.

    :child: TODO
    :slots: TODO
    :returns: TODO

    """
    mark = 'fail'
    records = {}

    for slot in slots:
        print slot
        result = ""
        child.sendline("show service-port shelf 1 slot %s" % slot)
        while True:
            index = child.expect(["--More--", "#", pexpect.EOF, pexpect.TIMEOUT])
            if index == 0:
                result += child.before
                child.send(" ")
            elif index == 1:
                result += child.before
                records = clear_zte_gpon(result, records)
                mark = "success"
                break
            else:
                mark = "fail"
                child.close(force=True)
                break
    if mark == 'success':
        child.sendline("exit")
        child.close(force=True)
    return mark, records


def zte_epon(child):
    """TODO: Docstring for zte_epon.

    :child: TODO
    :returns: TODO

    """
    index = child.sendline("show vlan-smart-qinq")
    child.expect("show vlan-smart-qinq")

    mark = "fail"
    result = ""
    records = {}

    while True:
        index = child.expect(["--More--", "#", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            result += child.before
            child.send(" ")
        elif index == 1:
            result += child.before
            child.sendline("exit")
            child.close(force=True)
            result = result.split('\r\n')
            result = [x.strip(' \x08') for x in result if x.strip(' \x08').startswith('epon')]
            result = [re.split('\s+', x) for x in result]
            for x in result:
                records.setdefault(x[5], set()).add(x[0])
            mark = "success"
            break
        else:
            child.close(force=True)
            break
    return mark, records


def zte(ip, username="", passwd=""):
    mark = "fail"
    records = {}

    child = pexpect.spawn("telnet %s" % ip)
    fout = file('1.log', 'w')
    child.logfile = fout

    try:
        child.expect("[uU]sername:")
        child.sendline(username)
        child.expect("[pP]assword:")
        child.sendline(passwd)
        child.expect(".*#")
        child.sendline("show card")
        child.expect("show card")
        index = child.expect(["--More--", "#"])
        print child.before
        temp = child.before.split('\r\n')
        if index == 0:
            child.send(' ')
        slots = [x.split()[2] for x in temp if x.startswith('1')
                 and x.find('GTGO') >= 0
                 and x.find('INSERVICE') >= 0]
        if slots:
            mark, records = zte_gpon(child, slots)
        else:
            mark, records = zte_epon(child)
    except (pexpect.EOF, pexpect.TIMEOUT):
        print "try one exception"
        mark = 'fail'
        child.close(force=True)
    return mark, records


def huawei(ip, username='', passwd=''):
    mark = "fail"
    result = ""
    records = {}

    child = pexpect.spawn("telnet %s" % ip)
    fout = file("1.log", "w")
    child.logfile = fout
    try:
        child.expect("User name:")
        child.sendline(username)
        child.expect('User password:')
        child.sendline(passwd)
        index = child.expect(['>', '---- More.*----'])
        if index == 1:
            child.send(' ')
            child.expect('>')
        child.sendline('enable')
        child.expect('#')
        child.sendline('undo terminal monitor')
        child.expect('#')
        child.sendline('disp service-port all')
        child.expect('}:')
        child.sendline('')
        while True:
            index = child.expect(["---- More.*----", "#",
                                  pexpect.EOF, pexpect.TIMEOUT])
            if index == 0:
                result += child.before
                child.send(" ")
                continue
            elif index == 1:
                result += child.before
                mark = "success"
                child.sendline("quit")
                child.expect([".*:"])
                child.sendline("y")
                child.close()
                break
            else:
                mark = "fail"
                child.close(force=True)
                break
    except (pexpect.EOF, pexpect.TIMEOUT):
        mark = 'fail'
        print "try one expetion"
        child.close(force=True)

    if mark == "success":
        result = result.split('\r\n')
        result = [x.replace("\x1b[37D", "").strip() for x in result
                  if "QinQ" in x]
        for x in result:
            x = x.split()
            svlan = x[1]
            if x[4].count('/') == 2:
                port = x[3] + '_' + x[4]
            else:
                port = x[3] + '_' + x[4] + x[5]
            records.setdefault(svlan, set()).add(port)

    return mark, records


def olt_check_out(olt, mark, records, fail_file, result_file):
    if mark == 'fail':
        with open(fail_file, 'a') as ffail:
            ffail.write('%s: %s\n' % (olt, mark))
        return
    with open(result_file, 'a') as fresult:
        fresult.write('%s:\n' % olt)
        for svlan, ports in records.items():
            if len(ports) > 1:
                fresult.write('%s svlan %s:\n' % (' ' * 4, svlan))
                for port in ports:
                    fresult.write('%s%s\n' % (' ' * 10, port))
        fresult.write('%s\n' % ('-' * 50))


def sw_check_out(sip, svlan_olt, result_file):
    if svlan_olt:
        with open(result_file, 'a') as fresult:
            fresult.write('%s:\n' % sip)
            for svlan, olts in svlan_olt.items():
                if len(olts) > 1:
                    fresult.write('%s svlan:%s\n' % (' ' * 4, svlan))
                    for olt in olts:
                        fresult.write('%s%s\n' % (' ' * 10, olt))
            fresult.write('%s\n' % ('-' * 50))


def sw_svlan_check(sw_file='sw_test.txt', olt_result_file='result/olt.txt',
                   sw_result_file='result/sw.txt', fail_file='result/fail.log'):

    for f in [fail_file, olt_result_file, sw_result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)

    with open(sw_file) as devices:
        sw = {}
        for device in devices:
            sip, olt = [x.strip() for x in device.split(',', 1)]
            sw.setdefault(sip, set()).add(olt)
    for k, v in sw.items():
        svlan_olt = {}
        for i in v:
            mark = "fail"
            records = {}
            olt_ip, factory, area = [x.strip() for x in i.split(',')]
            if factory.lower() == 'zte':
                mark, records = zte(olt_ip)
            elif factory.lower() == 'hw':
                mark, records = huawei(olt_ip)
            olt_check_out(i, mark, records,
                          fail_file=fail_file, result_file=olt_result_file)
            if mark == 'success':
                for svlan in records.keys():
                    svlan_olt.setdefault(svlan, set()).add(i)
        sw_check_out(k, svlan_olt, result_file=sw_result_file)

    with open(sw_file, 'a') as fsw:
        fsw.write('all devices checked\n')
    print 'all devices checked'

sw_svlan_check(sw_file='sw_list.txt')
