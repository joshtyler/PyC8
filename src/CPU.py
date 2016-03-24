# Python Chip8 Interpreter CPU
# Joshua Tyler 09/15

from array import *
from threading import Timer
from screen import *
from keyboard import *
import logging
import random

class CPU:

    # Constants
    __font = array('B', [
        0xF0, 0x90, 0x90, 0x90, 0xF0,
        0x20, 0x60, 0x20, 0x20, 0x70,
        0xF0, 0x10, 0xF0, 0x80, 0xF0,
        0xF0, 0x10, 0xF0, 0x10, 0xF0,
        0x90, 0x90, 0xF0, 0x10, 0x10,
        0xF0, 0x80, 0xF0, 0x10, 0xF0,
        0xF0, 0x80, 0xF0, 0x90, 0xF0,
        0xF0, 0x10, 0x20, 0x40, 0x40,
        0xF0, 0x90, 0xF0, 0x90, 0xF0,
        0xF0, 0x90, 0xF0, 0x10, 0xF0,
        0xF0, 0x90, 0xF0, 0x90, 0x90,
        0xE0, 0x90, 0xE0, 0x90, 0xE0,
        0xF0, 0x80, 0x80, 0x80, 0xF0,
        0xE0, 0x90, 0x90, 0x90, 0xE0,
        0xF0, 0x80, 0xF0, 0x80, 0xF0,
        0xF0, 0x80, 0xF0, 0x80, 0x80
    ])

    __PROG_START = 0x200 # Address of start of program

    __STACK_DEPTH = 16

    # Variables
    __mem = array('B')  # General memory, 'B' is Unsigned byte
    __V = array('B')  # Gen purpose registers
    __I = "0"  # 16 bit General purpose register

    __PC = "0"  # Program counter
    __SP = "0"  # Stack pointer
    __stack = array('H')  # Unsigned short (2 bytes)
    __DT = "0"  # delay timer
    __ST = "0"  # sound timer

    __instruction = "0"  # Variable to store current instruction

    __disp = "0"  # Display

    __keyb = "0" # Keyboard

    #  Methods
    def __init__(self, file, display, keyboard):
        self.__mem.extend(self.__font) # Load font to start of memory
        padMemory(self.__mem, 0, self.__PROG_START - 1)  # Pad until program start
        assert(self.__mem.buffer_info()[1] * self.__mem.itemsize -1 == 0x1FF)  # Assert if font is not correct size
        self.__mem.fromfile(file, getFileSize(file))  # Load memory from file
        self.__V = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 16 general purpose registers
        self.__I = 0

        self.__PC = self.__PROG_START
        self.__SP = 0
        self.__stack = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 16 layer stack

        self.__disp = display
        self.__keyb = keyboard

        # Call timer functions to setup timer callbacks
        logging.warning("Add sound output")
        self.__ST = 0  # sound timer
        self.__soundTimer()
        self.__DT = 0  # delay timer
        self.__delayTimer()

        #  Jump table for most significant nibble of instruction
        self.__GenOpDecode = {
            0x0:   self.__op0ClearReturn,
            0x1:   self.__op1Jump,
            0x2:   self.__op2Call,
            0x3:   self.__op3SkipEqualConst,
            0x4:   self.__op4SkipNotEqualConst,
            0x5:   self.__op5SkipEqualRegister,
            0x6:   self.__op6LoadConstantV,
            0x7:   self.__op7AddConstantV,
            0x8:   self.__op8MathematicalLogical,
            0x9:   self.__op9SkipNotEqualRegister,
            0xA:   self.__opALoadConstantI,
            0xB:   self.__opBJumpAdd,
            0xC:   self.__opCRandAND,
            0xD:   self.__opDSprite,
            0xE:   self.__opEKeyboard,
            0xF:   self.__opFMisc
        }

        #  Jump table for least significant nibble of instruction, if most significant is 8
        self.__MathOpDecode = {
            0x0:   self.__op8_0LdVxVy,
            0x1:   self.__op8_1ORVxVy,
            0x2:   self.__op8_2ANDVxVy,
            0x3:   self.__op8_3XORVxVy,
            0x4:   self.__op8_4AddVxVy,
            0x5:   self.__op8_5SubVxVy,
            0x6:   self.__op8_6ShrVx,
            0x7:   self.__op8_7SubNVxVy,
            0xE:   self.__op8_EShlVx
        }

        #  Jump table for least significant byte of instruction, if most significant is F
        self.__MiscOpDecode = {
            0x07:   self.__opF_07LoadVxDT,
            0x0A:   self.__opF_0ALoadVxK,
            0x15:   self.__opF_15LoadDTVx,
            0x18:   self.__opF_18LoadSTVx,
            0x1E:   self.__opF_1EAddIVx,
            0x29:   self.__opF_29LoadFVx,
            0x33:   self.__opF_33LoadBVx,
            0x55:   self.__opF_55LoadIVx,
            0x65:   self.__opF_33LoadVxI,
        }

    def __soundTimer(self):
        if self.__ST > 0:
            self.__ST -= 1
            #Activate sound here

        Timer(1.0/60.0, self.__soundTimer).start()  # Callback at 60Hz

    def __delayTimer(self):
        if self.__DT > 0:
            self.__DT -= 1

        Timer(1.0/60.0, self.__delayTimer).start()  # Callback at 60Hz

    def start(self):
        while self.__PC < ( self.__mem.buffer_info()[1] * self.__mem.itemsize - 1):  # Only loop while inside program range

            self.__instruction = self.__mem[self.__PC] << 8 | self.__mem[self.__PC + 1]  #  load two byte instruction
            logging.debug("Instruction: %s", hex(self.__instruction))

            self.__PC += 2  # Increment here to avoid messing up jumps

            self.__GenOpDecode[(self.__instruction & 0xF000) >> 12]()

    # Base instruction functions
    def __op0ClearReturn(self):
        logging.debug("0x0 opcode")

        if self.__instruction == 0x00E0:
            logging.debug("Clear Screen")
            self.__disp.clearScreen()
        elif self.__instruction == 0x00EE:
            logging.debug("Return from subroutine")
            assert(self.__SP > 0)
            self.__PC = self.__stack[self.__SP]
            self.__SP -= 1
        else :
            logging.warning("Redundant opcode: %s", hex(self.__instruction))


    def __op1Jump(self):
        logging.debug("0x1 opcode \n Jump")
        self.__PC = self.__instruction & 0x0FFF

    def __op2Call(self):
        logging.debug("0x2 opcode \n Call subroutine")
        assert(self.__SP +1 < self.__STACK_DEPTH)

        self.__SP += 1
        self.__stack[self.__SP] = self.__PC
        self.__PC = self.__instruction & 0x0FFF

    def __op3SkipEqualConst(self):
        logging.debug("0x3 opcode \n Skip if Vx = constant")

        if self.__V[(self.__instruction & 0x0F00) >> 8] == self.__instruction & 0x00FF:
            self.__PC += 2


    def __op4SkipNotEqualConst(self):
        logging.debug("0x4 opcode \n Skip if Vx != constant")

        if self.__V[(self.__instruction & 0x0F00) >> 8] != self.__instruction & 0x00FF:
            self.__PC += 2

    def __op5SkipEqualRegister(self):
        logging.debug("0x3 opcode \n Skip if Vx = Vy")

        if self.__V[(self.__instruction & 0x0F00) >> 8] == self.__V[(self.__instruction & 0x00F0) >> 4]:
            self.__PC += 2

    def __op6LoadConstantV(self):
        logging.debug("0x6 opcode \n Load constant to Vx")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__instruction & 0x00FF

    def __op7AddConstantV(self):
        logging.debug("0x7 opcode \n Add constant to Vx")
        self.__V[(self.__instruction & 0x0F00) >> 8] += self.__instruction & 0x00FF

    def __op8MathematicalLogical(self):
        logging.debug("0x8 opcode")
        self.__MathOpDecode[self.__instruction & 0x000F]()

    def __op9SkipNotEqualRegister(self):
        logging.debug("0x9 opcode \n Skip if Vx != Vy")

        if self.__V[(self.__instruction & 0x0F00) >> 8] != self.__V[(self.__instruction & 0x00F0) >> 4]:
            self.__PC += 2

    def __opALoadConstantI(self):
        logging.debug("0xA opcode \n Set I to constant")
        self.__I = self.__instruction & 0x0FFF

    def __opBJumpAdd(self):
        logging.debug("0xB opcode \n Jump to I plus V0")
        self.__op1Jump()
        self.__PC +=  self.__V[0]

    def __opCRandAND(self):
        logging.debug("0xC opcode \n Store random int ANDed with constant in Vx")
        randNo = random.randint(0, 255)
        constant = self.__instruction & 0x00FF

        self.__V[(self.__instruction & 0x0F00) >> 8] = randNo & constant

    def __opDSprite(self):
        logging.debug("0xD opcode \n Read and draw sprite")
        noBytes = self.__instruction & 0x000F

        x = self.__V[(self.__instruction & 0x0F00) >> 8]
        y = self.__V[(self.__instruction & 0x00F0) >> 4]

        logging.debug("Loading %d byte sprite from %s. Drawing to x: %d, y: %d", noBytes, hex(self.__I), x, y)
        # Ensure we are not trying to read outside of program memory
        assert(self.__mem.buffer_info()[1] * self.__mem.itemsize -1 >= self.__I + (noBytes -1) )

        self.__V[0xF] = 0  # Clear erased flag

        for i in range(0, noBytes):
            temp = self.__mem[self.__I + i]
            erased = self.__disp.XORByte(temp, x, y + i)

            if erased:
                self.__V[0xF] = 1

    def __opEKeyboard(self):
        logging.debug("0xE opcode")
        if self.__instruction & 0x00FF == 0x009E:
            logging.debug("Skip if key in Vx is pressed")
            if self.__keyb.checkIfPressed(self.__V[(self.__instruction & 0x0F00) >> 8]):
                self.__PC += 2

        elif self.__instruction & 0x00FF == 0x00A1:
            logging.debug("Skip if key in Vx is not pressed")
            if self.__keyb.checkIfPressed(self.__V[(self.__instruction & 0x0F00) >> 8]):
                self.__PC += 2
        else :
            logging.warning("Invalid opcode: %s", hex(self.__instruction))

    def __opFMisc(self):
        logging.debug("0xF opcode")
        self.__MiscOpDecode[self.__instruction & 0x00FF]()

    # 0x8XXX instructions
    def __op8_0LdVxVy(self):
        logging.debug("Set Vx = Vy")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__V[(self.__instruction & 0x00F0) >> 4]


    def __op8_1ORVxVy(self):
        logging.debug("Set Vx = Vx OR Vy")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__V[(self.__instruction & 0x00F0) >> 4] | self.__V[(self.__instruction & 0x0F00) >> 8]

    def __op8_2ANDVxVy(self):
        logging.debug("Set Vx = Vx AND Vy")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__V[(self.__instruction & 0x00F0) >> 4] & self.__V[(self.__instruction & 0x0F00) >> 8]

    def __op8_3XORVxVy(self):
        logging.debug("Set Vx = Vx XOR Vy")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__V[(self.__instruction & 0x00F0) >> 4] ^ self.__V[(self.__instruction & 0x0F00) >> 8]

    def __op8_4AddVxVy(self):
        logging.debug("Set Vx = Vx + Vy. Vf is carry")
        result = self.__V[(self.__instruction & 0x0F00) >> 8] + self.__V[(self.__instruction & 0x00F0) >> 4]

        if result & 0xFF != 0:
            self.__V[0xF] = 1
        else:
            self.__V[0xF] = 0

        self.__V[(self.__instruction & 0x0F00) >> 8] = result & 0xFF

    def __op8_5SubVxVy(self):
        logging.debug("Set Vx = Vx - Vy. Vf is NOT Borrwo")
        result = self.__V[(self.__instruction & 0x0F00) >> 8] - self.__V[(self.__instruction & 0x00F0) >> 4]

        if result > 0:
            self.__V[0xF] = 1
        else:
            self.__V[0xF] = 0

        self.__V[(self.__instruction & 0x0F00) >> 8] = result & 0xFF

    def __op8_6ShrVx(self):
        logging.debug("Shift Vx right. Vf is carry")

        self.__V[0xF] = self.__V[(self.__instruction & 0x0F00) >> 8] & 0b00000001

        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__V[(self.__instruction & 0x0F00) >> 8] >> 1


    def __op8_7SubNVxVy(self):
        logging.debug("Set Vx = Vy - Vx. Vf is NOT Borrow")
        result = self.__V[(self.__instruction & 0x00F0) >> 4] - self.__V[(self.__instruction & 0x0F00) >> 8]

        if result > 0:
            self.__V[0xF] = 1
        else:
            self.__V[0xF] = 0

        self.__V[(self.__instruction & 0x0F00) >> 8] = result & 0xFF


    def __op8_EShlVx(self):
        logging.debug("Shift Vx left. Vf is carry")

        self.__V[0xF] = self.__V[(self.__instruction & 0x0F00) >> 8] & 0b10000000

        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__V[(self.__instruction & 0x0F00) >> 8] << 1

    def __opF_07LoadVxDT(self):
        logging.debug("Vx = DT")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__DT

    def __opF_0ALoadVxK(self):
        logging.debug("Wait for keypress Store in Vx")
        self.__V[(self.__instruction & 0x0F00) >> 8] = self.__keyb.waitForKeypress()

    def __opF_15LoadDTVx(self):
        logging.debug("DT = Vx")
        self.__DT = self.__V[(self.__instruction & 0x0F00) >> 8]

    def __opF_18LoadSTVx(self):
        logging.debug("ST = Vx")
        self.__ST = self.__V[(self.__instruction & 0x0F00) >> 8]

    def __opF_1EAddIVx(self):
        logging.debug("I = I + Vx")
        self.__I += self.__V[(self.__instruction & 0x0F00) >> 8]

    def __opF_29LoadFVx(self):
        logging.debug("Set I to address of font sprite for value stored in Vx")
        self.__I = self.__V[(self.__instruction & 0x0F00) >> 8] * 5  # 5 bytes per sprite, starting at 0x00

    def __opF_33LoadBVx(self):
        logging.debug("Set data at address I, I+1, I+2 to BCD representation of Vx")
        number = self.__V[(self.__instruction & 0x0F00) >> 8]
        hundreds = int(number /100)
        tens = int((number - hundreds*100) /10)
        units = number - hundreds*100 -tens*10

        self.__mem[self.__I] = hundreds
        self.__mem[self.__I + 1] = tens
        self.__mem[self.__I + 2] = units

    def __opF_55LoadIVx(self):
        logging.debug("Store registers V0...Vx at mem with address I..I+15")

        max = self.__V[(self.__instruction & 0x0F00) >> 8] +1

        for i in range(0,max):
            self.__mem[self.__I + i] = self.__V[i]

        self.__I += max  # Customary from original implementation



    def __opF_33LoadVxI(self):
        logging.debug("Read registers V0...Vx from mem with address I..I+15")

        max = ((self.__instruction & 0x0F00) >> 8) + 1

        for i in range(0,max):
            self.__V[i] = self.__mem[self.__I + i]

        self.__I += max  # Customary from original implementation



def getFileSize(file):
    oldPos = file.tell()
    file.seek(0, 2)  # Seek end of file
    size = file.tell()
    logging.debug("File size: ", size," bytes")
    file.seek(oldPos, 0)  # Return to old position
    return size


def padMemory(arr, value, newSize):
    while arr.buffer_info()[1] * arr.itemsize <= newSize:
        arr.append(value)



