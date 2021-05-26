from multiprocessing.pool import ThreadPool
from threading import Thread

class TaskLatencyTest(Thread):
    objs:list
    def __init__(self, objs:list):
        Thread.__init__(self)
        self.objs=objs
    def run(self):
        pool = ThreadPool(len(self.objs))
        pool.map(lambda x: x.check_connection(), self.objs)