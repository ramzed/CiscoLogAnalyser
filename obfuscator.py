__author__ = 'lyakovleva'

FILENAME = 'dutylog'

def parse(filename):
    """
    Function for parsing rsyslog files for the next processing
    :param filename:
    :return: list

    """
    assert isinstance(filename, basestring)
    f = open(filename)
    parsed_file = []
    for line in f.readlines():
        parsed_line = []
        for field in line.split('  '):
            if field:
                parsed_line.append(field)
        parsed_file.append(parsed_line)
    return parsed_file
        
if __name__ == "__main__":
    print parse(FILENAME)