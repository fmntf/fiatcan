import time
import threading
from can import Message
from FiatProtocol import *


class CanOneHertzLoop(threading.Thread):

    should_run = True
    body_operational = True
    bm_operational = True
    track_position = 0
    bm_ch_playing = None
    bm_ch_muted = None
    bm_channel = None
    bm_is_playing = False

    def __init__(self, bus):
        super().__init__()
        self.bus = bus

        self.bm_ch_playing = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray(MASK_AUDIOCH_MEDIAPLAYER.bytes))
        self.bm_ch_muted = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray(MASK_AUDIOCH_MUTED.bytes))
        self.bm_channel = self.bm_ch_muted

    def run(self):
        watchdog1 = Message(arbitration_id=CANID_BM_WATCHDOG, data=bytearray(MESSAGE_BM_WATCHDOG1.bytes))
        watchdog2 = Message(arbitration_id=CANID_BM_WATCHDOG, data=bytearray(MESSAGE_BM_WATCHDOG2.bytes))

        start_time = time.time()
        while self.should_run:
            if self.body_operational and self.bm_operational:
                self.bus.send(self.bm_channel)
                time.sleep(0.3)

                self.bus.send(Message(arbitration_id=CANID_BM_TRACK_TIME,
                                      data=bytearray(ba(
                                      hex="0x{:02d}{:02d}487800000000".format(self.track_position // 60,
                                                                              self.track_position % 60)).bytes)))
                time.sleep(0.3)

                self.bus.send(watchdog1)
                time.sleep(0.02)
                self.bus.send(watchdog2)

                if self.bm_is_playing:
                    self.track_position += 1

            else:
                print("1Hz thread stopped: {}, {}".format(self.body_operational, self.bm_operational))

            time.sleep(1.0 - ((time.time() - start_time) % 1.0))

    def on_bm_playing(self, is_playing):
        self.bm_is_playing = is_playing
        if is_playing:
            self.bm_channel = self.bm_ch_playing
        else:
            self.bm_channel = self.bm_ch_muted

    def on_track_position(self, seconds):
        self.track_position = seconds

    def prepare_shutdown(self):
        self.should_run = False

    def on_body_state_change(self, body_operational):
        self.body_operational = body_operational

    def on_bm_state_change(self, bm_operational):
        self.bm_operational = bm_operational

    def on_shutdown(self):
        self.bm_operational = False
