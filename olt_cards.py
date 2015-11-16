#!/usr/bin/env python
# -*- coding: utf-8 -*-
import device.olt
import configparser
import funcy
import os
from py2neo import Graph, Node
from py2neo import authenticate
from toolz import compose, map

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


def get_cards(olt):
    functions = dict(zte=device.olt.zte_cards, hw=device.olt.hw_cards)
    no_company = lambda x: ['fail', None]
    ip, company = olt[:2]
    return functions.get(company, no_company)(ip) + [','.join(olt)]


def create_card_node(card):
    node, = graph.create(Node('Card', slot=card[0], name=card[1]))
    return node


def output_info(info):
    mark, result, olt = info
    with open(log_file, 'a') as logging:
        logging.write("{0}:{1}\n".format(olt, mark))
    if result and mark == 'success':
        ip = olt.split(',')[0]
        node = graph.find_one('Olt', property_key='ip', property_value=ip)
        card_nodes = list(map(create_card_node, result))
        list(map(lambda x: graph.create((node, 'HAS', x)), card_nodes))
    return


def import_cards():
    clear_log()
    nodes = graph.find('Olt', property_key='ip', property_value='222.188.51.211')
    #  nodes = graph.find('Olt', property_key='company', property_value='zte')
    # ip = [x.strip('\r\n') for x in open('ip.csv')]
    # nodes = [graph.find_one('Olt',
    #                         property_key='ip',
    #                         property_value=x) for x in ip]
    #  nodes = graph.find('Olt', property_key='ip', property_value='61.147.63.247')
    olts = [(x['ip'], x['company'], x['area']) for x in nodes]
    list(map(compose(output_info, get_cards), olts))


def main():
    pass

if __name__ == '__main__':
    main()
