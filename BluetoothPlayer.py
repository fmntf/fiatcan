import threading
import dbus
import dbus.mainloop.glib
from gi.repository import GLib


class BluetoothPlayer:

    listeners = {}

    bt_connected = False
    media_connected = False
    music_playing = False

    mainloop = None
    bus = None

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
        self.mainloop.run()

    def prepare_shutdown(self):
        self.mainloop.quit()

    def properties_changed(self, interface, changed, invalidated, path):
        if interface == "org.bluez.Device1":
            if "Connected" in changed:
                self.bt_connected = changed["Connected"]
                print("Bluetooth connected: {}".format(self.bt_connected))

        if interface == "org.bluez.MediaControl1":
            if "Connected" in changed:
                self.media_connected = changed["Connected"]
                if self.media_connected:
                    print("Media is connected")
                    obj = self.bus.get_object("org.bluez", changed["Player"])
                    media_interface = dbus.Interface(obj, "org.bluez.MediaPlayer1")
                    self.pause_music = media_interface.get_dbus_method("Pause")
                    self.play_music = media_interface.get_dbus_method("Play")

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