#!/usr/bin/env python
# -*- coding: utf-8 -*-
import device.olt
import configparser
import funcy
import os
from py2neo import Graph, Node
from py2neo import authenticate

config = configparser.ConfigParser()
config.read('config.ini')
neo4j_username = config.get('neo4j', 'username')
neo4j_password = config.get('neo4j', 'password')

olts_file, log_file, result_file = ('olts.txt', 'result/olt_log.txt',
                                    'result/olt_info.txt')

authenticate('61.155.48.36:7474', neo4j_username, neo4j_password)
graph = Graph("http://61.155.48.36:7474/db/data")


def clear_log():
    for f in [log_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)


def get_power_info(olt):
    functions = dict(hw=device.olt.hw_power)
    no_company = lambda x: ['fail', None]
    ip, company = olt[:2]
    return functions.get(company, no_company)(ip) + [','.join(olt)]


def output_info(info):
    mark, result, olt = info
    with open(log_file, 'a') as logging:
        logging.write("{0}:{1}\n".format(olt, mark))
    if result and result[0] == 'Alarm' and mark == 'success':
        with open(result_file, 'a') as frslt:
            frslt.write("{0}:单电源或单路供电.\n".format(olt, ))


def power_check():
    clear_log()
    nodes = graph.find('Olt', property_key='company', property_value='hw')
    olts = [(x['ip'], x['company'], x['area']) for x in nodes]
    funcy.lmap(funcy.compose(output_info, get_power_info), olts)


def main():
    pass


if __name__ == '__main__':
    main()
