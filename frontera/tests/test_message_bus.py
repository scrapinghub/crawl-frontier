# -*- coding: utf-8 -*-
from frontera.settings import Settings
from frontera.contrib.messagebus.zeromq import MessageBus as ZeroMQMessageBus
from frontera.contrib.messagebus.kafkabus import MessageBus as KafkaMessageBus
from frontera.utils.fingerprint import sha1
from random import randint
from time import sleep
import os
from kafka_utils.case import KafkaIntegrationTestCase, random_string
from kafka_utils.fixtures import ZookeeperFixture, KafkaFixture
import logging


class MessageBusTester(object):
    def __init__(self, cls, settings=Settings()):
        settings.set('SPIDER_FEED_PARTITIONS', 1)
        settings.set('QUEUE_HOSTNAME_PARTITIONING', True)
        self.messagebus = cls(settings)
        spiderlog = self.messagebus.spider_log()

        # sw
        self.sw_sl_c = spiderlog.consumer(partition_id=0, type='sw')
        scoring_log = self.messagebus.scoring_log()
        self.sw_us_p = scoring_log.producer()

        sleep(0.1)

        # db
        self.db_sl_c = spiderlog.consumer(partition_id=None, type='db')
        self.db_us_c = scoring_log.consumer()

        spider_feed = self.messagebus.spider_feed()
        self.db_sf_p = spider_feed.producer()

        sleep(0.1)

        # spider
        self.sp_sl_p = spiderlog.producer()
        self.sp_sf_c = spider_feed.consumer(0)

        sleep(0.1)

    def spider_log_activity(self, messages):
        for i in range(0, messages):
            if i % 2 == 0:
                self.sp_sl_p.send(sha1(str(randint(1, 1000))), 'http://helloworld.com/way/to/the/sun/' + str(0))
            else:
                self.sp_sl_p.send(sha1(str(randint(1, 1000))), 'http://way.to.the.sun' + str(0))
        self.sp_sl_p.flush()

    def spider_feed_activity(self):
        sf_c = 0
        for m in self.sp_sf_c.get_messages(timeout=1.0, count=512):
            sf_c += 1
        return sf_c

    def sw_activity(self):
        c = 0
        p = 0
        for m in self.sw_sl_c.get_messages(timeout=1.0, count=512):
            if m.startswith('http://helloworld.com/'):
                p += 1
                self.sw_us_p.send(None, 'message' + str(0) + "," + str(c))
            c += 1
        assert p > 0
        return c

    def db_activity(self, messages):

        sl_c = 0
        us_c = 0

        for m in self.db_sl_c.get_messages(timeout=1.0, count=512):
            sl_c += 1
        for m in self.db_us_c.get_messages(timeout=1.0, count=512):
            us_c += 1
        for i in range(0, messages):
            if i % 2 == 0:
                self.db_sf_p.send("newhost", "http://newhost/new/url/to/crawl")
            else:
                self.db_sf_p.send("someotherhost", "http://newhost223/new/url/to/crawl")
        self.db_sf_p.flush()
        return (sl_c, us_c)


class IPv6MessageBusTester(MessageBusTester):
    """
    Same as MessageBusTester but with ipv6-localhost
    """
    # TODO This class should be used for IPv6 testing. Use the broker on port
    # 5570 for this test.
    def __init__(self):
        settings = Settings()
        settings.set('ZMQ_ADDRESS', '::1')
        super(IPv6MessageBusTester, self).__init__(settings)


def test_zmq_message_bus():
    """
    Test MessageBus with default settings, IPv6 and Star as ZMQ_ADDRESS
    """
    tester = MessageBusTester(ZeroMQMessageBus)
    tester.spider_log_activity(64)
    assert tester.sw_activity() == 64
    assert tester.db_activity(128) == (64, 32)
    assert tester.spider_feed_activity() == 128


class KafkaMessageBusTestCase(KafkaIntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        #logging.basicConfig(level=logging.DEBUG)
        #logger = logging.getLogger("frontera.tests.kafka_utils.service")
        #logger.addHandler(logging.StreamHandler())
        if not os.environ.get('KAFKA_VERSION'):
            return

        cls.zk = ZookeeperFixture.instance()
        chroot = random_string(10)
        cls.server = KafkaFixture.instance(0, cls.zk.host, cls.zk.port,
                                           zk_chroot=chroot, partitions=1)

    @classmethod
    def tearDownClass(cls):
        if not os.environ.get('KAFKA_VERSION'):
            return

        cls.server.close()
        cls.zk.close()

    def test_kafka_message_bus_integration(self):
        """
        Test MessageBus with default settings, IPv6 and Star as ZMQ_ADDRESS
        """
        self.client.ensure_topic_exists("frontier-todo")
        self.client.ensure_topic_exists("frontier-done")
        self.client.ensure_topic_exists("frontier-score")

        #logging.basicConfig(level=logging.INFO)
        #kafkabus = logging.getLogger("kafkabus")
        #kafkabus.addHandler(logging.StreamHandler())
        settings = Settings()
        settings.set('KAFKA_LOCATION', '%s:%s' % (self.server.host, self.server.port))
        settings.set('FRONTIER_GROUP', 'frontier2')
        tester = MessageBusTester(KafkaMessageBus, settings)
        tester.spider_log_activity(64)
        assert tester.sw_activity() == 64
        assert tester.db_activity(128) == (64, 32)
        assert tester.spider_feed_activity() == 128
