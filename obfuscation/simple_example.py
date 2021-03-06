#!/usr/bin/python
#-*- coding: utf-8 -*-
"""
Этот скрипт служит для скрытия приватной информации в логах.

Он заменяет такие вещи как username, ip_address, hostname - на случайные,
сохраняя при этом одинаковые случайные строки, там где фигурировал один и тот же
исходный ключ.
"""
# Метаданные
__author__ = 'Pavel Lazarenko and all'
__version__ = '1.0'

######################## Импорт стандартных библиотек ##########################
import sys
import os
import re
import random
# Нам потребуется генерировать случайные наборы английских печатных символов
# К сожалению в разных версиях питона нужный объект называется по-разному,
# Чтобы сгладить эту разницу мы переопределим имя при импорте из второго питона.
# Итак, предполагаем, что мы находимся во втором питоне:
try:
    # сработает в python 2
    from string import lowercase as ascii_lowercase
# Если мы все-таки оказались в третьем, то интерпретатор сгенерирует исключение
# ImportError, которое мы перехватим.
except ImportError:
    # сработает в python 3
    from string import ascii_lowercase
# В результате у нас есть переменная ascii_lowercase, вне зависимости от того,
# какая версия интерпретатора запущена

################################# Константы ####################################
# (в соответствии с PEP8 - заглавными буквами)
DEFAULT_FILENAME = 'obfuscation/dutylog'

############################ Глабальные переменные #############################
# re.compile() - возвращает объект, который может в последствии использоваться
#                для быстрого применения регулярных выражений. Такая
#                предварительная компиляция используется, когда необходимо
#                проводить большое количество операций поиска по одниому и тому
#                же шаблону
username = re.compile(r"User '(.*?)'")
ipaddr_middle = re.compile(r'(\.\d{1,3}\.\d{1,3}\.)')
# синтаксис регулярных выражений:
# https://docs.python.org/2/library/re.html#regular-expression-syntax


################################################################################
# Служебные функции
def parse(filename):
    """
    Разбирает исходный файл по строкам, выделяя в каждой из них: дату, имя
    хоста и тело сообщения.

    :param filename: имя файла
    :return: итератор, возвращающий кортежи вида: (date, host, message)
    """
    # assert используется программистом для самопроверки, в данном случае
    # мы хотим убедиться, что передаем в функцию именно строку (а не например,
    # объект File)
    assert isinstance(filename, str)

    # Теперь мы хотим проверить, что получили на вход существующее в системе
    # имя, указывающее на файл.
    if not os.path.exists(filename) or not os.path.isfile(filename):
        # если такой файл не существует или это не файл, а директория например
        # мы прервем исполнение скрипта с ошибкой
        raise RuntimeError('Bad file name: %s' % filename)

    # Открываем файл на чтение
    # Синтаксис 'with ...' рекомендуется к использованию, так как он
    # автоматически закроет файл, когда мы выйдем из этого блока кода.
    with open(filename, 'r') as f:
        # Данный синтаксис перебора строк в файле читает по одной строке за
        # итерацию. (В отличие от for line in f.readlines(): - который сразу
        # читает весь файл и размещает его в памяти в виде списка строк)
        for line in f:
            # Секция занимающаяся непосредственно парсингом строки заключена
            # в блок try - except, для того, чтобы не делать лишних проверок,
            # является ли текущая строка правильной. Если строка неверна, на
            # одном из этапов мы получим исключение и ее обработка прервется
            # безболезненно для остальных строк.
            try:
                # Бьем строку на части с помощью разделителя по умолчанию
                # (первый параметр = None) при этом делая не более 3 разбиений
                # (второй парамерт = 3)
                # Разделитель по умолчанию - пустое поле (пробелы и табы)
                fields = line.split(None, 3)
                # Следующие три строчки - отвратительное распихивание элементов
                # списка по переменным. Не гибкое и полное потенциальных ошибок.
                date = ' '.join(fields[:2])
                host = fields[2]
                message = fields[3].strip()
            # Исключение IndexError возникнет в том случае, если при разделении
            # строки на подстроки получилось меньше четырех кусочков - такие
            # строки нас не интересуют, пропускаем ее и переходим к следующей
            except IndexError:
                continue
            # Секция else будет выполнена только, если код в секции try не
            # вызвал никаких ошибок. В данном случае - нет ошибок, значит можно
            # возвращать данные
            else:
                # Оператор yield позволит нам превратить эту функцию в генератор
                # До тех пох пока не закончится основной цикл (for line in f),
                # функция будет доходить до этого места и возвращать данные, но
                # при этом внутреннее ее состояние сохранится, и при следующем
                # обращении выполнение продолжится с этого же места.
                # Таким образом мы можем разделить чтение данных и обработку
                # данных, что позитивно скажется на нашем коде.
                yield date, host, message


def random_ip_middle():
    """
    Возвращает два случайных октета в виде, пригодном для размещения посередине
    ip адреса: .134.234. (с точками по краям)
    :return: str
    """
    return '.%d.%d.' % (random.randint(0, 255), random.randint(0, 255))


def obfuscate(filename):
    """
    Главная функция. (Можно было бы даже назвать ее main =))

    Выполняет логику скрипта, т.е. замену имен и адресов на случайные.

    :param filename: имя файла
    :type filename: str
    :return: итератор по обфусцированным строкам
    """
    # Для того, чтобы сопоставлять одни и те же исходные имена и адреса
    # одним и тем же случайным, нужно сохранять те замены, которые мы уже
    # сделали. В словарь.
    users = {}
    ips = {}

    # Вызываем функцию-генератор parse (см. описание выше)
    # На каждом шаге она возвращает нам три элемента (а точнее кортеж из 3-х
    # элементов, который мы сразу же распаковываем (размещаем) в локальные
    # переменные: date, host, message)
    for date, host, message in parse(filename):

        ### Заменяем имена
        # username - это скомпилированный нами заранее шаблон поиска
        # (см. секцию 'глобальные переменные')
        # Метод findall() вернет список всех найденных совпадений.
        # Здесь нужно обратить внимание на положение скобок в исходном шаблоне.
        # Так как будет возвращено именно содержимое этих скобок.
        for name in username.findall(message):
            # Следующая конструкция позволит нам сэкономить на проверках,
            # встречался ли этот пользователь раньше.
            # Мы пытаемся работать так, как будто этот пользователь уже нам
            # известен и занесен в словарь users
            try:
                # Заменяем имя реального пользователя на случайное
                message = message.replace("User '%s'" % name,
                                          "User '%s'" % users[name])
            # Если же этого пользователя в словаре нет, будет сгенерировано
            # исключение KeyError, которое мы перехватим и (с пониманием того,
            # что раз была ошибка, значит это новый пользователь) добавим его
            # в свой словарь
            except KeyError:
                # ascii_lowercase - это строка из всех букв нижнего регистра.
                # Строка в питоне поддерживает итерацию по своим символам,
                # Поэтому метод random.choice() применим, и возвращает он один
                # символ.
                # for i in range(8) - заставляет эту выборку произойти 8 раз,
                # а обертка из: ''.join(...) склеивает все эти 8 символов между
                # собой с помощью пустой строки.
                users[name] = ''.join([random.choice(ascii_lowercase)
                                       for i in range(8)])
                # заменяем имя реального пользователя на случайное, уже не боясь
                # промахнуться.
                message = message.replace("User '%s'" % name,
                                          "User '%s'" % users[name])

        ### Заменяем два средних октета в IP-адресах
        # Процедура тут абсолютно та же самая, что и для имен, поэтому
        # я не буду ее повторять.
        for ip in ipaddr_middle.findall(message):
            try:
                message = message.replace(ip, ips[ip])
            except KeyError:
                # Единственная разница в том, что строка для замены геренируется
                # отдельной функцией, описание которой смотри выше
                ips[ip] = random_ip_middle()
                message = message.replace(ip, ips[ip])

        # И снова мы превратим нашу функцию в генератор, и будем возвращать
        # по одной обработанной строке за раз.
        yield date, host, message


def main():
    # Вызываем функцию-генератор obfuscate
    for date, host, message in obfuscate(DEFAULT_FILENAME):
        # и просто раз за разом печатаем то, что она возвращает
        print(date, host, message)
    return 0

# Эта конструкция является правилом хорошего тона при создании скриптов python.
# У каждого запускаемого модуля есть атрибут __name__ (черт его побери! в питоне
# даже сама программа это тоже объект! объектно-ориентированный до мозга костей)
# Этот атрибут равер имени файла, в котором содержится код без суффикса .py во
# всех случаях кроме одного - если этот файл непосредственно запускается первым.
# В этом случае его атрибут __name__ устанавливается в специальное значение =
# '__main__'. Такие образом проверив значение этого атрибута мы можем понять,
# что делают с этим кодом: запускают или импортируют. И как правило для
# обработки этих ситуаций логика должна быть разная.
if __name__ == "__main__":
    # Таким образом этот блок будет выполнен только в том случае, если
    # этот файл непосредственно запущен на выполнение.
    sys.exit(main())