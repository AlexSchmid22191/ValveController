import sys
import time
import datetime
import Engine
import functools


class CVC:
    def __init__(self, txtpath=None, port=None):
        self.engine = Engine.Valvolino(port=port)
        self.txtpath = txtpath
        self.instructions = []
        self.runtime = datetime.timedelta(seconds=0)

    def parse_txt(self):
        with open(self.txtpath) as text:
            for line in text.readlines():
                line.lower()
                if line.startswith('wait'):
                    seconds = int(line.split(',')[-1])
                    print(seconds)
                    self.runtime += datetime.timedelta(seconds=seconds)
                    self.instructions.append([functools.partial(time.sleep, seconds), seconds, 'W'])
                elif line.startswith('toggle'):
                    valve = int(line.split(',')[1].split('V')[-1])
                    self.instructions.append([lambda: self.engine.toggle_valve(valve), valve, 'T'])
            print('Total runtime: {:s}'.format(str(self.runtime)))

    def execute(self):
        start_time = datetime.datetime.now()
        logpath = 'Log_{:s}.txt'.format(start_time.strftime('%Y-%m-%dT%H-%M-%S'))

        for instruction in self.instructions:
            if instruction[2] == 'T':
                valve = instruction[1]
                s = '{:s}\tToggled valve {:d}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                                                        valve)
                with open(logpath, 'a') as log:
                    log.write(s)
                    print(s[:-1])
            else:
                print('{:s}\tWaiting {:d} seconds'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                                                          instruction[1]))
            instruction[0]()
        print('{:s}\tFinished'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')))

    @staticmethod
    def selfsleep(secs):
        starttime = updatetime = datetime.datetime.now()
        while not (datetime.datetime.now() - starttime).seconds > secs:
            if (datetime.datetime.now() - updatetime).seconds > 1:
                updatetime = datetime.datetime.now()
                print('.', end='')
        print('')
        return


if __name__ == '__main__':
    try:
        textpath, comport = sys.argv[1:3]
    except (IndexError, ValueError):
        textpath = input('Enter instruction file:')
        comport = input('Enter COM Port:')

    cvc = CVC(txtpath=textpath, port=comport)
    cvc.engine.connect()
    cvc.parse_txt()
    cvc.execute()
