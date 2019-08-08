import time
import subprocess


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

    active_items = []
    ivr = None
    listeners = {}

    def __init__(self):

        def dismiss_menu():
            self.active_items = []
            self.fire_event('instpanel_display', None)

        def info_callback():
            result = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
            kernel_version = result.stdout.decode('UTF8').strip()
            self.fire_event('instpanel_display', kernel_version)
            self.active_item = None

        def shutdown_callback():
            self.fire_event('shutdown')
            self.fire_event('instpanel_display', "Shutdown...")
            time.sleep(2)
            self.fire_event('instpanel_display', None)
            subprocess.run(['sudo', 'poweroff'])

        def submenu_callback():
            self.active_items.append(0)
            item = self.get_active_item()
            self.fire_event('instpanel_display', item.string, True)

        self.ivr = [
            MenuItem('KERNEL', info_callback),
            MenuItem('SHUTDOWN', submenu_callback, [
                MenuItem('CONFERMA? SI', shutdown_callback),
                MenuItem('CONFERMA? NO', dismiss_menu),
            ]),
        ]

    def on_button(self, key):
        print("[menu] on_button "+key)
        if key == 'menu':
            if len(self.active_items) == 0:
                self.active_items.append(0)
                item = self.get_active_item()
                self.fire_event('instpanel_display', item.string, True)

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
                self.fire_event('instpanel_display', item.string, True)
            else:
                self.fire_event('remote', 'prev')

        elif key == 'up':
            if len(self.active_items) > 0:
                menu = self.get_active_menu()
                idx = self.active_items[-1]
                idx = (idx + 1) % len(menu)
                self.active_items[-1] = idx
                item = self.get_active_item()
                self.fire_event('instpanel_display', item.string, True)
            else:
                self.fire_event('remote', 'next')

        elif key == 'mute':
            if len(self.active_items) > 0:
                self.active_items.pop()
                if len(self.active_items) > 0:
                    item = self.get_active_item()
                    self.fire_event('instpanel_display', item.string, True)
                else:
                    self.fire_event('instpanel_display', None)
            else:
                self.fire_event('remote', 'mute')

    def get_active_item(self):
        item = self.ivr
        for idx in self.active_items:
            item = item[idx]

        return item

    def get_active_menu(self):
        menu = self.ivr
        for idx in self.active_items[0:-1]:
            menu = menu[idx]

        return menu

    def fire_event(self, event, *args):
        if event not in self.listeners:
            return
        for listener in self.listeners[event]:
            listener(*args)

    def on_event(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
