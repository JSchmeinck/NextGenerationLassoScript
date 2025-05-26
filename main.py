import tkinter as tk
import GUI_Master
import sys
import os


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller stores temp files here
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainApp:
    def __init__(self, master_window):
        self.master_window = master_window

        self.gui = GUI_Master.GUI(master_window=self.master_window, main=self)



if __name__ == '__main__':
    root = tk.Tk()
    root.iconbitmap(resource_path("lassoimage.ico"))
    main_app = MainApp(master_window=root)
    tk.mainloop()
