#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import device.switch.T64

#  s93_pager = "---- More ----"
#  s85_pager = "---- More ----"
#  t64_pager = "--More--"
#  logfile = sys.stdout


def card_check(ip='', username='', password='', super_password=''):
    return device.switch.T64.card_check(ip, username, password, super_password)


def main():
    pass


if __name__ == '__main__':
    main()
