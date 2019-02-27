from lxml import etree

import requests





class ProxyMeta(type):
    def __new__(cls, name, bases, attrs):
        count = 0
        attrs['__CrawlFunc__'] = []
        for k,v in attrs.items():
            if 'Crawl_' in k:
                attrs['__CrawlFunc__'].append(k)
                count += 1
        attrs['__CrawlFuncCount__'] = count
        return type.__new__(cls, name, bases, attrs)

class FreeProxyGetter(object, metaclass=ProxyMeta):
    def get_raw_proxies(self, callback):
        proxies = []
        print('callback', callback)
        for proxy in eval('self.{}()'.format(callback)):#self.callback()
            print('Getting', proxy, 'from', callback)
            proxies.append(proxy)
        return proxies

    def Crawl_xicidaili(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        for page in range(10):
            url = 'https://www.xicidaili.com/nn/{}/'.format(page)
            try:
                r = requests.get(url, headers=headers)
                print(r.status_code)
                selector = etree.HTML(r.text)
                adrs = selector.xpath('//*[@class="odd"]/td[2]/text()')
                ports = selector.xpath('//*[@class="odd"]/td[3]/text()')
                for i in range(len(adrs)):
                    yield (adrs[i] + ':' + ports[i])
            except:
                pass

    def Crawl_kuaidaili(self):
        for page in range(10):
            url = 'https://www.kuaidaili.com/free/inha/{}/'.format(page)
            r = requests.get(url)
            selector = etree.HTML(r.text)
            adrs = selector.xpath('//*[@data-title="IP"]/text()')
            ports = selector.xpath('//*[@data-title="PORT"]/text()')
            for i in range(len(adrs)):
                # print(adrs[i] + ':' + ports[i])
                yield (adrs[i] + ':' + ports[i])

