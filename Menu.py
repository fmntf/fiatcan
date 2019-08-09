import time
import subprocess
from TextMessage import TextMessage


class MenuItem:

    def __init__(self, string: str, callback: callable, items: list = None) -> object:
        self.string = string
        self.callback = callback
        self.items = items

    def click(self):
        self.callback()

    def __getitem__(self, key):
        return self.items[key]

    def __len__(self) -> int:
        return len(self.items)


class Menu:

    bus = None
    tm = TextMessage()
    active_items = []
    menu = None
    listeners = {}
    phone_calling = False

    def __init__(self, bus):
        def dismiss_menu():
            self.active_items = []
            self.instpanel_display(None)

        def temp_show(message, sec=2):
            self.instpanel_display(message)
            time.sleep(sec)
            self.instpanel_display(None)

        def info_callback():
            result = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
            kernel_version = result.stdout.decode('UTF8').strip()
            self.instpanel_display(kernel_version)
            self.active_item = None

        def reboot_callback():
            temp_show("Reboot...", 2)
            subprocess.run(['sudo', 'reboot'])

        def submenu_callback():
            self.active_items.append(0)
            item = self.get_active_item()
            self.instpanel_display(item.string, True)

        self.bus = bus
        self.menu = [
            MenuItem('KERNEL', info_callback),
            MenuItem('REBOOT', submenu_callback, [
                MenuItem('CONFERMA? SI', reboot_callback),
                MenuItem('CONFERMA? NO', dismiss_menu),
            ]),
        ]

    def on_button(self, key):
        print("[menu] key {}".format(key))
        if key == 'menu':
            if len(self.active_items) == 0:
                self.active_items.append(0)
                item = self.get_active_item()
                self.instpanel_display(item.string, True)

            else:
                item = self.get_active_item()
                item.click()

        elif key == 'down':
            if len(self.active_items) > 0:
                menu = self.get_active_menu()
                idx = self.active_items[-1]
                idx = (idx - 1) % len(menu)
                self.active_items[-1] = idx
                item = self.get_active_item()
                self.instpanel_display(item.string, True)

        elif key == 'up':
            if len(self.active_items) > 0:
                menu = self.get_active_menu()
                idx = self.active_items[-1]
                idx = (idx + 1) % len(menu)
                self.active_items[-1] = idx
                item = self.get_active_item()
                self.instpanel_display(item.string, True)

        elif key == 'mute':
            if len(self.active_items) > 0:
                self.active_items.pop()
                if len(self.active_items) > 0:
                    item = self.get_active_item()
                    self.instpanel_display(item.string, True)
                else:
                    self.instpanel_display(None)

    def get_active_item(self):
        item = self.menu
        for idx in self.active_items:
            item = item[idx]

        return item

    def get_active_menu(self):
        menu = self.menu
        for idx in self.active_items[0:-1]:
            menu = menu[idx]

        return menu

    def instpanel_display(self, message=None, is_menu=False):
        print("[menu] {}".format(message))
        self.fire_event('menu', message)
        if message is None:
            self.tm.clear_instpanel(self.bus)
        else:
            self.tm.send_instpanel(self.bus, message, is_menu)

    def on_phone(self, number):
        if number is None:
            self.phone_calling = False
        else:
            self.phone_calling = True

    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
