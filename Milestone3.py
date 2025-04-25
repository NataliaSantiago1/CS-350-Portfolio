from gpiozero import Button, LED
from statemachine import StateMachine, State
from time import sleep
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from threading import Thread

DEBUG = True

class ManagedDisplay():
    def __init__(self):
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)

        self.lcd_columns = 16
        self.lcd_rows = 2 
        self.lcd = characterlcd.Character_LCD_Mono(self.lcd_rs, self.lcd_en, 
                    self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7, 
                    self.lcd_columns, self.lcd_rows)
        self.lcd.clear()
    
    def cleanupDisplay(self):
        self.lcd.clear()
    
    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message

class CWMachine(StateMachine):
    redLight = LED(18)
    blueLight = LED(23)
    message1 = 'SOS'
    message2 = 'OK'
    activeMessage = message1
    endTransmission = False
    screen = ManagedDisplay()
    morseDict = {
        "S": "...", "O": "---", "K": "-.-"
    }

    off = State(initial=True)
    dot = State()
    dash = State()
    dotDashPause = State()
    letterPause = State()
    wordPause = State()

    doDot = off.to(dot) | dot.to(off)
    doDash = off.to(dash) | dash.to(off)
    doDDP = off.to(dotDashPause) | dotDashPause.to(off)
    doLP = off.to(letterPause) | letterPause.to(off)
    doWP = off.to(wordPause) | wordPause.to(off)

    def on_enter_dot(self):
        self.redLight.on()
        sleep(0.5)

    def on_exit_dot(self):
        self.redLight.off()

    def on_enter_dash(self):
        self.blueLight.on()
        sleep(1.5)

    def on_exit_dash(self):
        self.blueLight.off()

    def on_enter_dotDashPause(self):
        sleep(0.25)

    def on_enter_letterPause(self):
        sleep(0.75)

    def on_enter_wordPause(self):
        sleep(3.0)

    def toggleMessage(self):
        self.activeMessage = self.message2 if self.activeMessage == self.message1 else self.message1

    def processButton(self):
        self.toggleMessage()

    def run(self):
        myThread = Thread(target=self.transmit)
        myThread.start()
    
    def transmit(self):
        while not self.endTransmission:
            self.screen.updateScreen(f"Sending:\n{self.activeMessage}")
            wordList = self.activeMessage.split()
            for word in wordList:
                for char in word:
                    morse = self.morseDict.get(char, '')
                    for symbol in morse:
                        if symbol == '.':
                            self.doDot()
                        elif symbol == '-':
                            self.doDash()
                        self.doDDP()
                    self.doLP()
                self.doWP()
        self.screen.cleanupDisplay()

cwMachine = CWMachine()
cwMachine.run()
greenButton = Button(24)
greenButton.when_pressed = cwMachine.processButton

repeat = True
while repeat:
    try:
        sleep(20)
    except KeyboardInterrupt:
        repeat = False
        cwMachine.endTransmission = True
        sleep(1)
