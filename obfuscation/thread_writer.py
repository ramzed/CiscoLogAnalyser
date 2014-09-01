# -*- coding: utf-8 -*-
"""
Thread-класс, выполняющий следующие функции:
1. Чтение результатов работы из очереди
2. Восстановление правильного порядка на основании меток
3. Блочная запись результатов на диск
"""

#TODO: реализовать расположение строк в исходном порядке оптимальным методом

from __future__ import absolute_import

try:
    # python 2
    from Queue import Empty
except ImportError:
    # python 3
    from queue import Empty

from obfuscation.stoppable_loop import StoppableLoop
from obfuscation.log import log


class Writer(StoppableLoop):
    name = 'Writer'

    def __init__(self, target_filename, source_queue):
        """
        :param target_filename: имя файла, в который будут записаны результаты
        :type target_filename: str
        :param source_queue: очередь, из которой будут читаться результаты
        :type source_queue: Queue.Queue
        """
        StoppableLoop.__init__(self)
        self.filename = target_filename
        self.queue = source_queue
        self.fd = open(target_filename, 'w')

        # Предположительно данные в буфере будут достаточно близко к правильному
        # порядку. Следовательно и алгоритм сортировки мы будем выбирать
        # соответственный.
        self.buffer = []
        self.dump_threshold = 100000

    def logic(self):
        try:
            # запрос get() выполняется с параметрами blocking=True и timeout=1
            # это значит, что если очередь пуста, выполнение будет приостановлено
            # на время до 1 секунды, если за это время не появятся элементы в
            # очереди, будет сгенерировано исключение Empty()
            seq, line = self.queue.get(True, 1)
        except Empty:
            # Мы не собираемся ничего особого предпринимать, если очередь долго
            # пуста. Нам лишь нужно переодически выходить из ожидания, чтобы не
            # пропустить момент завершения программы
            pass
        else:
            log.debug('Position: %s Line: %s' % (seq, line))
            self.buffer.append((seq, line))

        if len(self.buffer) == self.dump_threshold:
            self.dump_to_disk()

    def dump_to_disk(self):
        self.fd.writelines([i[1] for i in sorted(self.buffer)])
        self.buffer = []

    def shut_down(self):
        if len(self.buffer) > 0:
            self.dump_to_disk()
        self.fd.close()