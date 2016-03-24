# Python Chip8 Interpreter Keyboard
# Joshua Tyler 09/15

from pygame import *


class keyboard:

    # Constants
    #  Hex keyboard,of format:
    #   1   2   3   C
    #   4   5   6   D
    #   7   8   9   E
    #   A   0   B   F

    __keyBindings = [K_x,               #0
                     K_1, K_2, K_3,     #123
                     K_q, K_w, K_e,     #456
                     K_a, K_s, K_d,     #789
                     K_z, K_c, K_4, K_r, K_f, K_v, ]   #ABCDEF


    __pressedKeys = "" # will be 16 bit array contraining key states

    def __init__(self):
        init()
        self.__pressedKeys = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


    def loadPressedKeys(self):
        event.pump()
        rawKeys = key.get_pressed()

        for i in range(1,16):
            if rawKeys[self.__keyBindings[i]]:
                self.__pressedKeys[i] = 1
            else:
                self.__pressedKeys[i] = 0


    def waitForKeypress(self):
        self.loadPressedKeys()

        while self.__pressedKeys.count(1) == 0:  # Wait for keypress
            self.loadPressedKeys()

        return list.index(1)  # Return lowest key pressed


    def checkIfPressed(self, key):
        self.loadPressedKeys()

        return self.__pressedKeys[key]