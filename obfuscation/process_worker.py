# -*- coding: utf-8 -*-
"""
Выполнение грязной работы.
Наиболее трудоемкая часть скрипта.
"""

#TODO: оптимизировать работу регулярных выражений

#TODO: добавить новые паттерны поиска в соответствии с документацией

import re
import socket


class Worker:
    def __init__(self, coordinator_address):
        self.coordinator = coordinator_address
        self.username = re.compile(r"User '(.*?)'")
        self.ipaddr_middle = re.compile(r'(\.\d{1,3}\.\d{1,3}\.)')
        self.cache = {}

    def __call__(self, message):
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

        return seq, line