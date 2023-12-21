import win11toast

import os
import sys
import subprocess


def resource(relative_path):
    base_path = getattr(
        sys,
        '_MEIPASS',
        os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
class Notifications:
    def __init__(self, gui):
        self.gui = gui

    def notification_folder(self, header, body, folder):


        win11toast.toast(header, body, app_id="LassoTool", on_click=lambda args: self.open_folder(folder))

    def notification_error(self, header, body):

        win11toast.toast(header, body, icon=resource('Error Icon.png'), app_id="LassoTool")

    def notification_yesno(self, header, body):
        icon = {
            'src': resource('Warning Icon.png'),
            'placement': 'appLogoOverride'
        }

        output = win11toast.toast(header, body, icon=icon, app_id="LassoTool", buttons=['Yes', 'No'], duration='1000')

        if output['arguments'].removeprefix('http:') == 'Yes':
            return True
        if output['arguments'].removeprefix('http:') == 'No':
            return False

    def open_folder(self, folder):
        folder = folder.replace('/', '\\')
        os.startfile(folder)


if __name__ == "__main__":
    notifications = Notifications(gui=2)
    notifications.notification_folder(header='Test', body='Test', folder='C:\Messdaten cuteToF')

