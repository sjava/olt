#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pexpect
from . import T64


def card_check(ip='', username='', password='', super_password=''):
    return T64.card_check(ip, username, password, super_password)
