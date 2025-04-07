from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import GUI_Master

import tkinter as tk
from tkinter import ttk


class CustomTreeview(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure the custom header style
        style = ttk.Style(self)
        style.configure("Custom.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Apply the custom style to the Treeview widget
        self["style"] = "Custom.Treeview"


class GUIWidgets:
    def __init__(self, gui_master: GUI_Master.GUI, master_window):
        self.gui_master = gui_master
        self.master_window = master_window

        # Creating GUI-Widgets displayed in the main window
        self.treeview_frame = ttk.Frame(master=self.master_window,
                                         width=540,
                                         height=370)
        self.import_logfile_button = ttk.Button(master=self.treeview_frame,
                                                text='Import Logfile',
                                                command=self.gui_master.import_logfile,
                                                width=40)
        self.logfile_treeview = CustomTreeview(master=self.treeview_frame,
                                               height=15, show='headings',
                                               columns='Logfile')
        self.logfile_treeview.heading(column='# 1',
                                      text='Logfile')

        self.import_samples_button = ttk.Button(master=self.treeview_frame,
                                                text='Import mzML',
                                                command=self.gui_master.import_samples,
                                                width=40)
        self.samples_treeview = CustomTreeview(master=self.treeview_frame,
                                               height=15,
                                               show='headings',
                                               columns='Samples')
        self.samples_treeview.column(column="# 1",
                                     anchor=tk.CENTER,
                                     stretch=tk.NO, width=250)
        self.samples_treeview.heading(column='# 1',
                                      text='Samples')
        # The bottom line menu
        self.conversion_frame = ttk.Frame(master=self.master_window,
                                          width=550,
                                          height=70)
        self.export_path = tk.StringVar()
        self.directory_entry = ttk.Entry(master=self.conversion_frame,
                                         state='readonly',
                                         textvariable=self.export_path,
                                         width=50)
        self.browse_directory_button = ttk.Button(master=self.conversion_frame,
                                                  text='Browse',

                                                  command=self.gui_master.export_directory)

        self.progress = tk.IntVar()
        self.progressbar = ttk.Progressbar(master=self.conversion_frame,
                                           mode='determinate',
                                           maximum=100,
                                           orient=tk.HORIZONTAL,
                                           length=500,
                                           variable=self.progress)


        # The data type menu
        self.datatype_frame = ttk.Frame(master=self.master_window,
                                        width=150,
                                        height=100,
                                        relief='groove')

        self.data_type = tk.StringVar()
        self.data_type.set('mzml')


        self.master_window.grid_columnconfigure(index=0, weight=1)
        self.master_window.grid_columnconfigure(index=1, weight=1)
        self.master_window.grid_columnconfigure(index=2, weight=1)

        # The laser type menu
        self.header_laser = ttk.Label(master=self.datatype_frame,
                                                text='Laser Type',
                                                borderwidth=5)
        self.laser_type = tk.StringVar()


        #The Synchronization menu
        self.synchronization_frame = ttk.Frame(master=self.master_window,
                                               width=150,
                                               height=110,
                                               relief='groove')
        self.header_synchronization = ttk.Label(master=self.synchronization_frame,
                                                text='Data Synchronization',
                                                borderwidth=5)
        self.synchronization = tk.BooleanVar(value=True)


        self.button_synchronization = ttk.Button(master=self.synchronization_frame,
                                                 text='Synchronize',
                                                 command=self.gui_master.synchronize_data,
                                                 state='active')

        self.ms2_imaging =  tk.BooleanVar(value=False)
        self.ms2_imaging_checkbutton = ttk.Checkbutton(master=self.master_window,
                                         text="MS2 Imaging",
                                                             onvalue=True,
                                                             offvalue=False,
                                                             variable=self.ms2_imaging,
                                         width=20)


    def grid_gui_widgets(self):
        """
        Grids all Tk GUI widgets that have been defined during the innitiation of the PostAblationGUI Class
        :return: None
        """


        self.build_import_ui()

        self.treeview_frame.grid(row=0, column=0, columnspan=1, rowspan=5, padx=(24, 0))
        self.treeview_frame.grid_propagate(False)
        self.import_logfile_button.grid(row=0, column=0, pady=5, padx=10)
        self.logfile_treeview.column("# 1", anchor=tk.CENTER, stretch=tk.NO, width=250)
        self.logfile_treeview.grid(row=1, column=0, rowspan=2, pady=5)
        self.import_samples_button.grid(row=0, column=1, pady=5, padx=10)
        self.samples_treeview.grid(row=1, column=1, rowspan=2, pady=5)

        self.datatype_frame.grid(row=0, column=1, pady=(50,0), rowspan=2, sticky='w')
        self.datatype_frame.grid_propagate(False)
        self.header_laser.grid(row=0, column=1, pady=(10, 0))

        self.synchronization_frame.grid(row=3, column=1, pady=(5, 0), sticky='w')
        self.synchronization_frame.grid_propagate(False)
        self.header_synchronization.grid(row=0, column=0, pady=(10, 0), padx=(5,0))
        self.button_synchronization.grid(row=2, column=0, pady=(10,0))

        self.ms2_imaging_checkbutton.grid(row=4, column=1, pady=(5, 0), sticky='w')

        self.conversion_frame.grid(row=7, column=0, pady=10, columnspan=1, padx=(24,0))
        self.conversion_frame.grid_propagate(False)
        self.directory_entry.grid(row=0, column=0, pady=(5, 0), columnspan=4, padx=(10, 0))
        self.browse_directory_button.grid(row=0, column=4, pady=(5, 0), sticky='w')
        self.progressbar.grid(row=5, column=0, columnspan=20, pady=(10, 0), padx=(10, 0))

    def build_import_ui(self):
        module_names = list(self.gui_master.modules.keys())
        if module_names:
            self.laser_type.set(module_names[0])

        row_id = 1
        for mod_name in self.gui_master.modules:
            ttk.Radiobutton(
                self.datatype_frame, text=mod_name, variable=self.laser_type, value=mod_name
            ).grid(row=row_id, column=1, padx=(10,0), sticky='w')

            row_id += 1
