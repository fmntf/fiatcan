import dbus
import dbus.mainloop.glib
import threading
from gi.repository import GLib


class PhoneManager:

    listeners = {}
    mainloop = None
    bus = None
    should_run = True

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()
        self.bus = dbus.SystemBus()

        self.bus.add_signal_receiver(self.on_signal,
                                     dbus_interface='org.ofono.VoiceCallManager',
                                     member_keyword='member')

        thread = threading.Thread(target=self.start)
        thread.start()

    def on_signal(self, *args, **kwargs):
        if kwargs['member'] == 'CallAdded':
            number = args[1]['LineIdentification']
            self.fire_event('call', number)
            print("Call: {}".format(number))

        elif kwargs['member'] == 'CallRemoved':
            print("Call end")
            self.fire_event('call', None)

    def start(self):
        self.mainloop.run()

    def prepare_shutdown(self):
        self.should_run = False
        self.mainloop.quit()

    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
