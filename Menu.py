import os
import os.path
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
    menu = None
    listeners = {}
    phone_calling = False
    candumping = None

    def __init__(self):
        if os.path.isfile('/otgstorage/readwrite'):
            fslabel = 'Make readonly'
            is_readwrite = True
        else:
            fslabel = 'Make readwrite'
            is_readwrite = False

        def dismiss_menu():
            self.active_items = []
            self.instpanel_display(None)

        def temp_show(message, sec=2):
            self.instpanel_display(message)
            time.sleep(sec)
            self.instpanel_display(None)

        def version_callback():
            result = subprocess.run(["dpkg-query", "--showformat='${Version}'", "--show", "infotainment"], stdout=subprocess.PIPE)
            infot_version = result.stdout.decode('UTF8').strip()

            result = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
            kernel_version = result.stdout.decode('UTF8').strip()

            self.instpanel_display("{}/{}".format(infot_version, kernel_version))

        def candump_callback():
            if self.candumping is None:
                ret = os.system("sudo datamount")
                if ret != 0:
                    self.instpanel_display("mount err {}".format(ret))
                    return
                self.candumping = subprocess.Popen(['candump', '-l', 'can0'], cwd='/data/traces')
                self.instpanel_display("dump started")
            else:
                self.candumping.kill()
                self.candumping = None
                if os.system("sudo dataumount") != 0:
                    self.instpanel_display("umount error")
                self.instpanel_display("dump stopped")

        def restart_callback():
            temp_show("Restarting...", 2)
            subprocess.run(['sudo', 'systemctl', 'restart', 'infotainment'])

        def submenu_callback():
            self.active_items.append(0)
            item = self.get_active_item()
            self.instpanel_display(item.string, True)

        def rootfs_callback():
            if is_readwrite:
                self.instpanel_display("Rebooting RO...")
                os.system("sudo rootfsro")
            else:
                self.instpanel_display("Rebooting RW...")
                os.system("sudo rootfsrw")

        self.menu = [
            MenuItem('Version', version_callback),
            MenuItem('Candump', candump_callback),
            MenuItem('Restart srvc', submenu_callback, [
                MenuItem('Confirm? No', dismiss_menu),
                MenuItem('Confirm? Yes', restart_callback),
            ]),
            MenuItem(fslabel, submenu_callback, [
                MenuItem('Confirm? No', dismiss_menu),
                MenuItem('Confirm? Yes', rootfs_callback),
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

        elif key == 'up':
            if len(self.active_items) > 0:
                menu = self.get_active_menu()
                idx = self.active_items[-1]
                idx = (idx - 1) % len(menu)
                self.active_items[-1] = idx
                item = self.get_active_item()
                self.instpanel_display(item.string, True)

        elif key == 'down':
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

    def instpanel_display(self, message=None, show_arrows=False):
        print("[menu] {}".format(message))
        self.fire_event('item', message, show_arrows)

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
