# -*- coding:utf-8 -*-
"""
Общая сущность для ведения журнала.
"""

import logging

log = logging.Logger('obfuscator')


def set_log_file(file_name, log_level):
    """
    Конфигурирует и добавляет обработчик для записи в файл

    :param file_name: имя лог-файла (будет перезаписан)
    :type file_name: str
    :param log_level: уровень логирования (INFO, DEBUG и т.д.)
    :type log_level: str
    """
    assert hasattr(logging, log_level.upper())

    log_format = logging.Formatter(
        fmt='%(levelname)-10s %(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    #    style='%',
    )
    file_handler = logging.StreamHandler(open(file_name, 'w'))
    file_handler.setFormatter(log_format)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    log.addHandler(file_handler)
