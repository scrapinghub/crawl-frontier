from crawlfrontier.tests import backends


class TestFIFO(backends.FIFOBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.FIFO'


class TestLIFO(backends.LIFOBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.LIFO'


class TestDFS(backends.DFSBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.DFS'


class TestDFSOverused(backends.DFSBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.MemoryDFSOverusedBackend'


class TestDFSOverusedSimulation(backends.DFSOverusedBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.MemoryDFSOverusedBackend'


class TestBFS(backends.BFSBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.BFS'


class TestRANDOM(backends.RANDOMBackendTest):
    backend_class = 'crawlfrontier.contrib.backends.memory.RANDOM'
