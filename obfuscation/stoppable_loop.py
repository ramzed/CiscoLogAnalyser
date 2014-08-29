# -*- coding: utf-8 -*-
"""
Thread-класс, выполняющий бесконечный цикл, до тех пор пока его
не остановят командой извне.
"""

import threading
from log import log


class StoppableLoop(threading.Thread):
    name = ''

    def __init__(self):
        threading.Thread.__init__(self)
        log.debug('%s: initialisation...' % self.name)
        self.stopped = False

    # Метод run() будет вызван при запуске треды на выполнение
    def run(self):
        log.debug('%s: starting...' % self.name)
        while not self.stopped:
            self.logic()
        else:
            self.shut_down()
        log.debug('%s: stopping...' % self.name)

    # Метод stop() будем вызывать мы, чтобы остановиться
    def stop(self):
        log.debug('%s: got stop request.' % self.name)
        self.stopped = True

    # Этот метод нужно переопределить в потомках
    def logic(self):
        raise NotImplementedError

    # в этом методе нужно сделать уборку за собой (закрыть сокеты,
    # сбросить остаток информации на диск и т.п.)
    def shut_down(self):
        pass