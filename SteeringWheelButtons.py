import time


class SteeringWheelButtons:

    listeners = {}
    debouncers = {}

    phone_calling = False
    menu_opened = False

    def debounce(self, button):
        if button in self.debouncers:
            if time.time() - self.debouncers[button] < 0.3:
                return

        self.debouncers[button] = time.time()
        self.fire_event('button', button)

        if button == 'menu':
            if self.phone_calling:
                print("[buttons] phone")
                self.fire_event('phone', button)
            else:
                print("[buttons] menu")
                self.fire_event('menu', button)

        if button == 'up' or button == 'down' or button == 'mute':
            if self.menu_opened:
                print("[buttons] menu")
                self.fire_event('menu', button)
            else:
                print("[buttons] media")
                self.fire_event('media', button)

    def on_phone(self, number):
        if number is None:
            self.phone_calling = False
        else:
            self.phone_calling = True

    def on_menu_opened(self, is_open):
        self.menu_opened = is_open

    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
