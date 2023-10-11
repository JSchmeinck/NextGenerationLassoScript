import tkinter as tk
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import numpy as np
import pandas as pd
import matplotlib.patches as patches
from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import PolygonSelector

class LogfileViewer:

    def __init__(self, gui, master_window):
        self.gui = gui
        self.window = tk.Toplevel(master=master_window)
        self.window.title("Image Synchronization")
        self.window.geometry('750x600')
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.resizable(width=False, height=False)
        self.window.withdraw()

        self.fig = plt.figure(frameon=False)
        self.ax = self.fig.add_axes([0.08, 0.09, 0.9, 0.85])
        self.canvas_draw_image = None

        self.rectangles_dictionary = {}

        self.label = tk.Label(self.window, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(side=tk.BOTTOM, fill=tk.X)


    def on_closing(self):
        self.window.withdraw()

    def show_logfile(self):

        logfile_dataframe = self.gui.importer.import_laser_logfile(logfile=self.gui.logfile_filepath,
                                                                   laser_type=self.gui.widgets.laser_type.get(),
                                                                   iolite_file=True,
                                                                   rectangular_data_calculation=True,
                                                                   logfile_viewer=True)

        xmin, xmax, ymin, ymax = self.buid_rectangles(logfile=logfile_dataframe)

        self.ax.set_xlim(left=xmin*0.8, right=xmax*1.2)
        self.ax.set_ylim(bottom=ymin * 0.95, top=ymax * 1.05)
        self.ax.invert_yaxis()

        if self.canvas_draw_image is None:
            self.canvas_draw_image = FigureCanvasTkAgg(self.fig, master=self.window)
            self.toolbar = NavigationToolbar2Tk(self.canvas_draw_image, self.window)
            self.toolbar.update()
            self.canvas_draw_image.get_tk_widget().pack()

            self.canvas_draw_image.mpl_connect("motion_notify_event", self.on_hover)


        else:
            self.canvas_draw_image.draw()

        self.window.deiconify()

    def buid_rectangles(self, logfile):
        self.rectangles_dictionary = {}

        for idx, row in logfile.iloc[::2].iterrows():
            x_start = row['X(um)']/1000
            y_start = row['Y(um)']/1000
            width = (logfile.loc[idx + 1, 'X(um)'] - row['X(um)'])/1000
            height = row['Spotsize']/1000
            if idx == 0:
                xmin = x_start
                xmax = x_start + width
                ymin = y_start
                ymax = y_start + height
            if x_start < xmin:
                xmin = x_start
            if (x_start + width) > xmax:
                xmax = (x_start + width)
            if y_start < ymin:
                ymin = y_start
            if (y_start + height) > ymax:
                ymax = (y_start + height)

            rectangle = patches.Rectangle((x_start, y_start), width, height, edgecolor='g', facecolor='none')
            self.ax.add_patch(rectangle)

            self.rectangles_dictionary[row['Name']] = rectangle

        return xmin, xmax, ymin, ymax

    def on_hover(self, event):
        for name, rectangle in self.rectangles_dictionary.items():
            if rectangle.contains(event)[0]:
                self.label.config(text=name)
                return
        self.label.config(text="")
