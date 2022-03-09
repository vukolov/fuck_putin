import requests

proxies = {
  'http': 'http://185.25.119.89:4598',
  'https': 'http://185.25.119.89:4598',
}
session = requests.Session()
session.proxies.update(proxies)

res = session.get('https://ya.ru')

print(res)