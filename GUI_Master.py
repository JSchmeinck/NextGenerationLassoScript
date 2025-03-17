import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
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
        self.master_window.geometry('800x500')
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

    def synchronize_data(self):
        self.logfile_viewer.show_logfile()
        state = self.synchronizer.synchronize_data(data_type=self.widgets.data_type.get(),
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

        self.widgets.progress.set(step)
        self.master_window.update_idletasks()

    def reset_progress(self):
        """
        Reset the progress bar to show no progress.
        """
        self.widgets.progress.set(0)
        self.master_window.update_idletasks()
