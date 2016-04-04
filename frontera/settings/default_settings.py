from datetime import timedelta
import logging

AUTO_START = True
BACKEND = 'frontera.contrib.backends.memory.FIFO'
CANONICAL_SOLVER = 'frontera.contrib.canonicalsolvers.Basic'
CONSUMER_BATCH_SIZE = 512
DELAY_ON_EMPTY = 5.0
DOMAIN_FINGERPRINT_FUNCTION = 'frontera.utils.fingerprint.sha1'
EVENT_LOG_MANAGER = 'frontera.logger.events.EventLogManager'

HBASE_THRIFT_HOST = 'localhost'
HBASE_THRIFT_PORT = 9090
HBASE_NAMESPACE = 'crawler'
HBASE_DROP_ALL_TABLES = False
HBASE_METADATA_TABLE = 'metadata'
HBASE_USE_SNAPPY = False
HBASE_USE_FRAMED_COMPACT = False
HBASE_BATCH_SIZE = 9216
HBASE_STATE_CACHE_SIZE_LIMIT = 3000000
HBASE_QUEUE_TABLE = 'queue'
KAFKA_GET_TIMEOUT = 5.0
MAX_NEXT_REQUESTS = 64
MAX_REQUESTS = 0
MESSAGE_BUS = 'frontera.contrib.messagebus.zeromq.MessageBus'
MIDDLEWARES = [
    'frontera.contrib.middlewares.fingerprint.UrlFingerprintMiddleware',
]
NEW_BATCH_DELAY = 30.0
OVERUSED_SLOT_FACTOR = 5.0
QUEUE_HOSTNAME_PARTITIONING = False
REQUEST_MODEL = 'frontera.core.models.Request'
RESPONSE_MODEL = 'frontera.core.models.Response'

SPIDER_LOG_PARTITIONS = 1
SPIDER_FEED_PARTITIONS = 1
SQLALCHEMYBACKEND_CACHE_SIZE = 10000
SQLALCHEMYBACKEND_CLEAR_CONTENT = True
SQLALCHEMYBACKEND_DROP_ALL_TABLES = True
SQLALCHEMYBACKEND_ENGINE = 'sqlite:///:memory:'
SQLALCHEMYBACKEND_ENGINE_ECHO = False
SQLALCHEMYBACKEND_MODELS = {
    'MetadataModel': 'frontera.contrib.backends.sqlalchemy.models.MetadataModel',
    'StateModel': 'frontera.contrib.backends.sqlalchemy.models.StateModel',
    'QueueModel': 'frontera.contrib.backends.sqlalchemy.models.QueueModel'
}
SQLALCHEMYBACKEND_REVISIT_INTERVAL = timedelta(days=1)

CASSANDRABACKEND_CACHE_SIZE = 10000
CASSANDRABACKEND_DROP_ALL_TABLES = False
CASSANDRABACKEND_MODELS = {
    'MetadataModel': 'frontera.contrib.backends.cassandra.models.MetadataModel',
    'StateModel': 'frontera.contrib.backends.cassandra.models.StateModel',
    'QueueModel': 'frontera.contrib.backends.cassandra.models.QueueModel',
    'CrawlStatsModel': 'frontera.contrib.backends.cassandra.models.CrawlStatsModel'
}
CASSANDRABACKEND_REVISIT_INTERVAL = timedelta(days=1)
CASSANDRABACKEND_CLUSTER_IPS = ['127.0.0.1']
CASSANDRABACKEND_CLUSTER_PORT = 9042
CASSANDRABACKEND_KEYSPACE = 'frontera'
CASSANDRABACKEND_CREATE_KEYSPACE_IF_NOT_EXISTS = True
CASSANDRABACKEND_CRAWL_ID = "default"
CASSANDRABACKEND_GENERATE_STATS = False

STATE_CACHE_SIZE = 1000000
STORE_CONTENT = False
TEST_MODE = False
TLDEXTRACT_DOMAIN_INFO = False
URL_FINGERPRINT_FUNCTION = 'frontera.utils.fingerprint.sha1'

ZMQ_ADDRESS = '127.0.0.1'
ZMQ_BASE_PORT = 5550

#--------------------------------------------------------
# Logging
#--------------------------------------------------------
LOGGER = 'frontera.logger.FrontierLogger'
LOGGING_ENABLED = True

LOGGING_EVENTS_ENABLED = False
LOGGING_EVENTS_INCLUDE_METADATA = True
LOGGING_EVENTS_INCLUDE_DOMAIN = True
LOGGING_EVENTS_INCLUDE_DOMAIN_FIELDS = ['name', 'netloc', 'scheme', 'sld', 'tld', 'subdomain']
LOGGING_EVENTS_HANDLERS = [
    "frontera.logger.handlers.EVENTS",
]

LOGGING_MANAGER_ENABLED = False
LOGGING_MANAGER_LOGLEVEL = logging.DEBUG
LOGGING_MANAGER_HANDLERS = [
    "frontera.logger.handlers.CONSOLE_MANAGER",
]

LOGGING_BACKEND_ENABLED = False
LOGGING_BACKEND_LOGLEVEL = logging.DEBUG
LOGGING_BACKEND_HANDLERS = [
    "frontera.logger.handlers.CONSOLE_BACKEND",
]

LOGGING_DEBUGGING_ENABLED = False
LOGGING_DEBUGGING_LOGLEVEL = logging.DEBUG
LOGGING_DEBUGGING_HANDLERS = [
    "frontera.logger.handlers.CONSOLE_DEBUGGING",
]


