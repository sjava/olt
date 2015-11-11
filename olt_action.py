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
zte_olt_username = config.get('olt', 'zte_username')
zte_olt_password = config.get('olt', 'zte_password')

hw_olt_username = config.get('olt', 'hw_username')
hw_olt_password = config.get('olt', 'hw_password')

neo4j_username = config.get('neo4j', 'username')
neo4j_password = config.get('neo4j', 'password')

olts_file, log_file, result_file = ('olts.txt', 'result/olt_log.txt',
                                    'result/olt_info.txt')
zte_command = "show card"
hw_command = ""

authenticate('61.155.48.36:7474', neo4j_username, neo4j_password)
graph = Graph("http://61.155.48.36:7474/db/data")


def olt_check():
    for f in [log_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)

    # olts = [x.strip() for x in open(olts_file)]
    olts = graph.find('Olt',
                      property_key='company',
                      property_value='zte')
    olts = [(x['ip'], x['company'], x['area']) for x in olts]
    funcy.lmap(funcy.compose(output_info, olt_get_info), olts)


def output_info(info):
    mark, result, olt = info
    with open(log_file, 'a') as logging:
        logging.write("{0}:{1}\n".format(olt, mark))
    if result and mark == 'success':
        ip = olt.split(',')[0]
        node = graph.find_one('Olt', property_key='ip', property_value=ip)
        card_nodes = map(create_card_node, result)
        funcy.lmap(lambda x: graph.create((node, 'HAS', x)), card_nodes)


def create_card_node(card):
    node, = graph.create(Node('Card', slot=card[0], name=card[1]))
    return node


def output_info_f(info):
    mark, result, olt = info
    with open(log_file, 'a') as logging:
        logging.write("{0}:{1}\n".format(olt, mark))
    if result and mark == 'success':
        with open(result_file, 'a') as fp:
            fp.write('{0}:\n'.format(olt, ))
            for r in result:
                fp.write('{0}\n'.format(r[1], ))
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
    # ip, company = olt.split(',')[:2]
    ip, company = olt[:2]
    return functions.get(company, no_company)(ip) + [','.join(olt)]


def result_clear(record):
    if record:
        record = [x for x in record if 'GTGO' in x]
    return record


def main():
    pass


if __name__ == '__main__':
    main()
