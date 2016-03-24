# Python Chip8 Interpreter Main Program
# Joshua Tyler 09/15

from CPU import *
from keyboard import *
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)

logging.getLogger().disabled = True

# Constants
FILENAME = "Breakout (Brix hack) [David Winter, 1997].ch8"

disp = screen()
keyb = keyboard()

file = open(FILENAME, 'rb')
myCPU = CPU(file, disp, keyb)

myCPU.start()