#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import re
from itertools import groupby
from operator import itemgetter

ip = ""
username = ""
passwd = ""


def clear_zte_gpon(result, dict):
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
            dict.setdefault(svlan, set()).add(port)
            continue
    return dict


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
                mark="success"
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
            mark="success"
            break
        else:
            child.close(force=True)
            break
    return mark, records


def zte(ip, username="", passwd="", filename="result.txt"):
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
            child.expect("#")
            print child.before
            temp = child.before.split('\r\n')
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

def huawei(ip,username,passwd):
    """TODO: Docstring for huawei.

    :ip: TODO
    :username: TODO
    :passwd: TODO
    :returns: TODO

    """
    mark="fail"
    records={}

    child=pexpect.spawn("telnet %s" % ip)

    fout=file("1.log","w")
    child.logfile=fout

    child.expect(["User name:",pexpect.EOF,pexpect.TIMEOUT])
    child.sendline(username)
    child.expect(["User password:",pexpect.EOF,pexpect.TIMEOUT])
    child.sendline(passwd)

    index=child.expect([">","---- More.*----",
        pexpect.EOF,pexpect.TIMEOUT])
    if index<2:
        if index==1:
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
            index=child.expect(["---- More.*----","#"])
    else:
        pass


def zte_epon1(ip, username="", passwd="", filename="result.txt"):
    """TODO: Docstring for zte.

    :ip: TODO
    :username: TODO
    :passwd: TODO
    :filename: TODO
    :returns: TODO

    """
    result = ""
    mark = "success"

    child = pexpect.spawn("telnet %s" % ip)
    index = child.expect(["[uU]sername:", pexpect.EOF, pexpect.TIMEOUT])
    if index == 0:
        child.sendline(username)
        index = child.expect(["[pP]assword:", pexpect.EOF, pexpect.TIMEOUT])
        child.sendline(passwd)
        index = child.expect([".*#", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            child.sendline("show vlan-smart-qinq")
            child.expect("show vlan-smart-qinq")
            while True:
                index = child.expect(["--More--", "#", pexpect.EOF, pexpect.TIMEOUT])
                if index == 0:
                    result += child.before
                    child.send(" ")
                elif index == 1:
                    result += child.before
                    child.close(force=True)
                    break
                else:
                    child.close(force=True)
                    break
        else:
            mark = "fail"
            child.close(force=True)
    else:
        mark = "fail"
        child.close(force=True)

    if mark == "success":
        temp = result.split('\r\n')
        lrst = [x.strip(' \x08') for x in temp if x.strip(' \x08').startswith('epon')]
        lrst = [re.split('\s+', x) for x in lrst]
        lrst = sorted(lrst, key=lambda x: int(x[5]))

        with open(filename, "a") as fh:
            fh.write("%s: %s\n" % (ip, mark))
            for key, items in groupby(lrst, itemgetter(5)):
                items = list(items)
                if len(items) > 1:
                    #  print key
                    fh.write("SVLAN: %s\n" % key)
                    for i in items:
                        #  print i
                        fh.write(" ".join(i) + '\n')
                    #  print "-" * 20
                    fh.write("-" * 20 + '\n')
    else:
        with open(filename, "a") as fh:
            fh.write("%s: %s\n" % (ip, mark))
            fh.write("-" * 20 + '\n')

#  zte(ip, username, passwd)
