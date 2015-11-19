#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
import sys
import configparser
import re
import T64

#  s93_pager = "---- More ----"
#  s85_pager = "---- More ----"
#  t64_pager = "--More--"
#  logfile = sys.stdout


def s89_card_check(ip='', username='', password='', super_password=''):
    return T64.card_check(ip, username, password, super_password)


def main():
    pass


if __name__ == '__main__':
    main()
