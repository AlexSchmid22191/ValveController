# Send a few comamnds over Serial port to test communication and valvolino Hardware

import Valvolino
import random
import time

# Adjust manually
valvo = Valvolino.Valvolino(port='COM11')

time.sleep(1)

while True:
    valvo.toggle_valve(1)
    valvo.toggle_valve(2)
    valvo.toggle_valve(3)
    valvo.toggle_valve(4)
    time.sleep(random.random()/10)
