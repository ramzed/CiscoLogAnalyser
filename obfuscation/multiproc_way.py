#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Разнес все по отдельным файлам, стало веселее.
"""

import os
import sys
import time
import multiprocessing as mp
try:
    # python 2
    from Queue import Empty
except ImportError:
    # python 3
    from queue import Empty


from log import log
from thread_reader import Reader
from thread_writer import Writer
from thread_coordinator import Coordinator
from thread_manager import Manager

######################### Проверка окружения ###################################
# Данная версия скрипта взлетит только в Linux-системах.
# Потому что для кросплатформенности нужно кучу всего предусматривать, ну ее
# нафиг пока что.
log.debug('Platform: %s' % sys.platform)
if not sys.platform.startswith('linux'):
    raise RuntimeError('Sorry. This script works only on Linux.')

# Конфликты между вторым и третьим питоном тоже могут быть, нам следует быть
# более конкретными в нашем коде
log.debug('Python version: %s' % sys.version)
is_py3 = sys.version_info.major == 3
log.debug('Python 3 interpreter detected: %s' % is_py3)

################################ Константы #####################################
INPUT_FILE = 'dutylog'
OUTPUT_FILE = 'cleanlog'

# Для того, чтобы все дети делали замены согласованно, управление этим
# процессом должно быть централизовано в одном месте.
# Сделаем тут некоторый уровень абстракции в виде юникс-сокета. И ребенку должно
# быть совершенно все равно, что по ту сторону сокета.
SOCK_NAME = '/tmp/f.sock'
# Убедимся, что имя не занято:
try:
    os.unlink(SOCK_NAME)
except OSError:
    if os.path.exists(SOCK_NAME):
        raise RuntimeError('Could not start. File exists: %s' % SOCK_NAME)


########################### Служебные классы ###################################
class QueueIter:
    """
    Перебираем элементы из очереди с возможностью выйти по команде извне.
    """
    def __init__(self, queue):
        self.queue = queue
        self.stopped = False
        self.next = self.__next__

    def __iter__(self):
        return self

    def __next__(self):
        while not self.stopped:
            try:
                next_item = self.queue.get(True, 1)
            except Empty:
                pass
            else:
                log.debug('Next item in queue: %s ' % str(next_item))
                return next_item
        else:
            log.debug('Queue iteration stopped by external command')
            raise StopIteration

    def stop(self):
        self.stopped = True


################################################################################
########################### Основной класс #####################################
################################################################################
class MultiObfuscater:

    def __init__(self, input_file, output_file):
        # Очередь задач. Записывает - reader. Читает - manager.
        self.jobs_queue = mp.Queue(maxsize=1000)
        # Итератор по очереди задач. С возможностью остановки извне.
        self.jobs_iter = QueueIter(self.jobs_queue)
        # Очередь результатов. Записывает - manager. Читает - writer.
        results_queue = mp.Queue()

        # инициализируем компоненты:
        self.components = {
            'reader': Reader(input_file, self.jobs_queue),
            'writer': Writer(output_file, results_queue),
            'coordinator': Coordinator(SOCK_NAME),
            'manager': Manager(self.jobs_iter, results_queue, SOCK_NAME),
        }

        log.info('Components initialized.')

    def start(self):
        # запускаем их все и надеемся, что взлетим...
        for component_instance in self.components.values():
            component_instance.start()
        log.info('Components started.')

        # ждем пока дочитается файл
        self.components['reader'].join()
        log.info('Reached end of input file.')
        log.debug('Reader alive: %s' % self.components['reader'].is_alive())

        # ждем пока рабочие разберут все задачи из очереди
        while not self.jobs_queue.empty():
            time.sleep(1)
        log.debug('Jobs queue is empty.')

        # тормозим итератор задач
        self.jobs_iter.stop()
        log.debug('Stopping jobs iterator.')

        # ждем пока остановится менеджер
        self.components['manager'].join()
        log.info('Manager finished.')
        log.debug('Manager alive: %s' % self.components['manager'].is_alive())

        # останавливаем остальные компоненты
        log.debug('Trying to stop writer.')
        self.components['writer'].stop()
        log.debug('Trying to stop coordinator.')
        self.components['coordinator'].stop()
        time.sleep(2)
        log.debug('Writer alive: %s' % self.components['writer'].is_alive())
        log.debug('Coordinator alive: %s' % self.components['coordinator'].is_alive())

        log.info('All components stopped.')

        # если сюда добрались - значит все ОК и код возврата = 0
        return 0

if __name__ == '__main__':
    sys.exit(MultiObfuscater(INPUT_FILE, OUTPUT_FILE).start())

