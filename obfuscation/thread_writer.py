# -*- coding: utf-8 -*-
"""
Thread-класс, выполняющий следующие функции:
1. Чтение результатов работы из очереди
2. Восстановление правильного порядка на основании меток
3. Блочная запись результатов на диск
"""

#TODO: реализовать расположение строк в исходном порядке

#TODO: реализовать блочную запись на диск

from stoppable_loop import StoppableLoop
from Queue import Empty
from log import log


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
            print(line)