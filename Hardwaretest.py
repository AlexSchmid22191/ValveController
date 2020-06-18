# Send a few comamnds over Serial port to test communication and valvolino Hardware

import Valvolino
import random
import time

# Adjust manually
valvo = Valvolino.Valvolino(port='/dev/ttyUSB0')

time.sleep(3)

while True:
    for i in range(1, 5):
        valvo.toggle_valve(i)
        time.sleep(random.random()/10)
#    time.sleep(random.random())
