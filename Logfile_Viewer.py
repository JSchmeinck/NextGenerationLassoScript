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

        self.polygon_vertices_list_start = []
        self.polygon_vertices_list_end = []
        self.polygon_vertices_list_complete = []
        self.polygon_dictionary = {}

    def on_closing(self):
        self.window.withdraw()

    def show_logfile(self):
        self.ax.cla()
        self.polygon_dictionary = {}



        logfile_dataframe = self.gui.importer.import_laser_logfile(logfile=self.gui.logfile_filepath,
                                                                   laser_type=self.gui.widgets.laser_type.get(),
                                                                   iolite_file=True,
                                                                   rectangular_data_calculation=True,
                                                                   logfile_viewer=True)

        sample_separated_logfile = self.divide_samples(logfile=logfile_dataframe)

        xmin, xmax, ymin, ymax = self.buid_rectangles(logfile=logfile_dataframe)

        for sample_number, polygon_file in self.polygon_dictionary.items():
            self.build_polygons(number=sample_number, polygon_vertices=polygon_file)

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
        sample_number = 0
        for idx, row in logfile.iloc[::2].iterrows():
            if self.gui.widgets.first_line_synchronization.get():
                if idx == 0:
                    continue
            if 'start' in row['Name']:
                sample_number += 1
            x_start = row['X(um)']/1000
            y_start = row['Y(um)']/1000
            width = (logfile.loc[idx + 1, 'X(um)'] - row['X(um)'])/1000
            height = row['Spotsize']/1000

            self.polygon_vertices_list_start.append([x_start, y_start])
            self.polygon_vertices_list_end.append([x_start + width, y_start + height])

            if idx == 0:
                xmin = x_start
                xmax = x_start + width
                ymin = y_start
                ymax = y_start + height
            if self.gui.widgets.first_line_synchronization.get():
                if idx == 2:
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
            if 'end' in row['Name']:
                self.polygon_vertices_list_end.reverse()
                self.polygon_vertices_list_complete = self.polygon_vertices_list_start + self.polygon_vertices_list_end
                self.polygon_dictionary[f'{sample_number}'] = self.polygon_vertices_list_complete
                self.polygon_vertices_list_start = []
                self.polygon_vertices_list_end = []

        return xmin, xmax, ymin, ymax

    def build_polygons(self, number, polygon_vertices):
        polygon_patch = patches.Polygon(polygon_vertices, closed=True, color="red",
                                        fill=False)
        self.ax.add_patch(polygon_patch)

        centroid_x = sum(p[0] for p in polygon_vertices) / len(polygon_vertices)
        centroid_y = sum(p[1] for p in polygon_vertices) / len(polygon_vertices)

        self.ax.text(centroid_x, centroid_y, number, ha='center', va='center', fontsize=20, color='black')

    def on_hover(self, event):
        for name, rectangle in self.rectangles_dictionary.items():
            if rectangle.contains(event)[0]:
                self.label.config(text=name)
                return
        self.label.config(text="")

    def divide_samples(self, logfile, sample_overview=False, multiple_samples_query=False):
        sample_overview_dictionary = {}
        sample_number = 1
        sample_new = True
        list_of_sample_idx = []
        list_of_sample_names = []
        list_of_sample_x_starts = []
        list_of_sample_x_ends = []
        list_of_sample_y_bottoms = []
        list_of_sample_spotsizes = []
        for idx, row in logfile.iloc[::2].iterrows():
            if self.gui.widgets.first_line_synchronization.get():
                if idx == 0:
                    continue

            x_start = row['X(um)'] / 1000
            y_bottom = row['Y(um)'] / 1000
            width = (logfile.loc[idx + 1, 'X(um)'] - row['X(um)']) / 1000
            spotsize = row['Spotsize'] / 1000
            x_end = x_start + width
            name = row['Name']

            if idx == 0 or sample_new is True:
                list_of_sample_idx.append(idx)
                list_of_sample_names.append(name)
                list_of_sample_x_starts.append(x_start)
                list_of_sample_x_ends.append(x_end)
                list_of_sample_y_bottoms.append(y_bottom)
                list_of_sample_spotsizes.append(spotsize)
                sample_new = False
            else:
                if spotsize not in list_of_sample_spotsizes:
                    logfile.loc[list_of_sample_idx[0], 'Name'] = f'{logfile.loc[list_of_sample_idx[0], "Name"]} (start)'
                    logfile.loc[list_of_sample_idx[-1], 'Name'] = f'{logfile.loc[list_of_sample_idx[-1], "Name"]} (end)'
                    sample_overview_dictionary[f'Sample {sample_number}'] = {}
                    sample_overview_dictionary[f'Sample {sample_number}']['Start_Name'] = list_of_sample_names[0]
                    sample_overview_dictionary[f'Sample {sample_number}']['End_Name'] = list_of_sample_names[-1]
                    sample_overview_dictionary[f'Sample {sample_number}']['idx_List'] = list_of_sample_idx
                    sample_overview_dictionary[f'Sample {sample_number}']['Names'] = list_of_sample_names
                    sample_number = sample_number + 1
                    sample_new = True
                    list_of_sample_idx = []
                    list_of_sample_names = []
                    list_of_sample_x_starts = []
                    list_of_sample_x_ends = []
                    list_of_sample_y_bottoms = []
                    list_of_sample_spotsizes = []
                    continue
                if float("{:.3f}".format(y_bottom - spotsize)) not in list_of_sample_y_bottoms:
                    logfile.loc[list_of_sample_idx[0], 'Name'] = f'{logfile.loc[list_of_sample_idx[0], "Name"]} (start)'
                    logfile.loc[list_of_sample_idx[-1], 'Name'] = f'{logfile.loc[list_of_sample_idx[-1], "Name"]} (end)'
                    sample_overview_dictionary[f'Sample {sample_number}'] = {}
                    sample_overview_dictionary[f'Sample {sample_number}']['Start_Name'] = list_of_sample_names[0]
                    sample_overview_dictionary[f'Sample {sample_number}']['End_Name'] = list_of_sample_names[-1]
                    sample_overview_dictionary[f'Sample {sample_number}']['idx_List'] = list_of_sample_idx
                    sample_overview_dictionary[f'Sample {sample_number}']['Names'] = list_of_sample_names
                    sample_number = sample_number + 1
                    sample_new = True
                    list_of_sample_idx = []
                    list_of_sample_names = []
                    list_of_sample_x_starts = []
                    list_of_sample_x_ends = []
                    list_of_sample_y_bottoms = []
                    list_of_sample_spotsizes = []
                    continue
                for x_start_legacy, x_end_legacy in zip(list_of_sample_x_starts, list_of_sample_x_ends):
                    # x_start is inside the legacy line and x_end is inside the legacy line
                    if x_start_legacy <= x_start and x_end <= x_end_legacy:
                        list_of_sample_idx.append(idx)
                        list_of_sample_names.append(name)
                        list_of_sample_x_starts.append(x_start)
                        list_of_sample_x_ends.append(x_end)
                        list_of_sample_y_bottoms.append(y_bottom)
                        list_of_sample_spotsizes.append(spotsize)
                        break
                    # x_start is to the left of the legacy line and x_end is inside the legacy line
                    elif x_end_legacy >= x_start <= x_start_legacy <= x_end <= x_end_legacy:
                        list_of_sample_idx.append(idx)
                        list_of_sample_names.append(name)
                        list_of_sample_x_starts.append(x_start)
                        list_of_sample_x_ends.append(x_end)
                        list_of_sample_y_bottoms.append(y_bottom)
                        list_of_sample_spotsizes.append(spotsize)
                        break
                    # x_start is inside the legacy line and x_end is to the right of the legacy line
                    elif x_start_legacy <= x_start <= x_end_legacy <= x_end >= x_start_legacy:
                        list_of_sample_idx.append(idx)
                        list_of_sample_names.append(name)
                        list_of_sample_x_starts.append(x_start)
                        list_of_sample_x_ends.append(x_end)
                        list_of_sample_y_bottoms.append(y_bottom)
                        list_of_sample_spotsizes.append(spotsize)
                        break
                    # x_start is to the left of the legacy line and x_end is to the right of the legacy line
                    elif x_start_legacy >= x_start <= x_end_legacy <= x_end >= x_start_legacy:
                        list_of_sample_idx.append(idx)
                        list_of_sample_names.append(name)
                        list_of_sample_x_starts.append(x_start)
                        list_of_sample_x_ends.append(x_end)
                        list_of_sample_y_bottoms.append(y_bottom)
                        list_of_sample_spotsizes.append(spotsize)
                        break
                    else:
                        logfile.loc[
                            list_of_sample_idx[0], 'Name'] = f'{logfile.loc[list_of_sample_idx[0], "Name"]} (start)'
                        logfile.loc[
                            list_of_sample_idx[-1], 'Name'] = f'{logfile.loc[list_of_sample_idx[-1], "Name"]} (end)'
                        sample_overview_dictionary[f'Sample {sample_number}'] = {}
                        sample_overview_dictionary[f'Sample {sample_number}']['Start_Name'] = list_of_sample_names[0]
                        sample_overview_dictionary[f'Sample {sample_number}']['End_Name'] = list_of_sample_names[-1]
                        sample_overview_dictionary[f'Sample {sample_number}']['idx_List'] = list_of_sample_idx
                        sample_overview_dictionary[f'Sample {sample_number}']['Names'] = list_of_sample_names
                        sample_number = sample_number + 1
                        sample_new = True
                        list_of_sample_idx = []
                        list_of_sample_names = []
                        list_of_sample_x_starts = []
                        list_of_sample_x_ends = []
                        list_of_sample_y_bottoms = []
                        list_of_sample_spotsizes = []
                        break
            if idx == len(logfile)-2:
                logfile.loc[list_of_sample_idx[0], 'Name'] = f'{logfile.loc[list_of_sample_idx[0], "Name"]} (start)'
                logfile.loc[list_of_sample_idx[-1], 'Name'] = f'{logfile.loc[list_of_sample_idx[-1], "Name"]} (end)'
                sample_overview_dictionary[f'Sample {sample_number}'] = {}
                sample_overview_dictionary[f'Sample {sample_number}']['Start_Name'] = list_of_sample_names[0]
                sample_overview_dictionary[f'Sample {sample_number}']['End_Name'] = list_of_sample_names[-1]
                sample_overview_dictionary[f'Sample {sample_number}']['idx_List'] = list_of_sample_idx
                sample_overview_dictionary[f'Sample {sample_number}']['Names'] = list_of_sample_names

        if sample_overview:
            return logfile, sample_overview_dictionary
        if multiple_samples_query:
            if len(sample_overview_dictionary) > 1:
                self.gui.multiple_samples_detected = True
                return
            else:
                self.gui.multiple_samples_detected = False
                return

        return logfile
