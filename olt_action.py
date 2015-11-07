#!/usr/bin/env python
# -*- coding: utf-8 -*-
import device.olt
import configparser
import funcy
import os

config = configparser.ConfigParser()
config.read('config.ini')
zte_olt_username = config.get('olt', 'zte_username')
zte_olt_password = config.get('olt', 'zte_password')

hw_olt_username = config.get('olt', 'hw_username')
hw_olt_password = config.get('olt', 'hw_password')

olts_file, log_file, result_file = ('olts.txt', 'result/olt_log.txt',
                                    'result/olt_info.txt')
zte_command = "show card"
hw_command = ""


def olt_check_f():
    for f in [log_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)


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
            record = record_clear(record)
            if record and mark == 'success':
                fresult.write('{0}:\n'.format(olt.strip(), ))
                for r in record:
                    fresult.write('{0}\n'.format(r, ))
                fresult.write('*' * 60 + '\n')


def olt_check_f():
    for f in [log_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)

    olts = [x.strip() for x in open(olts_file)]
    map(funcy.compose(output_info, olt_get_info), olts)


def output_info(mark, result, olt):
    with open(log_file, 'a') as logging:
        logging.write("{0}:{1}\n".format(olt, mark))
    record = result_clear(result)
    if record and mark == 'success':
        with open('result_file', 'a') as fp:
            fp.write('{0}:\n'.format(olt, ))
            for r in record:
                fp.write('{0}\n'.format(r, ))
            fp.write('*' * 60 + '\n')


def olt_get_info(olt):
    zte_get_info = funcy.partial(device.olt.zte_get_info,
                                 username=zte_olt_username,
                                 password=zte_olt_password,
                                 command=zte_command)
    hw_get_info = funcy.partial(device.olt.hw_get_info,
                                username=hw_olt_username,
                                password=hw_olt_password,
                                command=hw_command)
    no_company = lambda x: ['fail', None]
    functions = dict(zte=zte_get_info, hw=hw_get_info)
    ip, company = olt.split(',')[:2]
    return functions.get(company, no_company)(ip).append(olt)


def record_clear(record):
    if record:
        record = [x for x in record if 'ETGO' in x]
    return record

# def record_clear(record):
#     if record:
#         record = [x for x in record if 'Session 1' in x]
#     return record


def main():
    pass


if __name__ == '__main__':
    main()
