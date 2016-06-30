from __future__ import absolute_import
from tests.test_overused_buffer import DFSOverusedBackendTest
from tests import backends


class TestFIFO(backends.FIFOBackendTest):
    backend_class = 'frontera.contrib.backends.memory.FIFO'


class TestLIFO(backends.LIFOBackendTest):
    backend_class = 'frontera.contrib.backends.memory.LIFO'


class TestDFS(backends.DFSBackendTest):
    backend_class = 'frontera.contrib.backends.memory.DFS'


class TestDFSOverused(backends.DFSBackendTest):
    backend_class = 'frontera.contrib.backends.memory.MemoryDFSOverusedBackend'


class TestDFSOverusedSimulation(DFSOverusedBackendTest):
    backend_class = 'frontera.contrib.backends.memory.MemoryDFSOverusedBackend'


class TestBFS(backends.BFSBackendTest):
    backend_class = 'frontera.contrib.backends.memory.BFS'


class TestRANDOM(backends.RANDOMBackendTest):
    backend_class = 'frontera.contrib.backends.memory.RANDOM'
