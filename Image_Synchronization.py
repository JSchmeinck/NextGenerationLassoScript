import os
import tkinter.filedialog


import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import numpy as np
from datetime import datetime
import keyboard
from tkinter import ttk


def mask_array(main_array, mask_array, on_value, timestamp_array):

    # Create a boolean mask where the mask_array has the value 'Off'
    mask = np.ma.masked_invalid(mask_array, copy=True)

    boolean_mask = np.ma.getmaskarray(mask)

    inverted_boolean_mask = np.invert(boolean_mask)
    # Use the boolean mask to update the main_array with the replacement_value
    masked_array = np.where(boolean_mask, 0, main_array)

    # Set the values in main_array to replacement_value where mask_array has the value 'On'
    masked_array[inverted_boolean_mask] = on_value

    reduced_on_array = masked_array[masked_array != 0]

    zeros_array = np.array([0, 0])

    extended_array = []
    for i, value in enumerate(reduced_on_array):
        extended_array.append(value)
        if i % 2 == 1:  # Check if it's the second value
            extended_array.extend(zeros_array)

    extended_array = np.insert(extended_array, 0, 0)

    extended_array = np.delete(extended_array, -1)


    time_objects = [datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f') for time_str in timestamp_array]

    # Calculate time differences in seconds.milliseconds
    start_time = time_objects[0]
    time_diffs = [(time - start_time).total_seconds() for time in time_objects]

    # Convert time differences to a new numpy array
    time_diff_array = np.array(time_diffs)

    masked_array_time = np.where(boolean_mask, -1, time_diff_array)

    reduced_time_array = masked_array_time[masked_array_time != -1]

    duplicated_time_array = reduced_time_array.repeat(2)

    return extended_array, inverted_boolean_mask, duplicated_time_array, reduced_time_array




class ImageSynchronizer:
    def __init__(self, master_gui, master_window):
        self.gui = master_gui
        self.master = master_window
        self.window = tk.Toplevel(master=master_window)
        self.window.title("Image Synchronization")
        self.window.geometry('750x600')
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.resizable(width=False, height=False)
        self.window.withdraw()

        self.fig = plt.figure(frameon=False)
        self.ax = self.fig.add_axes([0.08, 0.09, 0.9, 0.85])

        self.image_data = None
        self.image_time = None
        self.image_intensity = None
        self.laser_logfile = None
        self.laser_log_time = None
        self.shifted_laser_log_time = None
        self.clean_time_array = None
        self.clean_time_array_extended = None
        self.time_data_sample = None

        self.laser_log_status = None
        self.filename = None
        self.directory = None

        self.laser_start_times_pointers = []
        self.laser_stop_times_pointers = []

        self.plot_frame = ttk.Frame(master=self.window, width=700, height=500)
        self.plot_frame.grid_propagate(False)
        self.plot_frame.grid(row=0, column=0, padx=50, pady=20, sticky='nesw')

        self.peripheral_frame = ttk.Frame(master=self.window, width=1000, height=100)
        self.peripheral_frame.grid(row=1, column=0, padx=50)

        self.click_offset = 0
        self.offset_axis = 0
        self.laser_log_time_offset = 0
        self.laser_log_time_extension = 0
        self.logfile_mask = None
        self.samples = None
        self.sample_rawdata = None
        self.synchronized_data = None
        self.indices_dictionary = {}
        self.list_of_unique_masses_in_file = None
        self.data_type = None
        self.import_separator = None

        self.move_left_button = ttk.Button(master=self.peripheral_frame,
                                           text='Move Left',
                                           command=lambda: self.move_laser_log_time(direction='left'))
        self.move_left_button.grid(row=0, column=0, sticky='e')
        self.move_increment = tk.DoubleVar(value=1.0)
        self.move_increment_entry = ttk.Entry(master=self.peripheral_frame,
                                              textvariable=self.move_increment,
                                              width=10)
        self.move_increment_entry.grid(row=0, column=1)
        self.move_right_button = ttk.Button(master=self.peripheral_frame,
                                            text='Move Right',
                                            command=lambda: self.move_laser_log_time(direction='right'))
        self.move_right_button.grid(row=0, column=2)
        self.reset_button = ttk.Button(master=self.peripheral_frame,
                                       text='Reset Offset',
                                       command=self.reset_offset,
                                       width=17)
        self.reset_button.grid(row=0, column=3)
        self.current_offset_label = ttk.Label(master=self.peripheral_frame,
                                              text='Current Offset:')
        self.current_offset_label.grid(row=0, column=4, sticky='e')
        self.current_offset = tk.StringVar(value='0 s')
        self.current_offset_entry = ttk.Label(master=self.peripheral_frame,
                                              textvariable=self.current_offset,
                                              state=tk.DISABLED)
        self.current_offset_entry.grid(row=0, column=5, padx=20)

        self.accept_button = ttk.Button(master=self.peripheral_frame,
                                        text='Accept', command=self.accept)
        self.accept_button.grid(row=0, column=7)

        # Extension_GUI

        self.subtract_extension_button = ttk.Button(master=self.peripheral_frame,
                                           text='-',
                                           command=lambda: self.extend_laser_log_time(direction='left'),
                                           width=5)
        self.subtract_extension_button.grid(row=1, column=0, sticky='e')
        self.extension_increment = tk.DoubleVar(value=1.0)
        self.extension_increment_entry = ttk.Entry(master=self.peripheral_frame,
                                              textvariable=self.extension_increment,
                                                   width=10)
        self.extension_increment_entry.grid(row=1, column=1)
        self.add_extension_button = ttk.Button(master=self.peripheral_frame,
                                            text='+',
                                            command=lambda: self.extend_laser_log_time(direction='right'),
                                            width=5)
        self.add_extension_button.grid(row=1, column=2, sticky='w')
        self.reset_extension_button = ttk.Button(master=self.peripheral_frame,
                                       text='Reset Extension',
                                       command=self.reset_extension,
                                       width=17)
        self.reset_extension_button.grid(row=1, column=3)
        self.current_extension_label = ttk.Label(master=self.peripheral_frame,
                                              text='Current Extension:')
        self.current_extension_label.grid(row=1, column=4)
        self.current_extension = tk.StringVar(value='0 s')
        self.current_extension_entry = ttk.Label(master=self.peripheral_frame,
                                              textvariable=self.current_extension,
                                              state=tk.DISABLED)
        self.current_extension_entry.grid(row=1, column=5, padx=20)

        self.checkbutton_multiple_samples = ttk.Checkbutton(master=self.peripheral_frame,
                                                            text='Multiple Samples',
                                                            onvalue=True,
                                                            offvalue=False,
                                                            variable=self.gui.widgets.multiple_samples,
                                                            command=self.gui.change_of_synchronization_mode)
        self.checkbutton_multiple_samples.grid(row=2, column=0, padx=20, columnspan=2)

        self.laser_log_plot = None
        self.raw_data_plot = None
        self.canvas = None
        self.dragging_line = False  # Flag to indicate dragging state
        self.dragging_xaxis = False

        self.multi_import = False

        self.sample_data_dictionary = {}

    def on_closing(self):
        self.window.withdraw()

    def set_laser_logfile(self, logfile):
        self.laser_logfile = logfile

    def set_image_data(self, image_data):
        self.image_data = image_data

    def plot_laser_log_and_image_data(self, time, intensity):
        self.clean_time_array_extended = self.clean_time_array.copy()

        if self.multi_import is False:
            self.laser_log_plot = self.ax.plot(self.laser_log_time, self.laser_log_status, 'g', picker=5)
            self.raw_data_plot = self.ax.plot(time, intensity, 'b-', picker=5)
            self.ax.set_xlabel('Time / s')
            self.ax.set_ylabel('Intensity')
            self.ax.ticklabel_format(style='sci', scilimits=(0, 0))
            self.ax.set_title('Synchronization')

            self.fig.canvas.mpl_connect('axes_enter_event', self.on_axes_enter)
            self.fig.canvas.mpl_connect('axes_leave_event', self.on_axes_leave)
            self.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
            self.fig.canvas.mpl_connect('button_release_event', self.on_button_release)
            self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.fig.canvas.mpl_connect('button_release_event', self.on_release)
            self.fig.canvas.mpl_connect('scroll_event', self.zoom)

        else:
            self.laser_log_plot[0].set_data(self.laser_log_time, self.laser_log_status)
            self.raw_data_plot[0].set_data(time, intensity)
            self.ax.relim()
            self.ax.autoscale()


        # Create a canvas for Matplotlib figure
        if self.multi_import is False:
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()
            self.multi_import = True
        else:
            self.canvas.draw()

    def toggle_window_visivility(self):
        if self.window.winfo_viewable():
            self.window.withdraw()
        else:
            self.window.deiconify()

    def zoom(self, event):

        # get the current x and y limits
        cur_xlim = self.ax.get_xlim()
        # set the range
        cur_xrange = (cur_xlim[1] - cur_xlim[0]) * .5
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 0.3

            self.ax.set_xlim([cur_xlim[0] + cur_xrange * scale_factor, cur_xlim[1] - cur_xrange * scale_factor])

        elif event.button == 'down':
            # deal with zoom out
            scale_factor = 0.3
            self.ax.set_xlim([cur_xlim[0] - cur_xrange * scale_factor,
                                  cur_xlim[1] + cur_xrange * scale_factor])
        else:
            # deal with something that should never happen
            return
        self.ax.figure.canvas.draw_idle()
        self.window.update()
            # set new limits

    def on_button_press(self, event):
        if event.button == 1:
            if event.inaxes is not None and event.inaxes == self.ax:
                # Check if the click is on the x-axis
                self.dragging_xaxis = True
                self.offset_axis = event.xdata
            if event.button == 1:
                # Check if the click is on the line
                self.dragging_line = True
                self.click_offset = event.xdata

    def on_button_release(self, event):
        if event.button == 1:
            self.dragging_line = False
            self.dragging_xaxis = False

    def on_axes_enter(self, event):
        if event.inaxes is not None and event.inaxes == self.ax and self.dragging_xaxis:
            self.dragging_xaxis = True

    def on_axes_leave(self, event):
        self.dragging_xaxis = False

    def on_motion(self, event):

        if self.dragging_line and keyboard.is_pressed("shift"):
            if event.xdata is not None and self.click_offset is not None:
                # Calculate the distance dragged
                current_x = event.xdata

                # Calculate the distance dragged
                delta_x = current_x - self.click_offset

                # Update the line data by shifting it in the x-direction
                self.laser_log_plot[0].set_xdata(self.laser_log_plot[0].get_xdata() + delta_x)

                # Update the offset for the next motion event
                self.click_offset = current_x

                new_x_data = self.laser_log_plot[0].get_xdata()
                self.laser_log_time_offset = self.laser_log_time[0] - new_x_data[0]
                self.current_offset.set(f'{-round(self.laser_log_time_offset, 2)} s')

        elif self.dragging_xaxis:
            if event.xdata is not None and self.offset_axis is not None:

                cur_xlim = self.ax.get_xlim()
                # Calculate the distance dragged
                delta_x = event.xdata - self.offset_axis

                # Update the x-axis limits
                new_x_limits = [cur_xlim[0] - delta_x, cur_xlim[1] - delta_x]
                self.ax.set_xlim(new_x_limits)
                # Redraw the canvas
        self.fig.canvas.draw()

    def on_release(self, event):

        # Disable dragging state
        self.dragging_line = False
        self.dragging_xaxis = False

    def reset_offset(self):
        self.laser_log_plot[0].set_xdata(self.laser_log_time)
        self.click_offset = 0
        self.current_offset.set(f'{self.click_offset} s')
        self.shifted_laser_log_time = self.laser_log_time
        self.canvas.draw()

    def reset_extension(self):

        self.laser_log_time_extension = 0

        self.clean_time_array_extended = self.clean_time_array.copy()

        duplicated_time_array = self.clean_time_array.repeat(2)
        duplicated_time_array = np.insert(duplicated_time_array, 0, 0)

        self.laser_log_plot[0].set_xdata(duplicated_time_array)

        self.current_extension.set(f'{self.laser_log_time_extension} s')

        self.canvas.draw()
    def move_laser_log_time(self, direction):

        increment = self.move_increment.get()

        old_x = self.laser_log_plot[0].get_xdata()

        if direction == 'left':
            new_x = np.array([x - increment for x in old_x])
            self.laser_log_plot[0].set_xdata(new_x)
            self.click_offset = self.click_offset - increment

        if direction == 'right':
            new_x = np.array([x + increment for x in old_x])
            self.laser_log_plot[0].set_xdata(new_x)
            self.click_offset = self.click_offset + increment

        self.laser_log_time_offset = self.laser_log_time[0] - new_x[0]
        self.current_offset.set(f'{-round(self.laser_log_time_offset, 2)} s')
        self.canvas.draw()

    def extend_laser_log_time(self, direction):

        is_sorted = lambda a: np.all(a[:-1] <= a[1:])

        if direction == 'left':
            self.laser_log_time_extension = self.laser_log_time_extension - self.extension_increment.get()

        if direction == 'right':
            self.laser_log_time_extension = self.laser_log_time_extension + self.extension_increment.get()

        self.clean_time_array_extended = self.clean_time_array.copy()
        self.clean_time_array_extended[0::2] = self.clean_time_array_extended[0::2] - self.laser_log_time_extension
        self.clean_time_array_extended[1::2] = self.clean_time_array_extended[1::2] + self.laser_log_time_extension

        if is_sorted(self.clean_time_array_extended):
            pass
        else:
            if direction == 'left':
                self.laser_log_time_extension = self.laser_log_time_extension + self.extension_increment.get()

            if direction == 'right':
                self.laser_log_time_extension = self.laser_log_time_extension - self.extension_increment.get()

            self.clean_time_array_extended = self.clean_time_array.copy()
            self.clean_time_array_extended[0::2] = self.clean_time_array_extended[0::2] - self.laser_log_time_extension
            self.clean_time_array_extended[1::2] = self.clean_time_array_extended[1::2] + self.laser_log_time_extension

        offset_time_array = self.clean_time_array_extended - self.laser_log_time_offset
        duplicated_time_array = offset_time_array.repeat(2)

        self.laser_log_plot[0].set_xdata(duplicated_time_array)

        self.current_extension.set(f'{self.laser_log_time_extension} s')

        self.canvas.draw()

    def accept(self):
        self.toggle_window_visivility()
        self.current_offset.set(f'0 s')

        if self.gui.widgets.multiple_samples.get():
            self.calculate_samples_multiple_samples()
        else:
            self.calculate_samples()

        self.gui.data_is_synchronized = True

    def calculate_samples(self):
        self.sample_data_dictionary = {}
        self.indices_dictionary = {}

        time_windows_arr = self.clean_time_array_extended - self.laser_log_time_offset
        df = self.sample_rawdata
        sample_names_arr = self.samples

        num_columns = df.shape[1]-1
        list_of_column_names = list(df.columns.values)

        max_length = max(len(time_windows_arr), len(sample_names_arr))

        # Pad the arrays with np.nan values to make them the same length
        time_windows_arr = np.pad(time_windows_arr, (0, max_length - len(time_windows_arr)), mode='constant',
                                  constant_values=np.nan)
        sample_names_arr = np.pad(sample_names_arr, (0, max_length - len(sample_names_arr)), mode='constant',
                                  constant_values='')

        # Create an empty dictionary to hold the data for each sample
        samples_data = {}

        # Create an empty list to hold the column names for each row
        column_names_list = []

        # Iterate through the time windows and sample names
        for i in range(0, len(time_windows_arr), 2):
            start_time = time_windows_arr[i]
            end_time = time_windows_arr[i + 1]
            sample_name = sample_names_arr[i // 2]

            # Filter the rows that fall within the current time window for the current sample
            mask = (df['Time'] >= start_time) & (df['Time'] <= end_time)
            sample_data = df[mask].drop(columns='Time')
            self.indices_dictionary[sample_name] = sample_data.index.tolist()
            # Store the filtered data as a new column in the dictionary
            samples_data[sample_name] = np.concatenate([sample_data[col].values for col in sample_data.columns])

            # Store the column names for each row
            column_names_list.extend(sample_data.columns)

        decider, length_of_arrays = self.check_array_length(samples_data)

        magic_number = num_columns
        if decider:
            final_step = length_of_arrays / magic_number
        else:
            largest_value = max(length_of_arrays)

            # Step 2: Iterate through the dictionary of numpy arrays
            for key, array in samples_data.items():
                # Step 3: Check if the length of the array matches the largest value
                if len(array) == largest_value:
                    final_step = len(array) / magic_number
                else:
                    # Calculate the integer and step as described in the question
                    integer = (largest_value - len(array)) / magic_number
                    step = len(array) / magic_number

                    nan_values = np.full((int(integer),), np.nan)

                    # Insert np.nan values at each step
                    for i in range(1, magic_number+1):
                        insert_index = (i * step) + ((i-1) * integer)
                        if insert_index == array.size:
                            array = np.concatenate((array, nan_values))
                        else:
                            array = np.insert(array, int(insert_index), nan_values)

                    # Update the dictionary with the modified array
                    samples_data[key] = array


        # Convert the dictionary to a new DataFrame
        result_df = pd.DataFrame(samples_data)

        if self.data_type == 'iCap TQ (Daisy)':
            self.list_of_unique_masses_in_file = list_of_column_names[1:]

        for k, i in enumerate(self.list_of_unique_masses_in_file):
            if k == 0:
                mass_name_array = np.full(shape=(int(final_step),), fill_value=i)
            else:
                filler = np.full(shape=(int(final_step),), fill_value=i)
                mass_name_array = np.concatenate((mass_name_array, filler))
        result_df.insert(0, 'Unnamed: 2', mass_name_array)

        self.sample_data_dictionary[self.gui.filename_list[0]] = result_df

    def calculate_samples_multiple_samples(self):
        self.sample_data_dictionary = {}
        indices_dictionary = {}


        logfile_dataframe = self.gui.importer.import_laser_logfile(logfile=self.gui.logfile_filepath,
                                                                   laser_type=self.gui.widgets.laser_type.get(),
                                                                   iolite_file=True,
                                                                   rectangular_data_calculation=True,
                                                                   logfile_viewer=True)
        logfile, sample_overview_dictionary = self.gui.logfile_viewer.divide_samples(logfile=logfile_dataframe,
                                                                            sample_overview=True)
        df = self.sample_rawdata
        for sample, infos in sample_overview_dictionary.items():
            indices_of_samples = np.array(infos['idx_List'])
            indices_of_samples = indices_of_samples.repeat(2)
            indices_of_samples[1::2] = indices_of_samples[1::2]+1

            sample_names_arr = infos['Names']

            num_columns = df.shape[1]-1
            list_of_column_names = list(df.columns.values)

            time_windows_arr = self.clean_time_array_extended - self.laser_log_time_offset
            time_windows_arr = time_windows_arr[indices_of_samples[0]:indices_of_samples[-1]+1]


            # Create an empty dictionary to hold the data for each sample
            samples_data = {}

            # Create an empty list to hold the column names for each row
            column_names_list = []

            # Iterate through the time windows and sample names
            for i in range(0, len(time_windows_arr), 2):
                start_time = time_windows_arr[i]
                end_time = time_windows_arr[i + 1]
                sample_name = sample_names_arr[i // 2]

                # Filter the rows that fall within the current time window for the current sample
                mask = (df['Time'] >= start_time) & (df['Time'] <= end_time)
                sample_data = df[mask].drop(columns='Time')
                indices_dictionary[sample_name] = sample_data.index.tolist()
                # Store the filtered data as a new column in the dictionary
                samples_data[sample_name] = np.concatenate([sample_data[col].values for col in sample_data.columns])

                # Store the column names for each row
                column_names_list.extend(sample_data.columns)

            decider, length_of_arrays = self.check_array_length(samples_data)

            magic_number = num_columns
            if decider:
                final_step = length_of_arrays / magic_number
            else:
                largest_value = max(length_of_arrays)

                # Step 2: Iterate through the dictionary of numpy arrays
                for key, array in samples_data.items():
                    # Step 3: Check if the length of the array matches the largest value
                    if len(array) == largest_value:
                        final_step = len(array) / magic_number
                    else:
                        # Calculate the integer and step as described in the question
                        integer = (largest_value - len(array)) / magic_number
                        step = len(array) / magic_number

                        nan_values = np.full((int(integer),), np.nan)

                        # Insert np.nan values at each step
                        for i in range(1, magic_number+1):
                            insert_index = (i * step) + ((i-1) * integer)
                            if insert_index == array.size:
                                array = np.concatenate((array, nan_values))
                            else:
                                array = np.insert(array, int(insert_index), nan_values)

                        # Update the dictionary with the modified array
                        samples_data[key] = array


            # Convert the dictionary to a new DataFrame
            result_df = pd.DataFrame(samples_data)

            if self.data_type == 'iCap TQ (Daisy)':
                self.list_of_unique_masses_in_file = list_of_column_names[1:]

            for k, i in enumerate(self.list_of_unique_masses_in_file):
                if k == 0:
                    mass_name_array = np.full(shape=(int(final_step),), fill_value=i)
                else:
                    filler = np.full(shape=(int(final_step),), fill_value=i)
                    mass_name_array = np.concatenate((mass_name_array, filler))
            result_df.insert(0, 'Unnamed: 2', mass_name_array)

            self.sample_data_dictionary[sample] = result_df

    def calculate_logfile_extension(self, log_data):
        part_one = [x - self.extension.get() for x in log_data[::2]]
        part_one = np.array(part_one)
        part_two = [x + self.extension.get() for x in log_data[1::2]]
        part_two = np.array(part_two)
        log_x_on_data = np.empty((part_one.size + part_two.size,), dtype=part_one.dtype)
        log_x_on_data[0::2] = part_one
        log_x_on_data[1::2] = part_two
        return log_x_on_data

    def check_array_length(self, data_dict):
        different_num_values = set()

        # Get the number of values for the first array to use it as the reference
        reference_num_values = data_dict[list(data_dict.keys())[0]].size
        different_num_values.add(reference_num_values)

        # Iterate through the dictionary items
        for key, arr in data_dict.items():
            # Get the number of values in the current array
            current_num_values = arr.size

            # Check if the number of values is different from the reference
            if current_num_values != reference_num_values:
                different_num_values.add(current_num_values)

        # Print the different number of values (if any)
        if different_num_values:
            return False, different_num_values
        else:
            return True, different_num_values

    def synchronize_data(self, data_type, import_separator, laser):

        self.directory = self.gui.list_of_files[0]
        self.filename = self.gui.filename_list[0]

        if data_type == 'iCap TQ (Daisy)':
            with open(self.directory) as file:
                rawdata_dataframe = pd.read_csv(file, skiprows=13)
            rawdata_dataframe_without_dwelltimes = rawdata_dataframe.drop(index=0)
            rawdata_dataframe_without_dwelltimes_and_lastrow = rawdata_dataframe_without_dwelltimes.drop(
                columns=rawdata_dataframe.columns[-1])
            rawdata_dataframe_without_dwelltime_and_time = rawdata_dataframe_without_dwelltimes_and_lastrow.drop(
                columns=rawdata_dataframe.columns[0])
            rawdata_dataframe_without_time = rawdata_dataframe_without_dwelltime_and_time.apply(pd.to_numeric)
            sum = rawdata_dataframe_without_time.sum(axis=1)
            rawdata_dataframe_without_time['TIC'] = sum
            sample_raw_data = rawdata_dataframe_without_dwelltimes_and_lastrow

            time_data_sample = rawdata_dataframe_without_dwelltimes['Time'].to_numpy()
            intensity_data_sample = rawdata_dataframe_without_time['TIC'].to_numpy()

        if data_type == 'EIC':
            column_names = []
            with open(self.directory) as f:
                df_info = pd.read_csv(f, sep=import_separator, skiprows=0, engine='python', nrows=2)
            header = df_info.columns
            for i in header:
                if 'Unnamed' in i:
                    continue
                else:
                    column_names.append(i)

            self.set_list_of_unique_masses_in_file(column_names[1:])

            with open(self.directory) as f:
                df = pd.read_csv(f, sep=import_separator, skiprows=2, engine='python', header=None)

            df.drop(columns=[df.columns[-1]], inplace=True)
            df.columns = column_names
            df.insert(0, 'Time', df['rt'] * 60)
            df = df.drop(columns=(['rt']))

            time_data_sample = df['Time'].to_numpy()

            eic_rawdata_dataframe_without_time = df.drop(
                columns=df.columns[0])
            eic_rawdata_dataframe_without_time = eic_rawdata_dataframe_without_time.apply(pd.to_numeric)
            sum = eic_rawdata_dataframe_without_time.sum(axis=1)
            eic_rawdata_dataframe_without_time['TIC'] = sum
            sample_raw_data = df
            intensity_data_sample = eic_rawdata_dataframe_without_time['TIC'].to_numpy()

        logfile = self.gui.logfile_filepath
        logfile_dataframe = self.gui.importer.import_laser_logfile(logfile=logfile,
                                                               laser_type=laser,
                                                               iolite_file=True,
                                                               rectangular_data_calculation=False)

        masked_array, inverted_mask, time_array, self.clean_time_array = mask_array(
            main_array=logfile_dataframe['Y(um)'].to_numpy(),
            mask_array=logfile_dataframe['Intended X(um)'].to_numpy(),
            on_value=(sum.max()) * 1.2,
            timestamp_array=logfile_dataframe['Timestamp'].to_numpy())


        self.import_separator = import_separator
        self.set_data_type(data_type)
        self.set_mask(inverted_mask)
        self.set_sample_array(logfile_dataframe['Comment'].dropna().to_numpy())
        self.set_sample_raw_data(sample_raw_data)

        self.laser_log_time = time_array
        self.laser_log_status = masked_array
        self.time_data_sample = time_data_sample
        self.plot_laser_log_and_image_data(time=time_data_sample,
                                           intensity=intensity_data_sample)

    def set_data_type(self, data_type):
        self.data_type = data_type

    def set_mask(self, mask):
        self.logfile_mask = mask

    def set_sample_array(self, sample_array):
        self.samples = sample_array

    def set_sample_raw_data(self, raw_data):
        self.sample_rawdata = raw_data

    def set_list_of_unique_masses_in_file(self, list):
        self.list_of_unique_masses_in_file = list

    def get_data(self, sample_name):
        if sample_name == 'Full Data':
            return self.sample_data_dictionary, self.list_of_unique_masses_in_file, self.time_data_sample
        else:
            return self.sample_data_dictionary[sample_name], self.list_of_unique_masses_in_file, self.time_data_sample
