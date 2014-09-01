# -*- coding: utf-8 -*-
"""
Thread-класс, выполняющий следующие функции:
1. Чтение исходного файла (построчное)
2. Присвоение меток линиям (порядковые намера)
3. Размещение задач на обработку в очередь.
"""

#TODO: Добавить возможность фильтрации строк перед тем как они попадут в систему

from __future__ import absolute_import

import threading
from obfuscation.log import log


class Reader(threading.Thread):
    name = 'Reader'

    def __init__(self, source_filename, target_queue):
        """
        :param source_filename: имя файла, который будет считан
        :type source_filename: str
        :param target_queue: очередь, в которую будут помещены задания
        :type target_queue: Queue.Queue
        """
        threading.Thread.__init__(self)
        self.filename = source_filename
        self.queue = target_queue

        log.debug('Reader parameters: filename = %s; queue = %s' % (self.filename,
                                                                    self.queue))

    # Метод run() будет вызван при запуске треды на выполнение
    def run(self):
        log.debug('Reader started.')

        with open(self.filename, 'r') as f:

            # index - это номер строки (начиная с 1)
            for index, line in enumerate(f):
                log.debug('Reading line %s: %s' % (index, line.rstrip()))

                # Параметры block=True и timeout=None нужны для обработки ситуации,
                # когда очередь достигла максимального размера.
                # В такое комбинации эта thread будет приостановлена до тех пор,
                # пока в очереди не появится место.
                self.queue.put((index, line.rstrip()), block=True, timeout=None)

        log.debug('Reader finished.')
