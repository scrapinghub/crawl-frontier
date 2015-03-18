from __future__ import absolute_import
import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy import UniqueConstraint

from crawlfrontier import Backend
from crawlfrontier.utils.misc import load_object

# Default settings
DEFAULT_ENGINE = 'sqlite:///:memory:'
DEFAULT_ENGINE_ECHO = False
DEFAULT_DROP_ALL_TABLES = True
DEFAULT_CLEAR_CONTENT = True
DEFAULT_MODELS = {
    'Page': 'crawlfrontier.contrib.backends.sqlalchemy.Page',
}

Base = declarative_base()


class Page(Base):
    __tablename__ = 'pages'
    __table_args__ = (
        UniqueConstraint('url'),
    )

    class State:
        NOT_CRAWLED = 'NOT CRAWLED'
        QUEUED = 'QUEUED'
        CRAWLED = 'CRAWLED'
        ERROR = 'ERROR'

    url = Column(String(1000), nullable=False)
    fingerprint = Column(String(40), primary_key=True, nullable=False, index=True, unique=True)
    depth = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    status_code = Column(String(20))
    state = Column(String(10))
    error = Column(String(20))

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
        pass

    def add_seeds(self, seeds):
        for seed in seeds:
            db_page, _ = self._get_or_create_db_page(url=seed.url, fingerprint=seed.meta['fingerprint'])
        self.session.commit()

    def get_next_requests(self, max_next_requests, info):
        query = self.page_model.query(self.session)
        query = query.filter(self.page_model.state == Page.State.NOT_CRAWLED)
        query = self._get_order_by(query)
        if max_next_requests:
            query = query.limit(max_next_requests)
        next_pages = []
        for db_page in query:
            db_page.state = Page.State.QUEUED
            request = self.manager.request_model(url=db_page.url)
            next_pages.append(request)
        self.session.commit()
        return next_pages

    def page_crawled(self, response, links):
        db_page, _ = self._get_or_create_db_page(url=response.url, fingerprint=response.meta['fingerprint'])
        db_page.state = Page.State.CRAWLED
        db_page.status_code = response.status_code
        for link in links:
            db_page_from_link, created = self._get_or_create_db_page(url=link.url, fingerprint=link.meta['fingerprint'])
            if created:
                db_page_from_link.depth = db_page.depth+1
        self.session.commit()

    def request_error(self, request, error):
        db_page, _ = self._get_or_create_db_page(url=request.url, fingerprint=request.meta['fingerprint'])
        db_page.state = Page.State.ERROR
        db_page.error = error
        self.session.commit()

    def _get_or_create_db_page(self, url, fingerprint):
        if not self._request_exists(fingerprint):
            db_request = self.page_model()
            db_request.fingerprint = fingerprint
            db_request.state = Page.State.NOT_CRAWLED
            db_request.url = url
            db_request.depth = 0
            db_request.created_at = datetime.datetime.utcnow()
            self.session.add(db_request)
            self.manager.logger.backend.debug('Creating request %s' % db_request)
            return db_request, True
        else:
            db_request = self.page_model.query(self.session).filter_by(fingerprint=fingerprint).first()
            self.manager.logger.backend.debug('Request exists %s' % db_request)
            return db_request, False

    def _request_exists(self, fingerprint):
        q = self.page_model.query(self.session).filter_by(fingerprint=fingerprint)
        return self.session.query(q.exists()).scalar()

    def _get_order_by(self, query):
        raise NotImplementedError


class FIFOBackend(SQLiteBackend):
    component_name = 'SQLite Backend FIFO'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.created_at)


class LIFOBackend(SQLiteBackend):
    component_name = 'SQLite Backend LIFO'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.created_at.desc())


class DFSBackend(SQLiteBackend):
    component_name = 'SQLite Backend DFS'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.depth.desc(), self.page_model.created_at)


class BFSBackend(SQLiteBackend):
    component_name = 'SQLite Backend BFS'

    def _get_order_by(self, query):
        return query.order_by(self.page_model.depth, self.page_model.created_at)


BASE = SQLiteBackend
LIFO = LIFOBackend
FIFO = FIFOBackend
DFS = DFSBackend
BFS = BFSBackend