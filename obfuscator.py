import re
import random
import string

__author__ = 'Pavel Lazarenko'

FILENAME = 'dutylog'


def seq_iter(obj):
    return obj if isinstance(obj, dict) else xrange(len(obj))


def parse(filename):
    """
    Function for parsing rsyslog files for the next processing
    :param filename:
    :return: list

    """
    assert isinstance(filename, str)
    f = open(filename)
    parsed_file = []
    for line in f.readlines():
        parsed_line = []
        for field in line.split('  '):
            if field:
                parsed_line.append(field)
        if len(parsed_line) == 3:
            parsed_file.append(parsed_line)
    return parsed_file


def obfuscate(parsed_file):
    """

    """
    users = {}
    ips = {}
    for line in seq_iter(parsed_file):
        assert isinstance(line, int)
        # Change User field
        regexp = re.compile(r"(User '.*')")
        username = regexp.search(parsed_file[line][2])
        if username and username.group():
            name = username.group().split("User ")[1].strip("'").split("'")[0]
            if name not in users:
                users[name] = ''.join(random.choice(string.lowercase) for i in range(8))
            parsed_file[line] = [parsed_file[line][0], parsed_file[line][1],
                                 re.sub(r"User '([a-z]+)'", "User '" + users[name] + "'", parsed_file[line][2])]

        # Change IP address
        r = r'((([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])[ (\[]?(\.|dot)' \
            r'[ )\]]?){3}([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]))[,| |/]'
        regexp = re.compile(r)
        ip = regexp.findall(parsed_file[line][2])
        if ip:
            for addr in ip:
                ad = addr[0]
                if ad not in ips:
                    ips[ad] = ad.split('.')[0] + '.' + ad.split('.')[1] + '.' + str(random.randint(0, 255)) + '.' + str(
                        random.randint(0, 255))
                parsed_file[line] = [parsed_file[line][0], parsed_file[line][1],
                                     re.sub(ad, ips[ad], parsed_file[line][2])]
        # Change anything else

    return parsed_file


if __name__ == "__main__":
    for line in obfuscate(parse(FILENAME)):
        print line[2]