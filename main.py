import tkinter as tk
import GUI_Master
import sys
import os


def resource(relative_path):
    base_path = getattr(
        sys,
        '_MEIPASS',
        os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MainApp:
    def __init__(self, master_window):
        self.master_window = master_window

        self.gui = GUI_Master.GUI(master_window=self.master_window, main=self)
        self.gui.grid_gui_widgets()

    def show_gui(self):
        self.gui.grid_gui_widgets()


if __name__ == '__main__':
    root = tk.Tk()
    root.iconbitmap(resource("lassoimage.ico"))
    main_app = MainApp(master_window=root)
    main_app.show_gui()
    tk.mainloop()
