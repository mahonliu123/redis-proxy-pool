import time
from multiprocessing import Process
import asyncio
import aiohttp
from aiohttp import ClientResponseError, ServerDisconnectedError, ClientConnectorError
from aiohttp import ClientProxyConnectionError as ProxyConnectionError
from Getter import FreeProxyGetter
from error import ResourceDepletionError
from settings import POOL_LOWER_PROXIES, POOL_UPPER_PROXIES, POOL_CHECK_TIME, get_proxy_timeout, \
    Valid_Check_Cycle, TEST_API
from db import RedisClient



class ValidityTester:
    test_api = TEST_API
    def __init__(self):
        self.raw_proxies = None

    def set_raw_proxies(self, proxies):
        self.raw_proxies = proxies
        self.conn = RedisClient()

    async def test_single_proxy(self, proxy):
        '''
        测试一个代理，如果有效，则将其put进可用代理队列右侧

        '''
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    if isinstance(proxy, bytes):
                        proxy = proxy.decode('utf-8')
                    real_proxy = 'http://' + proxy
                    print('Testing', real_proxy)
                    async with session.get(self.test_api, proxy=real_proxy, timeout=get_proxy_timeout) as response:
                        print(response.status)
                        if response.status == 200:
                            print('Valid', proxy)
                            # 若代理有效, 则将其加入队列中并且设置其优先级分数为最高
                            self.conn.max(proxy)
                except (ProxyConnectionError, TimeoutError, ValueError):
                    print('Invalid', proxy)
                    # 若代理无效, 则将其优先级将一档, 当优先级分数小于0时, 将其删除
                    self.conn.decrease(proxy)
        except (ServerDisconnectedError, ClientResponseError,ClientConnectorError) as s:
            print(s)

    def test(self): # 异步测试proxies是否有效
        print('正在测试代理')
        try:
            loop = asyncio.get_event_loop()
            tasks =[self.test_single_proxy(proxy) for proxy in self.raw_proxies]
            loop.run_until_complete(asyncio.wait(tasks))
        except ValueError:
            print('异步检测失败')

class PoolAdder:
    '''
    向代理池队列中加入代理
    '''
    def __init__(self, proxies):
        self.proxies = proxies
        self.conn = RedisClient()
        self.tester = ValidityTester()
        self.crawler = FreeProxyGetter()

    def over_upper_proxies(self):
        '''
        判断队列是否溢出

        '''
        if self.conn.get_proxy_count() > self.proxies:
            return True
        else:
            return False

    def add_to_queue(self):
        print('正在加入代理至队列')
        proxy_count = 0
        # 若队列中的代理数量不超过最大设定数量
        while not self.over_upper_proxies():
            for callback_label in range(self.crawler.__CrawlFuncCount__):
                callback = self.crawler.__CrawlFunc__[callback_label]
                raw_proxies = self.crawler.get_raw_proxies(callback)
                # 测试已爬代理并加入代理队列
                self.tester.set_raw_proxies(raw_proxies)
                self.tester.test()
                proxy_count += len(raw_proxies)
                if self.over_upper_proxies():
                    print('代理池队列已满，请等待')
                    break
            if proxy_count == 0:
                raise ResourceDepletionError

class Schedule:
    @staticmethod
    def valid_proxy(cycle_time = Valid_Check_Cycle):
        conn = RedisClient()
        tester = ValidityTester()
        while True:
            print('Refreshing ip')
            # redis队列中代理数量的一半
            count = int(0.5 * conn.get_proxy_count())
            if count == 0:
                print('waiting for adding proxy')
                time.sleep(cycle_time)
                continue
            # 从redis队列中拿出优先级最高的代理
            raw_proxies = conn.get_proxy()
            tester.set_raw_proxies(raw_proxies)
            # 异步测试
            tester.test()
            time.sleep(cycle_time)

    @staticmethod
    def check_proxy(lower_proxies = POOL_LOWER_PROXIES,
                    upper_proxies = POOL_UPPER_PROXIES,
                    check_cycle = POOL_CHECK_TIME):
        '''
        检测代理池中的代理队列是否少于最小数，若小于，则间隔时间向里面添加代理
        '''
        conn = RedisClient()
        adder =PoolAdder(upper_proxies)
        while True:
            # 若队列中代理数量小于设定的最小代理数量
            if conn.get_proxy_count() < lower_proxies:
                # 向队列中加入代理
                adder.add_to_queue()
            time.sleep(check_cycle)

    def run(self):
        print('IP processes is running....')
        '''
        开启两个进程, pro1用于定时检测redis队列中的代理是否有效
        pro2用于定时检测redis队列中的代理是否过少, 若过少则向里添加
        若过多, 则停止添加
        '''
        pro1 = Process(target=Schedule.valid_proxy)
        pro2 = Process(target=Schedule.check_proxy)
        pro1.start()
        pro2.start()