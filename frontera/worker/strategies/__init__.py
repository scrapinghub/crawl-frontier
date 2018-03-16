# -*- coding: utf-8 -*-
from __future__ import absolute_import
from frontera.core.models import Request
from frontera.contrib.middlewares.fingerprint import UrlFingerprintMiddleware

from abc import ABCMeta, abstractmethod
import six


@six.add_metaclass(ABCMeta)
class BaseCrawlingStrategy(object):
    """
    Interface definition for a crawling strategy.

    Before calling these methods strategy worker is adding 'state' key to meta field in every
    :class:`Request <frontera.core.models.Request>` with state of the URL. Pleases refer for the states to HBaseBackend
    implementation.

    After exiting from all of these methods states from meta field are passed back and stored in the backend.
    """

    def __init__(self, manager, args, mb_stream, states_context):
        self._mb_stream = mb_stream
        self._states_context = states_context
        self._manager = manager

    @classmethod
    def from_worker(cls, manager, args, mb_stream, states_context):
        """
        Called on instantiation in strategy worker.

        :param manager: :class: `Backend <frontera.core.manager.FrontierManager>` instance
        :param args: dict with command line arguments from :term:`strategy worker`
        :param mb_stream: :class: `UpdateScoreStream <frontera.worker.strategy.UpdateScoreStream>` instance
        :return: new instance
        """
        return cls(manager, args, mb_stream, states_context)

    @abstractmethod
    def add_seeds(self, seeds):
        """
        Called when add_seeds event is received from spider log.

        :param list seeds: A list of :class:`Request <frontera.core.models.Request>` objects.
        """

    @abstractmethod
    def page_crawled(self, response):
        """
        Called every time document was successfully crawled, and receiving page_crawled event from spider log.

        :param object response: The :class:`Response <frontera.core.models.Response>` object for the crawled page.
        """

    @abstractmethod
    def filter_extracted_links(self, request, links):
        """
        Called every time on receiving links_extracted event by strategy worker. This call is preceding the call
        to links_extracted handler and is aiming to filter unused links and return only those where states
        information is needed.

        :param object request: The :class:`Request <frontera.core.models.Request>` object for the crawled page.
        :param list links: A list of :class:`Request <frontera.core.models.Request>` objects generated from \
        the links extracted for the crawled page.

        :return: A subset of :class:`Request <frontera.core.models.Request>` input objects.
        """

    @abstractmethod
    def links_extracted(self, request, links):
        """
        Called every time document was successfully crawled, and receiving links_extracted event from spider log,
        after the links states are fetched from backend. Should be used to schedule links according to some rules.

        :param object request: The :class:`Request <frontera.core.models.Request>` object for the crawled page.
        :param list links: A list of :class:`Request <frontera.core.models.Request>` objects generated from \
        the links extracted for the crawled page.
        """

    @abstractmethod
    def page_error(self, request, error):
        """
        Called every time there was error during page downloading.

        :param object request: The fetched with error :class:`Request <frontera.core.models.Request>` object.
        :param str error: A string identifier for the error.
        """

    def finished(self):
        """
        Called by Strategy worker, after finishing processing each cycle of spider log. If this method returns true,
        then Strategy worker reports that crawling goal is achieved, stops and exits.

        :return: bool
        """
        return False

    def close(self):
        """
        Called when strategy worker is about to close crawling strategy.
        """
        self._mb_stream.flush()
        self._states_context.release()

    def schedule(self, request, score=1.0, dont_queue=False):
        """
        Schedule document for crawling with specified score.

        :param request: A :class:`Request <frontera.core.models.Request>` object.
        :param score: float from 0.0 to 1.0
        :param dont_queue: bool, True - if no need to schedule, only update the score
        """
        self._mb_stream.send(request, score, dont_queue)

    def create_request(self, url, method=b'GET', headers=None, cookies=None, meta=None, body=b''):
        """
        Creates request with specified fields, with state fetched from backend. This method only creates request, but
        isn't getting it's state from storage. Use self.refresh_states on a batch of requests to get their states
        from storage.

        :param url: str
        :param method: str
        :param headers: dict
        :param cookies: dict
        :param meta: dict
        :param body: str
        :return: :class:`Request <frontera.core.models.Request>`
        """
        return self._manager.create_request(url, method=method, headers=headers, cookies=cookies, meta=meta, body=body)

    def refresh_states(self, requests):
        """
        Retrieves states for all requests from storage.

        :param requests: list(:class:`Request <frontera.core.models.Request>`)
        """
        self._states_context.refresh_and_keep(requests)
