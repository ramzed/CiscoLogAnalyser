# -*- coding: utf-8 -*-
"""
Thread-класс, выполняющий следующие функции:
1. Ведение общего словаря замен, которые делают рабочие
2. Прием запросов от рабочих через сокет
"""

#TODO: добавить отдельные словари для имен пользователей, хостов и ip-адресов

#TODO: написать функции генерирующие случайные величины для каждого из словарей

#TODO: определить API, по которому рабочие смогут обращаться в конкретный словарь

import socket
import random

from stoppable_loop import StoppableLoop
from log import log


class Coordinator(StoppableLoop):
    name = 'Coordinator'

    def __init__(self, address):
        StoppableLoop.__init__(self)

        # сокет, на котором мы принимаем запросы
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(2.0)  # таймаут для всех операций с сокетом:
                                     # accept(), recv() и др.
        self.socket.bind(address)
        self.socket.listen(5)

        # это наш словарь замен
        self.substitution = {}

    # переопределяем метод родителя
    def logic(self):
        try:
            # Ждем коннекта
            connection, client_address = self.socket.accept()
        except socket.timeout:
            return

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

    def shut_down(self):
        self.socket.close()
