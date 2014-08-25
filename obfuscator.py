import re
import random
import string

__author__ = 'Pavel Lazarenko'

FILENAME = 'dutylog'

username = re.compile(r"User '(.*?)'")
ipaddr_middle = re.compile(r'(\.\d{1,3}\.\d{1,3}\.)')


def parse(filename):
    """
    Function for parsing rsyslog files for future processing

    :param filename:
    :return: iterator over (date, host, message) tuples
    """
    assert isinstance(filename, str)
    with open(filename) as f:
        for line in f:
            try:
                fields = line.split(None, 3)
                date = ' '.join(fields[:2])
                host = fields[2]
                message = fields[3].strip()
                yield date, host, message
            except IndexError:
                continue


def random_ip_middle():
    return '.%d.%d.' % (random.randint(0, 255), random.randint(0, 255))


def obfuscate(filename):
    """
    This function reads a file line by line and changes unsecured words
    (IP addresses, user names) to some random shit.

    :param filename: name of log file to process
    :type filename: str
    :return: iterator over obfuscated lines
    """
    users = {}
    ips = {}
    for date, host, message in parse(filename):
        # Changing User fields
        for name in username.findall(message):
            try:
                message = message.replace("User '%s'" % name, "User '%s'" % users[name])
            except KeyError:
                try:
                    # python 2
                    users[name] = ''.join(random.choice(string.lowercase) for i in range(8))
                except AttributeError:
                    # python 3
                    users[name] = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                message = message.replace("User '%s'" % name, "User '%s'" % users[name])

        # Changing IP addresses
        for ip in ipaddr_middle.findall(message):
            try:
                message = message.replace(ip, ips[ip])
            except KeyError:
                ips[ip] = random_ip_middle()
                message = message.replace(ip, ips[ip])
        # Changing anything else

        yield date, host, message


if __name__ == "__main__":
    for date, host, message in obfuscate(FILENAME):
        print(date, host, message)