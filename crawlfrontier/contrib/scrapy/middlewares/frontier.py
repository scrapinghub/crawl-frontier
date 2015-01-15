from twisted.internet.error import DNSLookupError, TimeoutError
from twisted.internet.task import LoopingCall
from scrapy.exceptions import NotConfigured, DontCloseSpider
from scrapy.http import Request
from scrapy import signals

from crawlfrontier.contrib.scrapy.manager import ScrapyFrontierManager

# Signals
frontier_download_error = object()

# Defaul values
DEFAULT_FRONTIER_ENABLED = True
DEFAULT_FRONTIER_SCHEDULER_INTERVAL = 0.5
DEFAULT_FRONTIER_SCHEDULER_CONCURRENT_REQUESTS = 256


class CrawlFrontierSpiderMiddleware(object):

    def __init__(self, crawler, stats):
        self.crawler = crawler
        self.stats = stats

        # Enable check
        if not crawler.settings.get('FRONTIER_ENABLED', DEFAULT_FRONTIER_ENABLED):
            raise NotConfigured

        # Frontier
        frontier_settings = crawler.settings.get('FRONTIER_SETTINGS', None)
        if not frontier_settings:
            raise NotConfigured
        self.frontier = ScrapyFrontierManager(frontier_settings)

        # Scheduler settings
        self.scheduler_interval = crawler.settings.get('FRONTIER_SCHEDULER_INTERVAL',
                                                       DEFAULT_FRONTIER_SCHEDULER_INTERVAL)
        self.scheduler_concurrent_requests = crawler.settings.get('FRONTIER_SCHEDULER_CONCURRENT_REQUESTS',
                                                                  DEFAULT_FRONTIER_SCHEDULER_CONCURRENT_REQUESTS)
        # Queued requests set
        self.queued_requests = set()

        # Signals
        self.crawler.signals.connect(self.spider_opened, signals.spider_opened)
        self.crawler.signals.connect(self.spider_closed, signals.spider_closed)
        #self.crawler.signals.connect(self.response_received, signals.response_received)
        # self.crawler.signals.connect(self.spider_idle, signals.spider_idle)
        self.crawler.signals.connect(self.download_error, frontier_download_error)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler, crawler.stats)

    def spider_opened(self, spider):
        if not self.frontier.manager.auto_start:
            self.frontier.start()
        self.next_requests_task = LoopingCall(self._schedule_next_requests, spider)
        self.next_requests_task.start(self.scheduler_interval)

    def spider_closed(self, spider, reason):
        self.next_requests_task.stop()
        self.frontier.stop()

    def process_start_requests(self, start_requests, spider):
        if start_requests:
            self.frontier.add_seeds(list(start_requests))
        return self._get_next_requests()

    def process_spider_output(self, response, result, spider):
        links = []
        for element in result:
            if isinstance(element, Request):
                links.append(element)
            else:
                yield element
        self.frontier.page_crawled(scrapy_response=response,
                                   scrapy_links=links)
        self._remove_queued_request(response.request)

    def download_error(self, request, exception, spider):
        # TODO: Add more errors...
        error = '?'
        if isinstance(exception, DNSLookupError):
            error = 'DNS_ERROR'
        elif isinstance(exception, TimeoutError):
            error = 'TIMEOUT_ERROR'
        self.frontier.request_error(scrapy_request=request, error=error)
        self._remove_queued_request(request)

    def spider_idle(self, spider):
        if not self.frontier.manager.finished:
            raise DontCloseSpider()

    def _schedule_next_requests(self, spider):
        n_scheduled = len(self.queued_requests)
        if not self.frontier.manager.finished and n_scheduled < self.scheduler_concurrent_requests:
            n_requests_gap = self.scheduler_concurrent_requests - n_scheduled
            next_pages = self._get_next_requests(n_requests_gap)
            for request in next_pages:
                self.crawler.engine.crawl(request, spider)

    def _get_next_requests(self, max_next_requests=0):
        requests = self.frontier.get_next_requests(max_next_requests)
        for request in requests:
            self._add_queued_request(request)
        return requests

    def _add_queued_request(self, request):
        self.queued_requests.add(request.url)

    def _remove_queued_request(self, request):
        if 'redirect_urls' in request.meta:
            url = request.meta['redirect_urls'][0]
        else:
            url = request.url
        try:
            self.queued_requests.remove(url)
        except KeyError:
            pass


class CrawlFrontierDownloaderMiddleware(object):
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_exception(self, request, exception, spider):
        self.crawler.signals.send_catch_log(signal=frontier_download_error,
                                            request=request,
                                            exception=exception,
                                            spider=spider)

