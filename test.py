#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import re
from itertools import groupby
from operator import itemgetter


def svlan(olts_file, result_file):
    """TODO: Docstring for svlan.

    :olts_file: TODO
    :result_file: TODO
    :returns: TODO

    """
    with open(olts_file) as olts, open(result_file, 'w') as fout:
        for olt in olts:
            mark = "fail"
            records = {}

            olt1 = olt.strip('\n')
            print olt1
            olt = olt1.split(',')
            if olt[1].lower() == "zte":
                mark, records = zte(olt[0], "", "")
            elif olt[1].lower() == "hw":
                mark, records = huawei(olt[0], "", "")

            fout.write("%s: %s\n" % (olt1, mark))
            if mark == "success":
                for svlan, ports in records.items():
                    if len(ports) > 1:
                        fout.write("%s svlan:%s\n" % (' ' * 2, svlan))
                        for port in ports:
                            fout.write("%s %s\n" % (' ' * 4, port))
            fout.write("%s\n\n" % ('*' * 50))


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
    """TODO: Docstring for zte.

    :ip: TODO
    :username: TODO
    :passwd: TODO
    :filename: TODO
    :returns: TODO

    """
    mark = "fail"
    records = {}

    child = pexpect.spawn("telnet %s" % ip)

    fout = file('1.log', 'w')
    child.logfile = fout

    index = child.expect(["[uU]sername:", pexpect.EOF, pexpect.TIMEOUT])
    if index == 0:
        child.sendline(username)
        index = child.expect(["[pP]assword:", pexpect.EOF, pexpect.TIMEOUT])
        child.sendline(passwd)
        index = child.expect([".*#", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            child.sendline("show card")
            child.expect("show card")
            index = child.expect(["--More--", "#", pexpect.EOF, pexpect.TIMEOUT])
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
        else:
            child.close(force=True)
    else:
        child.close(force=True)
    return mark, records


def huawei(ip, username, passwd):
    """TODO: Docstring for huawei.

    :ip: TODO
    :username: TODO
    :passwd: TODO
    :returns: TODO

    """
    mark = "fail"
    result = ""
    records = {}

    child = pexpect.spawn("telnet %s" % ip)

    fout = file("1.log", "w")
    child.logfile = fout

    index = child.expect(["User name:", pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        child.close(force=True)
        return mark, records
    child.sendline(username)
    index = child.expect(["User password:", pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        child.close(force=True)
        return mark, records
    child.sendline(passwd)

    index = child.expect([">", "---- More.*----",
        pexpect.EOF, pexpect.TIMEOUT])
    if index < 2:
        if index == 1:
            child.send(" ")
            child.expect(">")
        child.sendline("enable")
        child.expect(["#"])
        child.sendline("undo terminal monitor")
        child.expect(["#"])
        child.sendline("disp service-port all")
        child.expect(["}:"])
        child.sendline("")
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
    else:
        mark = "fail"
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
