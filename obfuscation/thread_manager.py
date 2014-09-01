# -*- coding: utf-8 -*-
"""
Thread-класс, выполняющий следующие функции:
1. Определение количества процессов для запуска
2. Получение заданий из источника (iterable)
3. Запуска рабочих
4. Получение результатов и размещение их в очередь результатов
"""
from __future__ import absolute_import

import threading
import multiprocessing as mp

from obfuscation.log import log
from obfuscation.process_worker import Worker


class Manager(threading.Thread):
    name = 'Manager'

    def __init__(self, source, target, sock_address):
        """
        :param source: Iterable по входным параметрам
        :param target: очередь, в которую будут размещаться результаты
        :type target: Queue.Queue
        :param sock_address: адрес сокета, на котором расположен координатор
        :type sock_address: str
        """
        threading.Thread.__init__(self)
        self.input = source
        self.output = target
        self.worker = Worker(sock_address)
        self.pool = mp.Pool(get_core_num())
        log.debug('Manager initialized.')

    def run(self):
        log.debug('Manager started.')
        # получаем асинхронный итератор по результатам
        results = self.pool.imap_unordered(self.worker,
                                           self.input)
        # и возвращаем их
        for item in results:
            self.output.put(item)

        log.debug('Manager finished.')


# Нам нужно знать, сколько вычислительных ядер имеется на нашей машине, чтобы
# максимально эффективно использовать имеющиеся мощности.
def get_core_num():
    """
    Интеловские процессоры реализуют чудесную технологию HyperThreading,
    которая не даст нам ожидаемого выигрыша от распараллеливания на все
    "виртуальные ядра". Поэтому если скрипт запущен на железе Intel - количество
    процессов должно быть в два раза меньше, чем видимое число ядер.
    """
    if is_intel():
        return mp.cpu_count() // 2
    else:
        return mp.cpu_count()


def is_intel():
    """
    Вот по-этому я и говорю, что скрипт пока что работает только на линуксе.
    """
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line.startswith('vendor_id') and \
                    line.split(':')[1].strip() == 'GenuineIntel':
                return True
    return False