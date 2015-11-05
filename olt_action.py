#!/usr/bin/env python
# -*- coding: utf-8 -*-
import device.olt
import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')
zte_olt_username = config.get('olt', 'zte_username')
zte_olt_password = config.get('olt', 'zte_password')

hw_olt_username = config.get('olt', 'hw_username')
hw_olt_username = config.get('olt', 'hw_password')

olts_file, log_file, result_file = ('olts.txt', 'result/olt_log.txt',
                                    'result/olt_info.txt')
zte_command = "show run | in monitor session"
hw_command = ""


def olt_check():
    for f in [log_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)

    with open(olts_file) as olts, open(log_file, 'a') as flog, open(
            result_file, 'a') as fresult:
        for olt in olts:
            mark = 'fail'
            record = []
            ip, factory, area = [x.strip() for x in olt.split(',')]
            if factory.lower() == 'zte':
                mark, record = device.olt.zte_get_info(
                    ip, zte_olt_username, zte_olt_password, zte_command)
            elif factory.lower() == 'hw':
                pass
            flog.write('{0}:{1}\n'.format(olt.strip(), mark))
            if mark == 'success' and record != []:
                fresult.write('{0}:\n'.format(olt.strip(), ))
                for r in record:
                    fresult.write('{0}\n'.format(r, ))
                fresult.write('*' * 60 + '\n')


def main():
    pass


if __name__ == '__main__':
    main()
