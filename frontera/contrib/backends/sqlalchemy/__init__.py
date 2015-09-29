from __future__ import absolute_import
import datetime
from sqlalchemy import exc

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator
from sqlalchemy import Column, String, Integer, PickleType
from sqlalchemy import UniqueConstraint

from frontera import Backend
from frontera.utils.misc import load_object

# Default settings
DEFAULT_ENGINE = 'sqlite:///:memory:'
DEFAULT_ENGINE_ECHO = False
DEFAULT_DROP_ALL_TABLES = True
DEFAULT_CLEAR_CONTENT = True
DEFAULT_MODELS = {
    'Page': 'frontera.contrib.backends.sqlalchemy.Page',
}

Base = declarative_base()


class DatetimeTimestamp(TypeDecorator):

    impl = String  # To use milliseconds in mysql
    timestamp_format = '%Y%m%d%H%M%S%f'

    def process_bind_param(self, value, _):
        if isinstance(value, datetime.datetime):
            return value.strftime(self.timestamp_format)
        raise ValueError('Not valid datetime')

    def process_result_value(self, value, _):
        return datetime.datetime.strptime(value, self.timestamp_format)


class Page(Base):
    __tablename__ = 'pages'
    __table_args__ = (
        UniqueConstraint('url'),
        {
            'mysql_charset': 'utf8',
            'mysql_engine': 'InnoDB',
            'mysql_row_format': 'DYNAMIC',
        },
    )

    class State:
        NOT_CRAWLED = 'NOT CRAWLED'
        QUEUED = 'QUEUED'
        CRAWLED = 'CRAWLED'
        ERROR = 'ERROR'

    url = Column(String(1024), nullable=False)
    fingerprint = Column(String(40), primary_key=True, nullable=False, index=True, unique=True)
    depth = Column(Integer, nullable=False)
    created_at = Column(DatetimeTimestamp(20), nullable=False)
    status_code = Column(String(20))
    state = Column(String(12))
    error = Column(String(20))
    meta = Column(PickleType())

    @classmethod
    def query(cls, session):
        return session.query(cls)

    def __repr__(self):
        return '<Page:%s>' % self.url


class SQLiteBackend(Backend):
    component_name = 'SQLite Backend'

    def __init__(self, manager):
        self.manager = manager

        # Get settings
        settings = manager.settings
        engine = settings.get('SQLALCHEMYBACKEND_ENGINE', DEFAULT_ENGINE)
        engine_echo = settings.get('SQLALCHEMYBACKEND_ENGINE_ECHO', DEFAULT_ENGINE_ECHO)
        drop_all_tables = settings.get('SQLALCHEMYBACKEND_DROP_ALL_TABLES', DEFAULT_DROP_ALL_TABLES)
        clear_content = settings.get('SQLALCHEMYBACKEND_CLEAR_CONTENT', DEFAULT_CLEAR_CONTENT)
        models = settings.get('SQLALCHEMYBACKEND_MODELS', DEFAULT_MODELS)

        # Create engine
        self.engine = create_engine(engine, echo=engine_echo)

        # Load models
        self.models = dict([(name, load_object(klass)) for name, klass in models.items()])

        # Drop tables if we have to
        if drop_all_tables:
            Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        # Create session
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)
        self.session = self.Session()

        # Clear content if we have to
        if clear_content:
            for name, table in Base.metadata.tables.items():
                self.session.execute(table.delete())

    @classmethod
    def from_manager(cls, manager):
        return cls(manager)

    @property
    def page_model(self):
        return self.models['Page']

    def frontier_start(self):
        pass

    def frontier_stop(self):
        self.session.close()
        self.engine.dispose()

    def add_seeds(self, seeds):
        for seed in seeds:
            self._create_db_page(seed, 0)
        self.session.commit()

    def get_next_requests(self, max_next_requests, **kwargs):
        query = self.page_model.query(self.session).with_lockmode('update')
        query = query.filter(self.page_model.state == Page.State.NOT_CRAWLED)
        query = self._get_order_by(query)
        if max_next_requests:
            query = query.limit(max_next_requests)
        next_pages = []
        for db_page in query:
            db_page.state = Page.State.QUEUED
            request = self.manager.request_model(url=db_page.url, meta=db_page.meta)
            next_pages.append(request)
        self.session.commit()
        return next_pages

    def page_crawled(self, response, links):
        db_page = self._get_db_page(response)
        db_page.state = Page.State.CRAWLED
        db_page.status_code = response.status_code
        for link in links:
            self._create_db_page(link, db_page.depth+1)
        self.session.commit()

    def request_error(self, request, error):
        db_page = self._get_db_page(request)
        db_page.state = Page.State.ERROR
        db_page.error = error
        self.session.commit()

    def _create_db_page(self, obj, depth):
        db_page = self.page_model()
        db_page.meta = obj.meta
        db_page.fingerprint = obj.meta['fingerprint']
        db_page.state = Page.State.NOT_CRAWLED
        db_page.url = obj.url
        db_page.depth = depth
        db_page.created_at = datetime.datetime.utcnow()
        try:
            self.session.add(db_page)
            self.session.commit()
        except exc.IntegrityError as e:
            self.session.rollback()
            self.manager.logger.backend.debug('Request exists %s' % db_page)

    def _get_db_page(self, obj):
        db_page = self.page_model.query(self.session).filter_by(fingerprint=obj.meta['fingerprint']).first()
        self.manager.logger.backend.debug('Request exists %s' % db_page)
        return db_page

    def _request_exists(self, fingerprint):
        q = self.page_model.query(self.session).filter_by(fingerprint=fingerprint)
        return self.session.query(q.exists()).scalar()

    def _get_order_by(self, query):
        raise NotImplementedError


class FIFOBackend(SQLiteBackend):
    component_name = 'SQLite FIFO Backend'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.created_at)


class LIFOBackend(SQLiteBackend):
    component_name = 'SQLite LIFO Backend'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.created_at.desc())


class DFSBackend(SQLiteBackend):
    component_name = 'SQLite DFS Backend'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.depth.desc(), self.page_model.created_at)


class BFSBackend(SQLiteBackend):
    component_name = 'SQLite BFS Backend'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.depth, self.page_model.created_at)


BASE = SQLiteBackend
LIFO = LIFOBackend
FIFO = FIFOBackend
DFS = DFSBackend
BFS = BFSBackend