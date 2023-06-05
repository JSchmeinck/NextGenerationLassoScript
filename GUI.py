import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import numpy as np
import os
import ExperimentClass


class GUI:
    def __init__(self, master_window):
        # Setting up the main window
        self.master_window = master_window
        self.master_window.title("Lasso Script")
        self.master_window.geometry('900x450')
        self.master_window.resizable(width=False, height=False)

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

        self.step_decider_frame = ttk.Frame(master=self.master_window,
                                            width=900,
                                            height=50)
        self.ablation_step_variable = tk.StringVar()
        self.pre_ablation_radiobutton = ttk.Radiobutton(master=self.master_window,
                                                        variable=self.ablation_step_variable,
                                                        value='Pre Ablation',
                                                        text='Pre Ablation',
                                                        command=self.change_ablation_step)
        self.post_ablation_radiobutton = ttk.Radiobutton(master=self.master_window,
                                                         variable=self.ablation_step_variable,
                                                         value='Post Ablation',
                                                         text='Post Ablation',
                                                         command=self.change_ablation_step)
        # Creating GUI-Widgets displayed in the main window
        self.import_logfile_button = ttk.Button(text='Import Logfile',
                                                command=self.import_logfile,
                                                width=28)
        self.logfile_treeview = ttk.Treeview(master=self.master_window,
                                             height=15, show='headings',
                                             columns='Logfile')
        self.logfile_treeview.heading(column='# 1',
                                      text='Logfile')
        self.import_samples_button = ttk.Button(master=self.master_window,
                                                text='Import Samples',
                                                command=self.import_samples,
                                                width=28)
        self.samples_treeview = ttk.Treeview(master=self.master_window,
                                             height=15,
                                             show='headings',
                                             columns='Samples')
        self.samples_treeview.column(column="# 1",
                                     anchor=tk.CENTER,
                                     stretch=tk.NO, width=250)
        self.samples_treeview.heading(column='# 1',
                                      text='Samples')
        self.go_button = ttk.Button(text='calculate rectangle rawdata file',
                                    command=self.build_experiment_objects,
                                    width=50)
        self.progressbar = ttk.Progressbar(master=self.master_window,
                                           mode='determinate',
                                           maximum=100,
                                           orient=tk.HORIZONTAL)
        self.move_up_button = ttk.Button(text="Move Up",
                                         command=lambda: self.moveup(),
                                         width=10)
        self.move_down_button = ttk.Button(text="Move Down",
                                           command=lambda: self.movedown(),
                                           width=10)
        self.separator_frame = ttk.Frame(self.master_window, width=300, height=150)
        self.separator_header_import = ttk.Label(self.separator_frame, text='separator import', borderwidth=5)
        self.separator_import = tk.StringVar(value=';')
        option_list = (';', ',')
        self.separator_menu_import = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_import,
                                                    *option_list)
        self.separator_header_export = ttk.Label(master=self.separator_frame,
                                                 text='separator export',
                                                 borderwidth=5)
        self.separator_export = tk.StringVar(value=';')
        self.separator_menu_export = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_export,
                                                    *option_list)
        self.header_instruments = ttk.Label(master=self.separator_frame,
                                            text='Chosen MS',
                                            borderwidth=5)
        self.data_type = tk.StringVar()
        self.data_type.set('iCap TQ (Daisy)')
        self.icap_tq_radiobutton = ttk.Radiobutton(master=self.separator_frame,
                                                   text='iCap TQ (Daisy)',
                                                   variable=self.data_type,
                                                   value='iCap TQ (Daisy)',
                                                   command=self.change_of_instrument,
                                                   width=30)
        self.agilent7900_radiobutton = ttk.Radiobutton(master=self.separator_frame,
                                                       text='Agilent 7900',
                                                       variable=self.data_type,
                                                       value='Agilent 7900',
                                                       command=self.change_of_instrument,
                                                       width=30)
        self.master_window.grid_columnconfigure(index=0, weight=1)
        self.master_window.grid_columnconfigure(index=1, weight=1)
        self.master_window.grid_columnconfigure(index=2, weight=1)

    def grid_gui_widgets(self):
        """
        Grids all Tk GUI widgets that have been defined during the innitiation of the the PostAblationGUI Class
        :return: None
        """
        self.import_logfile_button.grid(row=0, column=0, sticky='s', pady=5)
        self.logfile_treeview.column("# 1", anchor=tk.CENTER, stretch=tk.NO, width=250)
        self.logfile_treeview.grid(row=1, column=0, rowspan=2)
        self.import_samples_button.grid(row=0, column=1, sticky='s', pady=5)
        self.samples_treeview.grid(row=1, column=1, rowspan=2)
        self.go_button.grid(row=3, column=0, columnspan=2, sticky='n', pady=10)
        self.progressbar.grid(row=3, column=2)
        self.move_up_button.grid(row=1, column=2, sticky='nw', pady=10)
        self.move_down_button.grid(row=1, column=2, sticky='nw', pady=40)
        self.separator_frame.grid(row=2, column=2, sticky='w')
        self.separator_frame.grid_propagate(False)
        self.separator_header_import.grid(row=0, column=0, pady=(10, 0), sticky='we', padx=5)
        self.separator_menu_import.grid(row=1, column=0)
        self.separator_header_export.grid(row=2, column=0, sticky='nw', pady=(20, 0), padx=6)
        self.icap_tq_radiobutton.grid(row=1, column=1, padx=10)
        self.separator_header_export.grid(row=2, column=0, sticky='nw', pady=(20, 0), padx=6)
        self.separator_menu_export.grid(row=3, column=0)
        self.header_instruments.grid(row=0, column=1, sticky='nw', pady=(10, 0), padx=30)
        self.agilent7900_radiobutton.grid(row=2, column=1, sticky='w', padx=10)

    def import_logfile(self):
        """
        Opens the fileselection to select the logfile of the current experiment. Only one logfile can be imported for
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
        for item in self.logfile_treeview.get_children():
            self.logfile_treeview.delete(item)
        # The new logfile is added to the corresponding Treeview
        self.logfile_treeview.insert(parent='',
                                     index=0,
                                     text='',
                                     values=self.logfile_filename)
        return self.logfile_filepath

    def import_samples(self):

        if self.data_type.get() == 'iCap TQ (Daisy)':
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

        if self.data_type.get() == 'Agilent 7900':

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

        for item in self.samples_treeview.get_children():
            self.samples_treeview.delete(item)

        # self.data_list_samples.delete(0, 'end')
        for i, k in enumerate(self.filename_list):
            self.samples_treeview.insert(parent='', index=i, text='', values=[str(k)])

        self.export_path_list = []

        for file in self.list_of_files:
            pattern_csv_filename = os.path.basename(file)
            pattern_csv_filename_withoutcsv = pattern_csv_filename.replace('.csv', '')

            self.pattern_csv_filepath_without_filename = file.replace(pattern_csv_filename, '')

            export_name = self.pattern_csv_filepath_without_filename + 'lasso_rawdata_folder/' + \
                          pattern_csv_filename_withoutcsv + \
                          '_lasso_rawdata.csv'
            self.export_path_list.append(export_name)

    def change_ablation_step(self):
        pass

    def change_of_instrument(self):
        if self.data_type.get() == 'iCap TQ (Daisy)':
            self.import_samples_button.configure(text='Import Sample')
            self.separator_import.set(';')
            self.list_of_files = []
            self.filename_list = []
            self.export_path_list = []
            self.logfile_treeview.delete(*self.logfile_treeview.get_children())
            self.samples_treeview.delete(*self.samples_treeview.get_children())

        if self.data_type.get() == 'Agilent 7900':
            self.import_samples_button.configure(text='Import Sample Folder')
            self.separator_import.set(',')
            self.list_of_files = []
            self.filename_list = []
            self.export_path_list = []
            self.logfile_treeview.delete(*self.logfile_treeview.get_children())
            self.samples_treeview.delete(*self.samples_treeview.get_children())

    def moveup(self):
        leaves = self.samples_treeview.selection()
        for i in leaves:
            self.samples_treeview.move(i, self.samples_treeview.parent(i),
                                       self.samples_treeview.index(i) - 1)

        self.export_path_list = []

        for file in self.list_of_files:
            pattern_csv_filename = os.path.basename(file)
            pattern_csv_filename_withoutcsv = pattern_csv_filename.replace('.csv', '')

            self.pattern_csv_filepath_without_filename = file.replace(pattern_csv_filename, '')

            export_name = self.pattern_csv_filepath_without_filename + 'lasso_rawdata_folder/' + \
                          pattern_csv_filename_withoutcsv + \
                          '_lasso_rawdata.csv'
            self.export_path_list.append(export_name)

    def movedown(self):
        leaves = self.samples_treeview.selection()
        for i in reversed(leaves):
            self.samples_treeview.move(i, self.samples_treeview.parent(i),
                                       self.samples_treeview.index(i) + 1)

        self.export_path_list = []

        for file in self.list_of_files:
            pattern_csv_filename = os.path.basename(file)
            pattern_csv_filename_withoutcsv = pattern_csv_filename.replace('.csv', '')

            self.pattern_csv_filepath_without_filename = file.replace(pattern_csv_filename, '')

            export_name = self.pattern_csv_filepath_without_filename + 'lasso_rawdata_folder/' + \
                          pattern_csv_filename_withoutcsv + \
                          '_lasso_rawdata.csv'
            self.export_path_list.append(export_name)

    def build_experiment_objects(self):
        sample_rawdata_dictionary = {}
        if self.data_type.get() == 'iCap TQ (Daisy)':
            for n, m in enumerate(self.list_of_files):
                with open(m) as f:
                    # First 15 lines have to be skipped (in Qtegra files)
                    df = pd.read_csv(filepath_or_buffer=f,
                                     sep=self.separator_import.get())
                sample_rawdata_dictionary[f'{self.filename_list[n]}'] = df

        if self.data_type.get() == 'Agilent 7900':
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
                                             sep=self.separator_import.get(),
                                             skiprows=3,
                                             skipfooter=1,
                                             engine='python')
                        individual_lines_dictionary[f'Line_{ticker+1}'] = df
                sample_rawdata_dictionary[f'{self.filename_list[n]}'] = individual_lines_dictionary

        with open(self.logfile_filepath) as f:
            # pattern_dataframe = pd.read_csv(f, skipinitialspace=True).fillna('Faulty Line')
            logfile_dataframe = pd.read_csv(f, usecols=['Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                        'Grid Spacing(Î¼m)', 'X(um)', 'Y(um)'], index_col=False)

        self.experiment = ExperimentClass.Experiment(gui=self,
                                                     raw_laser_logfile_dataframe=logfile_dataframe,
                                                     sample_rawdata_dictionary=sample_rawdata_dictionary,
                                                     data_type=self.data_type.get())

        self.experiment.build_rectangular_data()

    def popup_error_message(self, title, message):
        popup_error = messagebox.showerror(title=title, message=message)

