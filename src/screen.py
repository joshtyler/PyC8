# Python Chip8 Interpreter Screen
# Joshua Tyler 09/15

import logging

import pygame


class screen:

    __WIDTH = 64

    __HEIGHT = 32

    __COLOUR_DEPTH = 8

    __SCALE_FACTOR = 16

    __PIXEL_0 = pygame.Color(0, 0, 0, 255)

    __PIXEL_1 = pygame.Color(255, 255, 255, 255)

    __display = "0"

    def __init__(self):
        pygame.init()
        self.__display = pygame.display.set_mode([self.__WIDTH * self.__SCALE_FACTOR, self.__HEIGHT * self.__SCALE_FACTOR], 0, self.__COLOUR_DEPTH)

    def clearScreen(self):
        self.__display.fill(self.__PIXEL_0)
        pygame.display.update()

    def XORByte(self, byteToDraw, x, y):

        y = y % self.__HEIGHT

        eraseFlag = 0

        for i in range(0,8):
            realX = (x+i) % self.__WIDTH
            oldVal = self.getPixel( realX,y)
            newVal = (byteToDraw >> 7 -i) & 0b00000001
            valToWrite = int(bool(oldVal) ^ bool(newVal))
            self.setPixel(realX, y, valToWrite)
            if valToWrite == 0 and oldVal == 1:
                eraseFlag = 1

        return eraseFlag

    def setPixel(self, x, y, color):
        x *= self.__SCALE_FACTOR
        y *= self.__SCALE_FACTOR

        if color == 0:
            color = self.__PIXEL_0
        else:
            color = self.__PIXEL_1

        pygame.draw.rect(self.__display, color, (x, y, self.__SCALE_FACTOR, self.__SCALE_FACTOR), 0 )

        pygame.display.update()


    def getPixel(self, x, y):
        x *= self.__SCALE_FACTOR
        y *= self.__SCALE_FACTOR

        color = self.__display.get_at((x,y))

        if color == self.__PIXEL_0:
            return 0
        else:
            return 1

