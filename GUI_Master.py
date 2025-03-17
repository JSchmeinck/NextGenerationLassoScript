import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import ExperimentClass
import GUI_Widgets
import Image_Synchronization
from tkinter import messagebox
import Importer
import Logfile_Viewer
import Windows_Notifications


class GUI:
    def __init__(self, master_window, main):
        # Setting up the main window
        self.master_window = master_window
        self.main=main
        self.master_window.title("LassoTool")
        self.master_window.geometry('900x600')
        self.master_window.resizable(width=False, height=False)

        self.importer = Importer.Importer(gui=self)
        self.logfile_viewer = Logfile_Viewer.LogfileViewer(gui=self, master_window=master_window)
        self.notifications = Windows_Notifications.Notifications(gui=self)

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
        self.data_is_background_corrected = False
        self.data_is_first_line_synchronized = False
        self.multiple_samples_detected = False
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
        self.update_status(reset=True)
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

        if self.widgets.data_type.get() == 'mzml':
            self.list_of_files = []
            self.filename_list = []

            file = tk.filedialog.askopenfilename(title='Choose your sample File',
                                                              filetypes=[('MZml', '*.mzml')])

            self.filename_list = [os.path.basename(file)]
            self.list_of_files = [file]


        for item in self.widgets.samples_treeview.get_children():
            self.widgets.samples_treeview.delete(item)

        # self.data_list_samples.delete(0, 'end')
        for i, k in enumerate(self.filename_list):
            self.widgets.samples_treeview.insert(parent='', index=i, text='', values=[str(k)])

        self.reset_progress()
        self.update_status(reset=True)

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
        if self.widgets.data_type.get() == 'mzml':
            self.widgets.import_samples_button.configure(text='Import Sample')
            self.widgets.separator_import.set(';')

    def change_of_synchronization_mode(self):
        if self.widgets.synchronization.get():
            self.widgets.move_up_button.configure(state='disabled')
            self.widgets.move_down_button.configure(state='disabled')
            self.widgets.button_synchronization.configure(state='active')
            self.widgets.checkbutton_multiple_samples.configure(state='active')
            self.widgets.checkbutton_first_line_synchronization.configure(state='active')
            if self.widgets.multiple_samples.get():
                self.widgets.view_logfile_button.configure(state='active')
            else:
                self.widgets.view_logfile_button.configure(state='disabled')
            if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
                self.widgets.separator_import.set(',')
        else:
            self.widgets.move_up_button.configure(state='active')
            self.widgets.move_down_button.configure(state='active')
            self.widgets.checkbutton_first_line_synchronization.configure(state='disabled')
            self.widgets.button_synchronization.configure(state='disabled')
            self.widgets.view_logfile_button.configure(state='disabled')
            self.widgets.checkbutton_multiple_samples.configure(state='disabled')

        self.update_status()

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

        multiple_samples = self.widgets.multiple_samples.get()

        sample_rawdata_dictionary = self.importer.import_sample_file(data_type=self.widgets.data_type.get(),
                                                                     synchronized=synchronized)

        logfile_dataframe = self.importer.import_laser_logfile(logfile=self.logfile_filepath,
                                                               laser_type=self.widgets.laser_type.get(),
                                                               iolite_file=synchronized,
                                                               rectangular_data_calculation=True)

        if multiple_samples and self.widgets.data_type.get() != 'mzml':
            logfile_dataframe = self.logfile_viewer.divide_samples(logfile=logfile_dataframe)

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
        logfile_dataframe = self.importer.import_laser_logfile(logfile=self.logfile_filepath,
                                                               laser_type='ImageBIO 266',
                                                               iolite_file=False,
                                                               rectangular_data_calculation=True)

        self.experiment = ExperimentClass.Experiment(gui=self,
                                                     raw_laser_logfile_dataframe=logfile_dataframe,
                                                     sample_rawdata_dictionary={},
                                                     data_type=self.widgets.data_type.get(),
                                                     logfile_filepath=self.logfile_filepath,
                                                     fill_value=None,
                                                     synchronized=False)

        self.experiment.build_laser_ablation_times()

    def update_status(self, reset=False):
        if reset:
            self.data_is_synchronized = False
            self.data_is_background_corrected = False
            self.data_is_first_line_synchronized = False
            self.multiple_samples_detected = False
            self.widgets.data_is_synchronized_checkbutton.grid_remove()
            self.widgets.first_line_for_synchronization_checkbutton.grid_remove()
            self.widgets.background_corrected_checkbutton.grid_remove()
            self.widgets.multiple_samples_detected_checkbutton.grid_remove()
        if self.widgets.multiple_samples.get():
            self.widgets.multiple_samples_detected_checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky='w')
            logfile_dataframe = self.importer.import_laser_logfile(logfile=self.logfile_filepath,
                                                                   laser_type=self.widgets.laser_type.get(),
                                                                   iolite_file=True,
                                                                   rectangular_data_calculation=True)
            if logfile_dataframe is False:
                self.widgets.multiple_samples_detected_checkbutton.grid_remove()
                self.widgets.multiple_samples.set(False)
                return
            if self.widgets.data_type.get() != 'mzml':
                self.logfile_viewer.divide_samples(logfile=logfile_dataframe, multiple_samples_query=True)
            self.widgets.multiple_samples_detected.set(self.multiple_samples_detected)
        if self.widgets.synchronization.get():
            self.widgets.data_is_synchronized_checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky='w')
            self.widgets.data_is_synchronized.set(self.data_is_synchronized)
            self.widgets.first_line_for_synchronization_checkbutton.grid(row=1, column=0, padx=5, pady=5, sticky='w')
            self.widgets.first_line_for_synchronization.set(self.data_is_first_line_synchronized)
            self.widgets.background_corrected_checkbutton.grid(row=2, column=0, padx=5, pady=5, sticky='w')
            self.widgets.background_corrected.set(self.data_is_background_corrected)
        if self.widgets.synchronization.get() is False:
            self.widgets.data_is_synchronized_checkbutton.grid_remove()
            self.widgets.first_line_for_synchronization_checkbutton.grid_remove()
            self.widgets.background_corrected_checkbutton.grid_remove()
            self.widgets.multiple_samples_detected_checkbutton.grid_remove()

    def synchronization_query(self):
        if self.data_is_synchronized and self.widgets.synchronization:
            synchronized = True
        elif self.data_is_synchronized and self.widgets.synchronization.get() is False:
            decider = self.notifications.notification_yesno(header='Synchronization Warning',
                                               body='Your data is successfully synchronised but you have not ticked '
                                                       'the Synchronize Checkbox. Do you want to continue '
                                                       'with the synchronized data?')
            synchronized = decider
        elif self.data_is_synchronized is False and self.widgets.synchronization.get():
            decider = self.notifications.notification_yesno(header='Synchronization Warning',
                                               body='Your data not synchronised but you have ticked '
                                                       'the Synchronize Checkbox. Do you want to continue '
                                                       'with the unsynchronized data?')
            synchronized = decider
        else:
            synchronized = False
        return synchronized

    def synchronize_data(self):
        self.logfile_viewer.show_logfile()
        state = self.synchronizer.synchronize_data(data_type=self.widgets.data_type.get(),
                                           import_separator=self.widgets.separator_import.get(),
                                           laser=self.widgets.laser_type.get())
        if state is False:
            return
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
        elif separator_list == 'Comma':
            separator = ','
        elif separator_list == 'Semicolon':
            separator = ';'
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
