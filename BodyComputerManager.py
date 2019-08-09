import can
import os
import threading
import time
from can import Message
from FiatProtocol import *
from SteeringWheelButtons import SteeringWheelButtons
from TextMessage import TextMessage


class BodyComputerManager(threading.Thread):

    should_run = True
    listeners = {}
    tm = TextMessage()
    buttons = None

    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.buttons = SteeringWheelButtons()

    def run(self):
        br = can.BufferedReader()
        notifier = can.Notifier(self.bus, [br])

        bm_playing = False
        date_sync = False

        while self.should_run:
            message = br.get_message(1)
            if message is not None:
                arbid = "{0:08x}".format(message.arbitration_id).upper()
                payload = ba(message.data)
                #print("From {}: {}".format(arbid, payload))

                if message.arbitration_id == CANID_BODY_BUTTONS:  # buttons
                    if payload & MASK_BUTTON_VOLUME_UP == MASK_BUTTON_VOLUME_UP:
                        self.buttons.debounce('vol+')
                    if payload & MASK_BUTTON_VOLUME_DN == MASK_BUTTON_VOLUME_DN:
                        self.buttons.debounce('vol-')
                    if payload & MASK_BUTTON_WINDOWS == MASK_BUTTON_WINDOWS:
                        self.buttons.debounce('win')
                    if payload & MASK_BUTTON_MUTE == MASK_BUTTON_MUTE:
                        self.buttons.debounce('mute')
                    if payload & MASK_BUTTON_UP == MASK_BUTTON_UP:
                        self.buttons.debounce('up')
                    if payload & MASK_BUTTON_DOWN == MASK_BUTTON_DOWN:
                        self.buttons.debounce('down')
                    if payload & MASK_BUTTON_MENU == MASK_BUTTON_MENU:
                        self.buttons.debounce('menu')
                    if payload & MASK_BUTTON_SOURCE == MASK_BUTTON_SOURCE:
                        self.buttons.debounce('src')

                elif message.arbitration_id == CANID_BODY_STATUS:
                    sys_status = payload[0:16]
                    #print("Body computer asked for status, answering {}...".format(sys_status))
                    self.bus.send(Message(arbitration_id=CANID_BM_STATUS, data=bytearray(sys_status.bytes)))

                elif message.arbitration_id == CANID_4003_PROXI:
                    print("Answering PROXI request")
                    self.bus.send(Message(arbitration_id=CANID_BM_PROXI, data=bytearray(payload.bytes)))

                elif message.arbitration_id == CANID_4003_CLOCK:
                    if not date_sync:
                        payload_str = payload.__str__()
                        formatted_date = "{}-{}-{} {}:{}:00".format(
                            payload_str[10:14], payload_str[8:10], payload_str[6:8], payload_str[2:4], payload_str[4:6]
                        )
                        os.system('sudo date -s "{}"'.format(formatted_date))
                        date_sync = True

                elif message.arbitration_id == CANID_RADIO_AUDIOCH:
                    if payload & MASK_RADIO_AUDIOCH_MPMUTE_O == MASK_RADIO_AUDIOCH_MPMUTE_O:
                        if not bm_playing:
                            bm_playing = True
                            self.fire_event('bm_playing', bm_playing)
                    if payload & MASK_RADIO_AUDIOCH_MPMUTE_I == MASK_RADIO_AUDIOCH_MPMUTE_I:
                        if bm_playing:
                            bm_playing = False
                            self.fire_event('bm_playing', bm_playing)

        notifier.stop()

    def shutdown(self):
        self.should_run = False



    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
