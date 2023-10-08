import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import ExperimentClass
import GUI_Widgets
import Image_Synchronization
from tkinter import messagebox


class GUI:
    def __init__(self, master_window):
        # Setting up the main window
        self.master_window = master_window
        self.master_window.title("Lasso Script")
        self.master_window.geometry('900x550')
        self.master_window.resizable(width=False, height=False)

        self.widgets = GUI_Widgets.GUIWidgets(gui_master=self,
                                              master_window=master_window)

        # The experiment Class that will be created for the post ablation data recreation
        self.experiment = None

        # Introducing general Variables of the GUI object
        self.list_of_files = []
        self.filename_list = []
        self.idxs = None
        self.pattern_csv_filepath_without_filename = None
        self.export_path_list = None
        self.logfile_filename = None
        self.logfile_filepath = None

        self.synchronizer = Image_Synchronization.ImageSynchronizer(master_gui=self, master_window=self.master_window)
        self.data_is_synchronized = False

    def grid_gui_widgets(self):
        self.widgets.grid_gui_widgets()

    def import_logfile(self):
        """
        Opens the fileselection to select the one logfile of the current experiment. The selected logfile is inserted into
        the corresponding Treeview. Only one logfile can be imported for
        one Experiment
        :return: The directory which was chosen by the user to contain the logfile
        """
        # Open file explorer to choose one CSV file
        self.logfile_filepath: str = tk.filedialog.askopenfilename(title='Choose a logfile',
                                                                   filetypes=[('CSV', '*.csv')])
        # The file name is extracted from the directory
        self.logfile_filename: list = [os.path.basename(self.logfile_filepath)]
        # If a logfile has been selected previously, that logfile is being deleted.
        # Only one logfile can be selected per Experiment
        for item in self.widgets.logfile_treeview.get_children():
            self.widgets.logfile_treeview.delete(item)
        # The new logfile is added to the corresponding Treeview
        self.widgets.logfile_treeview.insert(parent='',
                                             index=0,
                                             text='',
                                             values=self.logfile_filename)
        self.reset_progress()
        self.data_is_synchronized = False
        return self.logfile_filepath

    def import_samples(self):
        """
        Opens the fileselection to select one or more sample folders/files of the current experiment. The selected
        folders/files is inserted into the corresponding Treeview. Resets the list of files and filenames and
        updates them with the new samples.
        """
        if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
            self.list_of_files = []
            self.filename_list = []

            samples_filepath = tk.filedialog.askopenfilenames(title='Choose your sample files',
                                                              filetypes=[('CSV', '*.csv')])

            for i in samples_filepath:
                filename = os.path.basename(i)
                if filename in self.filename_list:
                    continue
                else:
                    self.filename_list.append(filename)

            for i in samples_filepath:
                if i in self.list_of_files:
                    continue
                else:
                    self.list_of_files.append(i)

        if self.widgets.data_type.get() == 'Agilent 7900':

            self.list_of_files = []
            self.filename_list = []
            folder_filepath = tk.filedialog.askdirectory(title='Choose your sample folder')

            folders = [os.path.abspath(os.path.join(folder_filepath, f)) for f in os.listdir(folder_filepath) if
                       os.path.isdir(os.path.join(folder_filepath, f))]
            for folder in folders:
                foldername = os.path.basename(folder)
                if foldername in self.filename_list:
                    pass
                else:
                    self.filename_list.append(foldername)

                if folder in self.list_of_files:
                    pass
                else:
                    self.list_of_files.append(folder)

        if self.widgets.data_type.get() == 'EIC':
            self.list_of_files = []
            self.filename_list = []

            file = tk.filedialog.askopenfilename(title='Choose your sample File',
                                                              filetypes=[('CSV', '*.csv')])

            self.filename_list = [os.path.basename(file)]
            self.list_of_files = [file]


        for item in self.widgets.samples_treeview.get_children():
            self.widgets.samples_treeview.delete(item)

        # self.data_list_samples.delete(0, 'end')
        for i, k in enumerate(self.filename_list):
            self.widgets.samples_treeview.insert(parent='', index=i, text='', values=[str(k)])

        self.reset_progress()
        self.data_is_synchronized = False

    def change_of_instrument(self):
        """
        When the user switches the data type of the mass spec, both treeviews are reset to show the
        user that there is no compatibility between these data types. The import separator is adjusted to reflect
        the most likely separator type of th current data type.
        """
        if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
            self.widgets.import_samples_button.configure(text='Import Sample')
            self.widgets.separator_import.set(';')

        if self.widgets.data_type.get() == 'Agilent 7900':
            self.widgets.import_samples_button.configure(text='Import Sample Folder')
            self.widgets.separator_import.set(',')
        if self.widgets.data_type.get() == 'EIC':
            self.widgets.import_samples_button.configure(text='Import Sample')
            self.widgets.separator_import.set(';')

    def change_of_synchronization_mode(self):
        if self.widgets.synchronization.get():
            self.widgets.button_synchronization.configure(state='active')
            if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
                self.widgets.separator_import.set(',')
        else:
            self.widgets.button_synchronization.configure(state='disabled')

    def moveup(self):
        """
        Updates the treeview and the file and filename lists to reflect the users intend to reorganize
        the sample input files before data conversion. This function moves one file one place up in the
        treeview and file lists as long as its not the first one already.
        """
        selection = self.widgets.samples_treeview.selection()
        if selection:
            selected_item = selection[0]
            index = self.widgets.samples_treeview.index(selected_item)
            if index > 0:
                self.widgets.samples_treeview.move(selected_item, '', index - 1)
                self.list_of_files[index], self.list_of_files[index - 1] = self.list_of_files[index - 1], \
                    self.list_of_files[index]
                self.filename_list[index], self.filename_list[index - 1] = self.filename_list[index - 1], \
                    self.filename_list[index]

    def movedown(self):
        """
        Updates the treeview and the file and filename lists to reflect the users intend to reorganize
        the sample input files before data conversion. This function moves one file one place down in the
        treeview and file lists as long as its not the last one already.
        """
        selection = self.widgets.samples_treeview.selection()
        if selection:
            selected_item = selection[0]
            index = self.widgets.samples_treeview.index(selected_item)
            if index < len(self.list_of_files) - 1:
                self.widgets.samples_treeview.move(selected_item, '', index + 2)
                self.list_of_files[index], self.list_of_files[index + 1] = self.list_of_files[index + 1], \
                    self.list_of_files[index]
                self.filename_list[index], self.filename_list[index + 1] = self.filename_list[index + 1], \
                    self.filename_list[index]

    def build_experiment_objects(self):
        """
        Collect the data from the logfile and samples files/folders and creates the managing experiment instance
        for the whole conversion.
        """
        self.reset_progress()

        synchronized = self.synchronization_query()

        sample_rawdata_dictionary: dict = {}
        if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
            for n, m in enumerate(self.list_of_files):
                if synchronized:
                    with open(m) as f:
                        # First 15 lines have to be skipped (in Qtegra files)
                        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                       sep=self.get_separator_import(),
                                                       skiprows=13)
                    sample_rawdata_dictionary[f'{self.filename_list[n]}'] = df
                    break
                else:
                    with open(m) as f:
                        # First 15 lines have to be skipped (in Qtegra files)
                        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                       sep=self.get_separator_import())
                    sample_rawdata_dictionary[f'{self.filename_list[n]}'] = df

        if self.widgets.data_type.get() == 'Agilent 7900':
            individual_lines_dictionary = {}
            # Loop through the imported directorys one by one
            for n, m in enumerate(self.list_of_files):
                directory = os.fsencode(m)
                # Loop trough the files inside the directory
                for ticker, file in enumerate(os.listdir(directory)):
                    filename = os.fsdecode(file)
                    # Only use the files that are csv data
                    if filename.endswith(".csv"):
                        with open(f'{m}/{filename}') as f:
                            df = pd.read_csv(filepath_or_buffer=f,
                                             sep=self.get_separator_import(),
                                             skiprows=3,
                                             skipfooter=1,
                                             engine='python')
                        individual_lines_dictionary[f'Line_{ticker + 1}'] = df
                sample_rawdata_dictionary[f'{self.filename_list[n]}'] = individual_lines_dictionary
        if self.widgets.data_type.get() == 'EIC':
            for n, m in enumerate(self.list_of_files):
                with open(m) as f:
                    df: pd.DataFrame = pd.read_csv(f, sep=self.get_separator_import(), skiprows=2, engine='python')
                df.drop(columns=[df.columns[-1]], inplace=True)
                sample_rawdata_dictionary[f'{self.filename_list[n]}'] = df


        if self.widgets.laser_type.get() == 'Cetac G2+':
            with open(self.logfile_filepath) as file:
                iolite_dataframe = pd.read_csv(file, skiprows=1, header=None)
            iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number', 'Comment',
                                         'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)', 'Scan Velocity (um/s)',
                                         'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)',
                                         'Spot Type', 'Spot Size', 'Spot Angle', 'MFC1', 'MFC2']
            logfile_dictionary = {}

            scan_speed_array = iolite_dataframe['Scan Velocity (um/s)'].dropna().values
            scan_speed_array[1::2] = np.nan

            pattern_number_array = iolite_dataframe['Sequence Number'].dropna().values
            pattern_number_array = pattern_number_array.repeat(2)
            run_queue_order_array = pattern_number_array.copy()
            pattern_number_array[1::2] = np.nan

            run_queue_order_array = run_queue_order_array-1
            run_queue_order_array[1::2] = np.nan

            name_array = iolite_dataframe['Comment'].dropna().values
            name_array = name_array.repeat(2)
            name_array[1::2] = np.nan

            type_array = iolite_dataframe['Spot Type'].to_numpy()
            type_array = type_array[:, 0]
            type_array = type_array[0::7]
            type_array = type_array.repeat(2)
            type_array[1::2] = np.nan

            x_array = iolite_dataframe['Intended X(um)'].dropna().values
            y_array = iolite_dataframe['Intended Y(um)'].dropna().values

            logfile_dictionary['Pattern #'] = pattern_number_array
            logfile_dictionary['Name'] = name_array
            logfile_dictionary['Type'] = type_array
            logfile_dictionary['Run Queue Order'] = run_queue_order_array
            logfile_dictionary['Scan Speed(Î¼m/sec)'] = scan_speed_array
            logfile_dictionary['X(um)'] = x_array
            logfile_dictionary['Y(um)'] = y_array

            logfile_dataframe = pd.DataFrame(logfile_dictionary)

        if self.widgets.laser_type.get() == 'ImageBIO 266':
            if synchronized:
                with open(self.logfile_filepath) as file:
                    iolite_dataframe = pd.read_csv(file, skiprows=1, header=None)
                iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                             'Comment',
                                             'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                             'Scan Velocity (um/s)',
                                             'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)']

                logfile_dictionary = {}

                scan_speed_array = iolite_dataframe['Scan Velocity (um/s)'].dropna().values
                scan_speed_array[1::2] = np.nan

                pattern_number_array = iolite_dataframe['Sequence Number'].dropna().values
                pattern_number_array = pattern_number_array.repeat(2)
                run_queue_order_array = pattern_number_array.copy()
                pattern_number_array[1::2] = np.nan

                run_queue_order_array = run_queue_order_array - 1
                run_queue_order_array[1::2] = np.nan

                name_array = iolite_dataframe['Comment'].dropna().values
                name_array = name_array.repeat(2)
                name_array[1::2] = np.nan

                type_array = iolite_dataframe['Laser State'].to_numpy()
                type_array = type_array[0::6]
                type_array = type_array.repeat(2)
                type_array[1::2] = np.nan

                x_array = iolite_dataframe['Intended X(um)'].dropna().values
                y_array = iolite_dataframe['Intended Y(um)'].dropna().values

                logfile_dictionary['Pattern #'] = pattern_number_array
                logfile_dictionary['Name'] = name_array
                logfile_dictionary['Type'] = type_array
                logfile_dictionary['Run Queue Order'] = run_queue_order_array
                logfile_dictionary['Scan Speed(Î¼m/sec)'] = scan_speed_array
                logfile_dictionary['X(um)'] = x_array
                logfile_dictionary['Y(um)'] = y_array

                logfile_dataframe = pd.DataFrame(logfile_dictionary)

            else:
                try:
                    with open(self.logfile_filepath) as f:
                        # pattern_dataframe = pd.read_csv(f, skipinitialspace=True).fillna('Faulty Line')

                        logfile_dataframe = pd.read_csv(f, usecols=['Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                                    'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                                    'Y(um)'], index_col=False)
                except:
                    with open(self.logfile_filepath) as f:
                        logfile_dataframe = pd.read_csv(f, usecols=['ï»¿Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                                    'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                                    'Y(um)'], index_col=False)

        self.experiment = ExperimentClass.Experiment(gui=self,
                                                     raw_laser_logfile_dataframe=logfile_dataframe,
                                                     sample_rawdata_dictionary=sample_rawdata_dictionary,
                                                     data_type=self.widgets.data_type.get(),
                                                     logfile_filepath=self.logfile_filepath,
                                                     fill_value=self.widgets.fill_value.get(),
                                                     synchronized=synchronized)

        self.experiment.build_rectangular_data()

    def build_laserduration_sheet(self):
        """
        Collect the data from the logfile and creates the managing experiment instance
        for the patter duration file.
        """
        self.reset_progress()
        try:
            with open(self.logfile_filepath) as f:
                # pattern_dataframe = pd.read_csv(f, skipinitialspace=True).fillna('Faulty Line')

                logfile_dataframe = pd.read_csv(f, usecols=['Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                            'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                            'Y(um)'], index_col=False)

        except:
            with open(self.logfile_filepath) as f:
                logfile_dataframe = pd.read_csv(f, usecols=['ï»¿Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                            'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                            'Y(um)'], index_col=False)

        self.experiment = ExperimentClass.Experiment(gui=self,
                                                     raw_laser_logfile_dataframe=logfile_dataframe,
                                                     sample_rawdata_dictionary={},
                                                     data_type=self.widgets.data_type.get(),
                                                     logfile_filepath=self.logfile_filepath,
                                                     fill_value=None,
                                                     synchronized=False)

        self.experiment.build_laser_ablation_times()

    def synchronization_query(self):
        if self.data_is_synchronized and self.widgets.synchronization:
            synchronized = True
        elif self.data_is_synchronized and self.widgets.synchronization.get() is False:
            popup_yes_no = messagebox.askyesno(title='Synchronization Warning',
                                               message='Your data is successfully synchronised but you have not ticked '
                                                       'the Synchronize Checkbox. Do you want to continue '
                                                       'with the synchronized data?')
            if popup_yes_no:
                synchronized = True
            else:
                synchronized = False
        elif self.data_is_synchronized is False and self.widgets.synchronization.get():
            popup_yes_no = messagebox.askyesno(title='Synchronization Warning',
                                               message='Your data not synchronised but you have ticked '
                                                       'the Synchronize Checkbox. Do you want to continue '
                                                       'with the unsynchronized data?')
            if popup_yes_no:
                synchronized = False
            else:
                synchronized = True
        else:
            synchronized = False
        return synchronized

    def synchronize_data(self):
        self.synchronizer.synchronize_data(data_type=self.widgets.data_type.get(),
                                           import_separator=self.widgets.separator_import.get(),
                                           laser=self.widgets.laser_type.get())
        self.synchronizer.toggle_window_visivility()

    def export_directory(self):
        """
        Update the path selected by the user and shown in the path entry field.
        """
        path = filedialog.askdirectory()
        self.widgets.export_path.set(path)
        self.widgets.directory_entry.delete(0, tk.END)
        self.widgets.directory_entry.insert(0, path)

    def get_separator_export(self):
        """
        Give the separator for the exported files chosen by the user to a requesting instance.
        """
        separator_list = self.widgets.separator_export.get()
        if separator_list == 'Tab':
            separator = '\t'
        elif separator_list == 'Space':
            separator = ' '
        else:
            separator = separator_list
        return separator

    def get_separator_import(self):
        """
        Give the separator for the exported files chosen by the user to a requesting instance.
        """
        separator_list = self.widgets.separator_import.get()
        if separator_list == 'Tab':
            separator = '\t'
        elif separator_list == 'Space':
            separator = ' '
        else:
            separator = separator_list
        return separator

    def get_export_path(self):
        """
        Give the export path chosen by the user to a requesting instance.
        """
        return self.widgets.export_path.get()

    def increase_progress(self, step):
        """
        Update the progress bar to increase the progress shown by a supplied step size
        """
        current_progress = self.widgets.progress.get()
        self.widgets.progress.set(current_progress + step)
        self.master_window.update_idletasks()

    def reset_progress(self):
        """
        Reset the progress bar to show no progress.
        """
        self.widgets.progress.set(0)
        self.master_window.update_idletasks()
