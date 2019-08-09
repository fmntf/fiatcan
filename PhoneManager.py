import dbus
import dbus.mainloop.glib
import threading
from gi.repository import GLib


class PhoneManager:

    listeners = {}
    mainloop = None
    bus = None
    should_run = True

    call_state = 'disconnected'
    hangup_call = None
    answer_call = None

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()
        self.bus = dbus.SystemBus()

        self.bus.add_signal_receiver(self.on_signal,
                                     dbus_interface='org.ofono.VoiceCallManager',
                                     member_keyword='member')

        self.bus.add_signal_receiver(self.property_changed,
                                     bus_name="org.ofono",
                                     dbus_interface="org.ofono.VoiceCall",
                                     signal_name="PropertyChanged")

        thread = threading.Thread(target=self.start)
        thread.start()

    def on_signal(self, *args, **kwargs):
        if kwargs['member'] == 'CallAdded':
            number = args[1]['LineIdentification']

            obj = self.bus.get_object("org.ofono", args[0])
            iface = dbus.Interface(obj, "org.ofono.VoiceCall")
            self.hangup_call = iface.get_dbus_method("Hangup")
            self.answer_call = iface.get_dbus_method("Answer")
            properties = iface.get_dbus_method("GetProperties")()
            if 'State' in properties:
                self.call_state = properties["State"]
            else:
                self.call_state = "incoming"

            self.fire_event('call', number)
            print("Call: {}".format(number))

        elif kwargs['member'] == 'CallRemoved':
            print("Call end")
            self.fire_event('call', None)
            self.hangup_call = None
            self.answer_call = None

    def start(self):
        self.mainloop.run()

    def on_button(self, key):
        print("[phone] key {}".format(key))
        if key == 'menu':
            if self.call_state == 'incoming':
                self.answer_call()
            else:
                if self.hangup_call is not None:
                    self.hangup_call()

    def property_changed(self, key, value):
        print("Call {}: {}".format(key, value))
        if key == 'State':
            self.call_state = value

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
