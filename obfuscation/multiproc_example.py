#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Я тут наколбасил жути какой-то. Оно работает, но как в этом разбираться...
"""

import os
import sys
import logging
import socket
import multiprocessing as mp
import threading
import random
import re
import time
try:
    # python 2
    from Queue import Empty
except ImportError:
    # python 3
    from queue import Empty

LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO

################################ Логирование ###################################
# Программа стала жирной и сложной, дебаг-лог нужен
log = logging.Logger('obfuscator')
log_format = logging.Formatter(
    fmt='%(levelname)-10s %(asctime)s: %(message)s',
    datefmt='%H:%M:%S',
    style='%')
file_handler = logging.StreamHandler(open('/tmp/obfuscator-debug.log', 'w'))
file_handler.setFormatter(log_format)
file_handler.setLevel(LOG_LEVEL)
log.addHandler(file_handler)

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


########################### Служебные функции ##################################
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
########################### Основные классы ####################################
################################################################################

################################################################################
class Reader(threading.Thread):
################################################################################
    """
    Чтение исходного файла, присвоение меток и размещение задач в очередь.
    """
    def __init__(self, source_filename, target_queue):
        threading.Thread.__init__(self)
        self.filename = source_filename
        self.queue = target_queue
        log.debug('Reader initialized.')

    def run(self):
        log.debug('Reader started.')
        with open(self.filename, 'r') as f:
            for index, line in enumerate(f):
                log.debug('Reading line %s: %s' % (index, line.rstrip()))
                self.queue.put((index, line.rstrip()), block=True, timeout=None)
        log.debug('Reader finished.')


################################################################################
class Writer(threading.Thread):
################################################################################
    """
    Приемка результатов, сортировка и запись в конечный файл.

    TODO: придумать алгоритм сортировки
    """
    def __init__(self, target_filename, source_queue):
        threading.Thread.__init__(self)
        self.filename = target_filename
        self.queue = source_queue
        self.stopped = False
        log.debug('Writer initialized.')

    def run(self):
        log.debug('Writer started.')
        while not self.stopped:
            try:
                seq, line = self.queue.get(True, 1)
            except Empty:
                pass
            else:
                log.debug('Position: %s Line: %s' % (seq, line))
                print(line)
        log.debug('Writer finished.')

    def stop(self):
        log.debug('Writer will now stop.')
        self.stopped = True


class Manager(threading.Thread):
    """
    Запускает рабочих в количестве.
    """
    def __init__(self, source, target, sock_address):
        threading.Thread.__init__(self)
        self.input = source
        self.output = target
        self.worker = Worker(sock_address)
        self.pool = mp.Pool(get_core_num())
        log.debug('Manager initialized.')

    def run(self):
        log.debug('Manager started.')
        # колдунство
        results = self.pool.imap_unordered(self.worker,
                                           self.input)
        for item in results:
            self.output.put(item)

        log.debug('Manager finished.')


class Worker:
    """Вот кто будет жопу рвать за всех остальных нахлебников"""
    def __init__(self, coordinator_address):
        self.coordinator = coordinator_address
        self.username = re.compile(r"User '(.*?)'")
        self.ipaddr_middle = re.compile(r'(\.\d{1,3}\.\d{1,3}\.)')
        self.cache = {}
        log.debug('Worker initialized.')

    def __call__(self, message):
        log.debug('Worker started.')
        seq, line = message
        for name in self.username.findall(line):
            try:
                line = line.replace("User '%s'" % name,
                                    "User '%s'" % self.cache[name])
            except KeyError:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(self.coordinator)
                sock.send(bytes(name, 'utf-8'))
                self.cache[name] = str(sock.recv(128))[2:-1]
                sock.close()
                line = line.replace("User '%s'" % name,
                                    "User '%s'" % self.cache[name])

        for ip in self.ipaddr_middle.findall(line):
            try:
                line = line.replace(ip, self.cache[ip])
            except KeyError:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(self.coordinator)
                sock.send(bytes(ip, 'utf-8'))
                self.cache[ip] = str(sock.recv(128))[2:-1]
                sock.close()
                line = line.replace(ip, self.cache[ip])

        log.debug('Worker finished.')
        return seq, line


class Coordinator(threading.Thread):
    """
    Прослушивание сокета и глобальное управление заменами.
    """
    def __init__(self, address):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(2.0)
        self.socket.bind(address)
        self.socket.listen(5)
        self.substitution = {}
        self.stopped = False
        log.debug('Coordinator initialized.')

    def run(self):
        log.debug('Coordinator started.')
        while not self.stopped:
            try:
                # Ждем коннекта
                connection, client_address = self.socket.accept()
            except socket.timeout:
                continue

            # Получаем запрос
            key = connection.recv(128)
            log.debug('Coordinator receives: %s' % key)

            # Получаем значение подстановки из своего словаря
            try:
                reply = self.substitution[key]
            # Или генерируем случайное, если его нет
            except KeyError:
                reply = str(random.randint(1, 1024))
                self.substitution[key] = reply
                log.debug('New substitution created: %s -> %s' % (key, reply))

            # Засылаем ответ
            try:
                # Вот вам и разница между питонами!
                # Сработает в python2:
                connection.send(reply)
            except TypeError:
                # сработает в python3:
                connection.send(bytes(reply, 'utf-8'))

            # Закрываем соединение
            connection.close()
        else:
            self.socket.close()
        log.debug('Coordinator finished.')

    def stop(self):
        log.debug('Coordinator will now stop.')
        self.stopped = True


############################# Главная функция ##################################
# Несколько слов насчет первых трех строк. Дефолтное значение первого аргумента
# устанавливается в None. Потом проверяется, не None ли оно и изменяется, если
# None. Кажется нелогичным и излишним. Хочется написать: main(argv=sys.argv[1:])
# Но делать этого нельзя. Потому что дефолтные значения аргументов вычисляются
# сразу же при объявлении функции, а в этот момент переменная sys.argv еще не
# установлена. Получим ошибку.
def main(argv=None):
    log.info('New run. Hello everybody!')
    if argv is None:
        argv = sys.argv[1:]

    # здесь будут парситься параметры командной строки,
    # если они однажды появятся

    # Настраиваемся:
    # Очередь задач. Записывает - reader. Читает - manager.
    jobs_queue = mp.Queue(maxsize=1000)
    # Итератор по очереди задач. С возможностью остановки извне.
    jobs_iter = QueueIter(jobs_queue)
    # Очередь результатов. Записывает - manager. Читает - writer.
    results_queue = mp.Queue()

    # инициализируем компоненты:
    components = {
        'reader': Reader(INPUT_FILE, jobs_queue),
        'writer': Writer(OUTPUT_FILE, results_queue),
        'coordinator': Coordinator(SOCK_NAME),
        'manager': Manager(jobs_iter, results_queue, SOCK_NAME),
    }
    log.info('Components initialized.')
    # запускаем их все и надеемся, что взлетим...
    for component_instance in components.values():
        component_instance.start()
    log.info('Components started.')

    # ждем пока дочитается файл
    components['reader'].join()
    log.info('Reached end of input file.')
    log.debug('Reader alive: %s' % components['reader'].is_alive())

    # ждем пока рабочие разберут все задачи из очереди
    while not jobs_queue.empty():
        time.sleep(1)
    log.debug('Jobs queue is empty.')

    # тормозим итератор задач
    jobs_iter.stop()
    log.debug('Stopping jobs iterator.')

    # ждем пока остановится менеджер
    components['manager'].join()
    log.info('Manager finished.')
    log.debug('Manager alive: %s' % components['manager'].is_alive())

    # останавливаем остальные компоненты
    log.debug('Trying to stop writer.')
    components['writer'].stop()
    log.debug('Trying to stop coordinator.')
    components['coordinator'].stop()
    time.sleep(2)
    log.debug('Writer alive: %s' % components['writer'].is_alive())
    log.debug('Coordinator alive: %s' % components['coordinator'].is_alive())

    log.info('All components stopped.')

    # если сюда добрались - значит код возврата 0
    return 0


if __name__ == '__main__':
    sys.exit(main())

