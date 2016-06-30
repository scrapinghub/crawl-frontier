# -*- coding: utf-8 -*-
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
import six


@six.add_metaclass(ABCMeta)
class BaseDecoder(object):

    @abstractmethod
    def decode(self, buffer):
        """
        Decodes the message.

        :param bytes buffer: encoded message
        :return: tuple of message type and related objects
        """
        pass

    @abstractmethod
    def decode_request(self, buffer):
        """
        Decodes Request objects.

        :param bytes buffer: serialized string
        :return: object Request
        """
        pass


@six.add_metaclass(ABCMeta)
class BaseEncoder(object):

    @abstractmethod
    def encode_add_seeds(self, seeds):
        """
        Encodes add_seeds message

        :param list seeds: A list of frontier Request objects
        :return: bytes encoded message
        """
        pass

    @abstractmethod
    def encode_page_crawled(self, response, links):
        """
        Encodes a page_crawled message

        :param object response: A frontier Response object
        :param list links: A list of Request objects

        :return: bytes encoded message
        """
        pass

    @abstractmethod
    def encode_request_error(self, request, error):
        """
        Encodes a request_error message

        :param object request: A frontier Request object
        :param string error: Error description

        :return: bytes encoded message
        """
        pass

    @abstractmethod
    def encode_request(self, request):
        """
        Encodes requests for spider feed stream.

        :param object request: Frontera Request object
        :return: bytes encoded message
        """
        pass

    @abstractmethod
    def encode_update_score(self, fingerprint, score, url, schedule):
        """
        Encodes update_score messages for scoring log stream.

        :param str fingerprint: fingerprint in hex form
        :param float score: score
        :param str url: A document url
        :param bool schedule: True if document needs to be scheduled for download
        :return: bytes encoded message
        """
        pass

    @abstractmethod
    def encode_new_job_id(self, job_id):
        """
        Encodes changing of job_id parameter.

        :param int job_id:
        :return: bytes encoded message
        """
        pass

    @abstractmethod
    def encode_offset(self, partition_id, offset):
        """
        Encodes current spider offset in spider feed.

        :param int partition_id:
        :param int offset:
        :return: bytes encoded message
        """
        pass
