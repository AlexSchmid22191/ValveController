import sys
import time
import datetime
import Engine


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
                    self.runtime += datetime.timedelta(seconds=seconds)
                    self.instructions.append(lambda: time.sleep(seconds))
                elif line.startswith('toggle'):
                    valve = line.split(',')[1].split('V')[-1]
                    self.instructions.append(lambda: self.engine.toggle_valve(valve))
            print('Total runtime: {:s}'.format(str(self.runtime)))

    def execute(self):
        for instruction in self.instructions:
            instruction()


try:
    textpath, comport = sys.argv[1:3]
except IndexError:
    textpath = input('Enter instruction file:')
    comport = input('Enter COM Port:')


if __name__ == '__main__':
    cvc = CVC(txtpath=textpath, port=comport)
    cvc.parse_txt()
    cvc.execute()
