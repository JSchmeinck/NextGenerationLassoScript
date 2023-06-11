import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import ExperimentClass
import GUI_Widgets


class GUI:
    def __init__(self, master_window):
        # Setting up the main window
        self.master_window = master_window
        self.master_window.title("Lasso Script")
        self.master_window.geometry('700x450')
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

        for item in self.widgets.samples_treeview.get_children():
            self.widgets.samples_treeview.delete(item)

        # self.data_list_samples.delete(0, 'end')
        for i, k in enumerate(self.filename_list):
            self.widgets.samples_treeview.insert(parent='', index=i, text='', values=[str(k)])

        self.reset_progress()

    def change_of_instrument(self):
        """
        When the user switches the data type of the mass spec, both treeviews are reset to show the
        user that there is no compatibility between these data types. The import separator is adjusted to reflect
        the most likely separator type of th current data type.
        """
        if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
            self.widgets.import_samples_button.configure(text='Import Sample')
            self.widgets.separator_import.set(';')
            self.list_of_files = []
            self.filename_list = []
            self.export_path_list = []
            self.widgets.logfile_treeview.delete(*self.widgets.logfile_treeview.get_children())
            self.widgets.samples_treeview.delete(*self.widgets.samples_treeview.get_children())

        if self.widgets.data_type.get() == 'Agilent 7900':
            self.widgets.import_samples_button.configure(text='Import Sample Folder')
            self.widgets.separator_import.set(',')
            self.list_of_files = []
            self.filename_list = []
            self.export_path_list = []
            self.widgets.logfile_treeview.delete(*self.widgets.logfile_treeview.get_children())
            self.widgets.samples_treeview.delete(*self.widgets.samples_treeview.get_children())

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
        sample_rawdata_dictionary: dict = {}
        if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
            for n, m in enumerate(self.list_of_files):
                with open(m) as f:
                    # First 15 lines have to be skipped (in Qtegra files)
                    df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                   sep=self.widgets.separator_import.get())
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
                                             sep=self.widgets.separator_import.get(),
                                             skiprows=3,
                                             skipfooter=1,
                                             engine='python')
                        individual_lines_dictionary[f'Line_{ticker + 1}'] = df
                sample_rawdata_dictionary[f'{self.filename_list[n]}'] = individual_lines_dictionary
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
                                                     logfile_filepath=self.logfile_filepath)

        self.experiment.build_rectangular_data()

    def build_laserduration_sheet(self):
        """
        Collect the data from the logfile and creates the managing experiment instance
        for the patter duration file.
        """
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
                                                     logfile_filepath=self.logfile_filepath)

        self.experiment.build_laser_ablation_times()

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
        return self.widgets.separator_export.get()

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
