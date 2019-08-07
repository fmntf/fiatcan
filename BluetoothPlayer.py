import re
import threading
import time

import dbus
import dbus.mainloop.glib
from gi.repository import GLib


class BluetoothPlayer:

    listeners = {}
    mainloop = None
    bus = None
    connect_thread = None
    should_run = True

    bt_connected = False
    media_connected = False
    music_playing = False
    media_player = None
    pause_music = None
    play_music = None

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()
        self.bus = dbus.SystemBus()

        self.bus.add_signal_receiver(self.properties_changed,
            bus_name="org.bluez",
            dbus_interface="org.freedesktop.DBus.Properties",
            signal_name="PropertiesChanged",
            path_keyword="path")

        thread = threading.Thread(target=self.start)
        thread.start()

    def start(self):
        self.connect_thread = threading.Thread(target=self.connect_device)
        self.connect_thread.start()

        self.mainloop.run()

    def prepare_shutdown(self):
        self.should_run = False
        self.mainloop.quit()

    def connect_device(self):
        while self.should_run:
            time.sleep(10)
            if not self.bt_connected:
                print("Trying to connect devices...")
                obj = self.bus.get_object("org.bluez", "/")
                interface = dbus.Interface(obj, "org.freedesktop.DBus.ObjectManager")
                regexp = re.compile("(^/org/bluez/hci[0-9]/dev_[A-Z0-9_]+$)")

                for object in interface.GetManagedObjects():
                    matches = regexp.match(object)
                    if matches is not None:
                        hciobj = self.bus.get_object("org.bluez", matches[0])
                        hciiface = dbus.Interface(hciobj, "org.bluez.Device1")
                        conn = hciiface.get_dbus_method("Connect")
                        print("Connecting to {}".format(matches[0]))
                        try:
                            conn()
                            break
                        except:
                            pass
            time.sleep(30)


    def properties_changed(self, interface, changed, invalidated, path):
        if interface == "org.bluez.Device1":
            if "Connected" in changed:
                self.bt_connected = changed["Connected"]
                print("Bluetooth connected: {}".format(self.bt_connected))

        if interface == "org.bluez.MediaControl1":
            if "Player" in changed:
                self.media_player = changed["Player"]
            if "Connected" in changed:
                self.media_connected = changed["Connected"]
                if self.media_connected:
                    print("Media is connected, " + self.media_player)
                    obj = self.bus.get_object("org.bluez", self.media_player)
                    media_interface = dbus.Interface(obj, "org.bluez.MediaPlayer1")
                    self.pause_music = media_interface.get_dbus_method("Pause")
                    self.play_music = media_interface.get_dbus_method("Play")
                    time.sleep(5)
                    self.play_music()

        elif interface == "org.bluez.MediaPlayer1":
            if "Track" in changed:
                track = changed["Track"]
                self.fire_event('track', track["Title"], track["Artist"], track["Album"])
                print("Track: {} - {}".format(track["Title"], track["Artist"]))

            if "Status" in changed:
                if changed["Status"] == "playing":
                    self.music_playing = True
                    print("Music is playing")
                else:
                    self.music_playing = False
                    print("Music is paused")
                self.fire_event('playing', self.music_playing)

            if "Position" in changed:
                player_position = int(changed["Position"]/1000)
                self.fire_event('position', player_position)

    def on_bm_playing(self, is_playing):
        print("[player] on_bm_playing {}".format(is_playing))
        if self.media_connected:
            if is_playing:
                print("Player: play")
                self.play_music()
            else:
                print("Player: stop")
                self.pause_music()

    def on_button(self, key):
        print("[player] on_button "+key)
        if key == 'mute':
            if self.media_connected:
                if not self.music_playing:
                    self.play_music()
                else:
                    self.pause_music()


    def fire_event(self, event, *args):
        print("[player] fired "+event)
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)