# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from collections import defaultdict

import six

from frontera import Backend
from frontera.core import OverusedBuffer
from frontera.utils.misc import load_object


class MessageBusBackend(Backend):
    def __init__(self, manager):
        settings = manager.settings
        messagebus = load_object(settings.get('MESSAGE_BUS'))
        self.mb = messagebus(settings)
        codec_path = settings.get('MESSAGE_BUS_CODEC')
        encoder_cls = load_object(codec_path+".Encoder")
        decoder_cls = load_object(codec_path+".Decoder")
        store_content = settings.get('STORE_CONTENT')
        self._aggregate = load_object(settings.get('MESSAGE_BUS_REQUEST_AGGREGATION_FUNCTION'))
        self._encoder = encoder_cls(manager.request_model, send_body=store_content)
        self._decoder = decoder_cls(manager.request_model, manager.response_model)
        self.spider_log_producer = self.mb.spider_log().producer()
        spider_feed = self.mb.spider_feed()
        self.partition_id = int(settings.get('SPIDER_PARTITION_ID'))

        if self.partition_id < 0 or self.partition_id >= settings.get('SPIDER_FEED_PARTITIONS'):
            raise ValueError("Spider partition id cannot be less than 0 or more than SPIDER_FEED_PARTITIONS.")

        self.consumer = spider_feed.consumer(partition_id=self.partition_id)
        self._get_timeout = float(settings.get('KAFKA_GET_TIMEOUT'))
        self._logger = logging.getLogger("messagebus-backend")
        self._logger.info("Consuming from partition id %d", self.partition_id)

        if settings.get('MESSAGE_BUS_USE_OVERUSED_BUFFER'):
            self._buffer = OverusedBuffer(
                self._get_next_requests_unbuffered,
                self._logger.debug,
            )
            self.get_next_requests = self._get_next_requests_buffered

    @classmethod
    def from_manager(cls, manager):
        return cls(manager)

    def frontier_start(self):
        pass

    def frontier_stop(self):
        self.spider_log_producer.flush()

    def add_seeds(self, seeds):
        for key, host_links in six.iteritems(self._aggregate(seeds)):
            message = self._encoder.encode_add_seeds(host_links)

            self.spider_log_producer.send(key, message)

    def page_crawled(self, response):
        key = get_host_fprint(response)
        message = self._encoder.encode_page_crawled(response)

        self.spider_log_producer.send(key, message)

    def links_extracted(self, request, links):
        for key, host_links in six.iteritems(self._aggregate(links)):
            message = self._encoder.encode_links_extracted(request, host_links)

            self.spider_log_producer.send(key, message)

    def request_error(self, page, error):
        key = get_host_fprint(page)
        message = self._encoder.encode_request_error(page, error)

        self.spider_log_producer.send(key, message)

    def _get_next_requests_unbuffered(self, max_n_requests, **kwargs):
        requests = []

        for encoded in self.consumer.get_messages(count=max_n_requests, timeout=self._get_timeout):
            try:
                request = self._decoder.decode_request(encoded)
            except:
                self._logger.exception("Could not decode message: %s", encoded)
            else:
                requests.append(request)

        key = b'0123456789abcdef0123456789abcdef012345678'
        offset = self.consumer.get_offset(self.partition_id)
        message = self._encoder.encode_offset(self.partition_id, offset)

        self.spider_log_producer.send(key, message)

        return requests

    def _get_next_requests_buffered(self, max_n_requests, **kwargs):
        return self._buffer.get_next_requests(max_n_requests, **kwargs)

    get_next_requests = _get_next_requests_unbuffered

    def finished(self):
        return False

    @property
    def metadata(self):
        return None

    @property
    def queue(self):
        return None

    @property
    def states(self):
        return None


def aggregate_per_host(requests):
    per_host = defaultdict(list)

    for request in requests:
        try:
            key = request.meta[b'domain'][b'fingerprint']
            per_host[key].append(request)
        except KeyError:
            continue

    return per_host


def get_host_fprint(request):
    try:
        return request.meta[b'domain'][b'fingerprint']
    except KeyError:
        return None
