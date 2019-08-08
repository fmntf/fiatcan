import can
import os
import threading
import time
from can import Message
from FiatProtocol import *
from TextMessage import TextMessage


class BodyComputerManager(threading.Thread):

    should_run = True
    listeners = {}
    tm = TextMessage()
    button_debouncers = {}

    def __init__(self, bus):
        super().__init__()
        self.bus = bus

    def run(self):
        br = can.BufferedReader()
        notifier = can.Notifier(self.bus, [br])

        body_operational = True
        bm_operational = True
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
                        self.debounce_button('vol+')
                    if payload & MASK_BUTTON_VOLUME_DN == MASK_BUTTON_VOLUME_DN:
                        self.debounce_button('vol-')
                    if payload & MASK_BUTTON_WINDOWS == MASK_BUTTON_WINDOWS:
                        self.debounce_button('win')
                    if payload & MASK_BUTTON_MUTE == MASK_BUTTON_MUTE:
                        self.debounce_button('mute')
                    if payload & MASK_BUTTON_UP == MASK_BUTTON_UP:
                        self.debounce_button('up')
                    if payload & MASK_BUTTON_DOWN == MASK_BUTTON_DOWN:
                        self.debounce_button('down')
                    if payload & MASK_BUTTON_MENU == MASK_BUTTON_MENU:
                        self.debounce_button('menu')
                    if payload & MASK_BUTTON_SOURCE == MASK_BUTTON_SOURCE:
                        self.debounce_button('src')

                elif message.arbitration_id == CANID_BODY_STATUS:
                    if bm_operational:
                        sys_status = payload[0:16]
                    else:
                        sys_status = ba(hex='0x000A')

                    #print("Body computer asked for status, answering {}...".format(sys_status))
                    self.bus.send(Message(arbitration_id=CANID_BM_STATUS, data=bytearray(sys_status.bytes)))
                    if sys_status & MESSAGE_STATUS_WORKING == MESSAGE_STATUS_WORKING:
                        if not body_operational:
                            body_operational = True
                            self.fire_event('body_state_change', body_operational)
                    else:
                        if body_operational:
                            body_operational = False
                            self.fire_event('body_state_change', body_operational)
                        bm_operational = False
                        self.fire_event('bm_state_change', bm_operational)

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

    def prepare_shutdown(self):
        self.should_run = False

    def instpanel_display(self, message=None, is_menu=False):
        if message is None:
            self.tm.clear_instpanel(self.bus)
        else:
            self.tm.send_instpanel(self.bus, message, is_menu)

    def radiounit_display(self, title, artist):
        self.tm.send_music(self.bus, title, artist)

    def debounce_button(self, button):
        if button in self.button_debouncers:
            if time.time() - self.button_debouncers[button] < 0.3:
                return

        self.button_debouncers[button] = time.time()
        self.fire_event('button', button)

    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
