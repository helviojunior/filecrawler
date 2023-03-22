import time
from typing import Any
import queue
import threading


class Worker:
    __running = False
    q = None
    __total = 0
    __count = 0
    threads = 1
    callback = None
    per_thread_callback = None
    inserted = []
    threads_status = {}

    def __init__(self, callback: Any = None, per_thread_callback: Any = None, threads=2):
        if callback is None or not callable(callback):
            raise Exception('worker is not callable')

        if per_thread_callback is not None and not callable(per_thread_callback):
            raise Exception('per_thread_callback is not callable')

        self.callback = callback
        self.per_thread_callback = per_thread_callback
        self.q = queue.Queue()
        self.threads = threads
        self.total = 0
        if self.threads <= 1:
            self.threads = 1

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def add_item(self, item) -> bool:
        self.q.put(item)
        self.__total += 1
        return True

    def start(self, **kwargs):

        if self.callback is None or not callable(self.callback):
            raise Exception('The worker is not callable')

        self.__running = True
        self.__count = 0
        for i in range(self.threads):
            self.threads_status[i] = False
            t = threading.Thread(target=self.__worker, kwargs=dict(index=i, **kwargs))
            t.daemon = True
            t.start()

    def __worker(self, index, **kwargs):
        tcb = None
        if self.per_thread_callback is not None:
            tcb = self.per_thread_callback(index, **kwargs)

        thread_count = 0
        while self.__running:
            entry = self.q.get()

            if entry is None:
                self.q.task_done()
                continue

            try:
                self.threads_status[index] = True
                self.callback(worker=self, entry=entry, thread_callback_data=tcb, thread_count=thread_count, **kwargs)
                thread_count += 1
            finally:
                thread_count += 1
                self.__count += 1
                self.q.task_done()
                self.threads_status[index] = False

    @property
    def count(self):
        return len(self.q.queue)

    @property
    def executed(self):
        return self.__count

    @property
    def running(self):
        return self.__running

    @property
    def executing(self):
        return next((
            v for _, v in self.threads_status.items()
            if v
        ), False)

    def wait_finish(self):
        while self.running and self.executed < 1 and self.count > 0:
            time.sleep(0.3)

        while self.running and self.count > 0:
            time.sleep(0.300)

        while self.executing:
            time.sleep(0.300)

    def close(self):
        self.__running = False
        self.inserted = []
        with self.q.mutex:
            self.q.queue.clear()
