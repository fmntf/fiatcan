import time


class InstrumentPanel:

    listeners = {}
    tm = None
    menu_opened = False

    def __init__(self, tm):
        self.tm = tm

    def on_menu(self, message, show_arrows):
        if message is None:
            self.tm.clear_instpanel()
            self.menu_opened = False
        else:
            self.tm.send_instpanel(message, show_arrows)
            self.menu_opened = True
        self.fire_event('menu_opened', self.menu_opened)

    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)

    def on_phone(self, number):
        if number is None:
            self.tm.send_instpanel("  Metto giu!")
            time.sleep(1)
            self.tm.clear_instpanel()
        else:
            self.tm.send_instpanel("Pronto?Pronto!")
