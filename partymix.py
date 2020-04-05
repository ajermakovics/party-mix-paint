#!/usr/bin/env python3
"""
Paint using Numark Party Mix
License: GNU GPL
"""

from sys import exit
import time

try:
    import mido
    import turtle
except ImportError:
    print("Please install:")
    print("  pip3 install mido python-rtmidi turtle")
    exit(1)

# Party Mix key mapping
class Deck:
    def __init__(self, controlChannel, noteChannel):
        self.WHEEL = f"channel={controlChannel},control=6"
        self.FADER = f"channel={controlChannel},control=9"
        self.SCRATCH = f"channel={controlChannel},note=7"
        self.HEADPHONES = f"channel={controlChannel},note=27"
        self.PAD1 = f"channel={noteChannel},note=20"
        self.PAD2 = f"channel={noteChannel},note=21"
        self.PAD3 = f"channel={noteChannel},note=22"
        self.PAD4 = f"channel={noteChannel},note=23"
        self.PLAY_PAUSE = f"channel={controlChannel},note=0"
        self.CUE = f"channel={controlChannel},note=1"
        self.SYNC = f"channel={controlChannel},note=2"

class Keys:
    DECK1 = Deck(0, 4)
    DECK2 = Deck(1, 5)
#TODO: Master keys

class MixController:
    def __init__(self, pen, devname, cb=False):
        if cb:
            self.midi_in = mido.open_input(devname, callback=self.midi_callback)
        else:
            self.midi_in = mido.open_input(devname)
        self.midi_out = mido.open_output(devname)
        self.lastEventTime = time.time()
        self.pen = self.initPen(pen)

    # Pen using Turtle: https://docs.python.org/3.3/library/turtle.html?highlight=turtle
    def initPen(self, pen):
        turtle.bgcolor("black")
        pen.pendown()
        pen.pencolor("white")
        pen.width(3)
        return pen

    # Read messages from device. Rate limited
    def pump(self):
        for msg in self.midi_in.iter_pending():
            if time.time() - self.lastEventTime > 0.05: # limit to 20 events per second (1/20)
                self.midi_callback(msg)
                self.lastEventTime = time.time()

    def toggleLights(self, on=True):
        #TODO: find specific channel and note for lights
        for chan in range(15):
            for note in range(127):
                self.sendNoteOn(chan, note, on)

    # Handle events from device (button press)
    def midi_callback(self, msg):
        key = self.key(msg)
        print('Msg:', msg, ", key:", key)

        if Keys.DECK1.PLAY_PAUSE == key:
            print(f"Pressed Play/Pause. Exiting")
            self.close()
            exit(0)
        elif Keys.DECK1.SYNC == key:
            self.pen.clear()
        elif Keys.DECK2.HEADPHONES == key:
            if msg.type == 'note_on':
                self.toggleLights(True)
            else:
                self.toggleLights(False)
        elif Keys.DECK1.WHEEL == key:
            if msg.value > 124:
                self.pen.backward(3)
            else:
                self.pen.forward(3)
        elif Keys.DECK2.WHEEL == key:
            if msg.value > 124:
                self.pen.left(20)
            else:
                self.pen.right(20)
        elif Keys.DECK1.PAD1 == key:
            self.pen.pencolor("red")
        elif Keys.DECK1.PAD2 == key:
            self.pen.pencolor("green")
        elif Keys.DECK1.PAD3 == key:
            self.pen.pencolor("blue")
        elif Keys.DECK1.PAD4 == key:
            self.pen.pencolor("yellow")
        elif Keys.DECK1.FADER == key:
            self.pen.shapesize(msg.value/10)
            self.pen.width(msg.value)
        elif Keys.DECK1.HEADPHONES == key:
            if msg.type == 'note_on':
                self.pen.penup()
            else:
                self.pen.pendown()
        elif Keys.DECK2.PAD1 == key:
            self.pen.pencolor("orange")
        elif Keys.DECK2.PAD2 == key:
            self.pen.pencolor("purple")
        elif Keys.DECK2.PAD3 == key:
            self.pen.pencolor("turquoise")
        elif Keys.DECK2.PAD4 == key:
            self.pen.pencolor("white")

    def key(self, msg):
        if msg.type == 'control_change':
            return f"channel={msg.channel},control={msg.control}"
        # else 'note_on' or 'note_off'
        return f"channel={msg.channel},note={msg.note}"

    def sendNoteOn(self, chan, note, on=True):
        vel=127 if on else 0
        msg = mido.Message('note_on', channel=chan, note=note, velocity=vel)
        self.midi_out.send(msg)

    def close(self):
        self.midi_out.close()
        self.midi_in.close()
        self.midi_in = self.midi_out = None


devices = mido.get_ioport_names()
deviceName = None
NUMARK_DEVICE_NAME='Party Mix'

print('MIDI devices:')
for device in devices:
    print('- ' + device)
    if device.startswith(NUMARK_DEVICE_NAME):
        print('  Found: ', device)
        deviceName = device

if deviceName is None:
    print(f"Couldn't find a Mix device '{NUMARK_DEVICE_NAME}', exiting.")
    exit(1)

cb = False
running = True

controller = MixController(turtle.Pen(), deviceName, cb)

# turtle.mainloop()

while running:
    if not cb: controller.pump()
