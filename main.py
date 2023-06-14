import tkinter as tk
import GUI_Master


class MainApp:
    def __init__(self, master_window):
        self.master_window = master_window

        self.gui = GUI_Master.GUI(master_window=self.master_window)
        self.gui.grid_gui_widgets()

    def show_gui(self):
        self.gui.grid_gui_widgets()


if __name__ == '__main__':
    root = tk.Tk()
    main_app = MainApp(master_window=root)
    main_app.show_gui()
    tk.mainloop()
