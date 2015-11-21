#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import os
import multiprocessing
from py2neo import Graph, Node
from py2neo import authenticate
from toolz import compose, map, partial
from device.switch import *


config = configparser.ConfigParser()
config.read('config.ini')
neo4j_username = config.get('neo4j', 'username')
neo4j_password = config.get('neo4j', 'password')

sw_username = config.get('switch', 'username')
sw_password = config.get('switch', 'passwd')
sw_super_password = config.get('switch', 'super_passwd')

sw_file, log_file, result_file = ('sw.txt', 'result/sw_log.txt',
                                  'result/sw_info.txt')

authenticate('61.155.48.36:7474', neo4j_username, neo4j_password)
graph = Graph("http://61.155.48.36:7474/db/data")


def clear_log():
    for f in [log_file, result_file]:
        if os.path.exists(f):
            os.remove(f)
        os.mknod(f)


def create_sw_node(r):
    area, ip, hostname, model = r.split(',')
    node = Node('Switch', area=area, ip=ip, hostname=hostname, model=model)
    return node


def import_sw(file):
    switchs = (x.strip() for x in open(file))
    list(map(lambda x: graph.create(create_sw_node(x)), switchs))


s93_card_check = partial(S93.card_check, username=sw_username,
                         password=sw_password, super_password=sw_super_password)
s85_card_check = partial(S85.card_check, username=sw_username,
                         password=sw_password, super_password=sw_super_password)
s89_card_check = partial(S89.card_check, username=sw_username,
                         password=sw_password, super_password=sw_super_password)
t64_card_check = partial(T64.card_check, username=sw_username,
                         password=sw_password, super_password=sw_super_password)


def card_entry(info):
    create_card_node = lambda x: graph.create(Node('Card', slot=x[0], name=x[1]))[0]
    mark, cards, switch = info
    with open(log_file, 'a') as flog:
        flog.write("{0}:{1}\n".format(switch, mark))
    if cards and mark == 'success':
        ip = switch.split(',')[0]
        switch_node = graph.find_one('Switch', property_key='ip', property_value=ip)
        card_nodes = map(create_card_node, cards)
        list(map(lambda x: graph.create((switch_node, 'HAS', x)), card_nodes))


def card_entry_m(lock, info):
    create_card_node = lambda x: graph.create(Node('Card', slot=x[0], name=x[1]))[0]
    mark, cards, switch = info
    with lock:
        with open(log_file, 'a') as flog:
            flog.write("{0}:{1}\n".format(switch, mark))
    if cards and mark == 'success':
        ip = switch.split(',')[0]
        with lock:
            switch_node = graph.find_one('Switch', property_key='ip', property_value=ip)
            card_nodes = map(create_card_node, cards)
            list(map(lambda x: graph.create((switch_node, 'HAS', x)), card_nodes))


def get_card(switch):
    functions = dict(S9306=s93_card_check,
                     S8508=s85_card_check,
                     S8505=s85_card_check,
                     S9303=s93_card_check,
                     S8905=s89_card_check,
                     T64G=t64_card_check)
    no_model = lambda x: ['fail', Node]
    ip, model = switch[:2]
    return functions.get(model, no_model)(ip) + [','.join(switch)]


def card_check():
    """
    :returns: TODO

    """
    clear_log()
    nodes = graph.find('Switch')
    #  nodes = graph.find('Switch', property_key='model', property_value='S9306', limit=10)
    switchs = [(x['ip'], x['model'], x['area']) for x in nodes]
    #  list(map(compose(card_entry, get_card), switchs))
    pool = multiprocessing.Pool(8)
    lock = multiprocessing.Manager().Lock()
    func = partial(card_entry_m, lock)
    list(pool.map(compose(func, get_card), switchs))
    pool.close()
    pool.join()


def main():
    pass


if __name__ == '__main__':
    main()
