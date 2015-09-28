#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import pexpect

config = ConfigParser.ConfigParser()
config.read('config.ini')
username = config.get('switch', 'username')
passwd = config.get('switch', 'passwd')
super_passwd = config.get('switch', 'super_passwd')


def telnet_sw(ip, username=username, passwd=passwd, super_passwd=super_passwd):
    child = pexpect.spawn('telnet {0}'.format(ip))


def main():
    pass


if __name__ == '__main__':
    main()
