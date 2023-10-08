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
        self.import_logfile_button = ttk.Button(text='Import Logfile',
                                                command=self.gui_master.import_logfile,
                                                width=28)
        self.logfile_treeview = CustomTreeview(master=self.master_window,
                                               height=20, show='headings',
                                               columns='Logfile')
        self.logfile_treeview.heading(column='# 1',
                                      text='Logfile')

        self.import_samples_button = ttk.Button(master=self.master_window,
                                                text='Import Samples',
                                                command=self.gui_master.import_samples,
                                                width=28)
        self.samples_treeview = CustomTreeview(master=self.master_window,
                                               height=20,
                                               show='headings',
                                               columns='Samples')
        self.samples_treeview.column(column="# 1",
                                     anchor=tk.CENTER,
                                     stretch=tk.NO, width=250)
        self.samples_treeview.heading(column='# 1',
                                      text='Samples')
        # The bottom line menu
        self.conversion_frame = ttk.Frame(master=self.master_window,
                                          width=800,
                                          height=70)
        self.export_path = tk.StringVar()
        self.directory_entry = ttk.Entry(master=self.conversion_frame,
                                         state='readonly',
                                         textvariable=self.export_path,
                                         width=40)
        self.browse_directory_button = ttk.Button(master=self.conversion_frame,
                                                  text='Browse',

                                                  command=self.gui_master.export_directory)
        self.go_button = ttk.Button(master=self.conversion_frame,
                                    text='Convert',
                                    command=self.gui_master.build_experiment_objects)
        self.build_laser_duration_button = ttk.Button(master=self.conversion_frame,
                                                      text='Build pattern duration',
                                                      command=self.gui_master.build_laserduration_sheet)
        self.progress = tk.IntVar()
        self.progressbar = ttk.Progressbar(master=self.master_window,
                                           mode='determinate',
                                           maximum=100,
                                           orient=tk.HORIZONTAL,
                                           length=544,
                                           variable=self.progress)
        self.move_up_button = ttk.Button(text="Move Up",
                                         command=lambda: self.gui_master.moveup(),
                                         width=15)
        self.move_down_button = ttk.Button(text="Move Down",
                                           command=lambda: self.gui_master.movedown(),
                                           width=15)
        # The separator menu
        self.separator_frame = ttk.Frame(master=self.master_window,
                                         width=110,
                                         height=170)
        self.separator_header_import = ttk.Label(master=self.separator_frame,
                                                 text='Delimiter import',
                                                 borderwidth=5)
        self.separator_import = tk.StringVar(value=';')
        option_list = (';', ',', 'Tab', 'Space')
        self.separator_menu_import = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_import,
                                                    *option_list)
        self.separator_header_export = ttk.Label(master=self.separator_frame,
                                                 text='Delimiter export',
                                                 borderwidth=5)
        self.separator_export = tk.StringVar(value=';')
        self.separator_menu_export = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_export,
                                                    *option_list)
        self.fill_value = tk.IntVar(value=0)
        self.fill_value_header = ttk.Label(master=self.separator_frame,
                                           text='fill_value',
                                           borderwidth=5)
        self.fill_value_entry = ttk.Entry(master=self.separator_frame,
                                          textvariable=self.fill_value,
                                          width=10)
        # The data type menu
        self.datatype_frame = ttk.Frame(master=self.master_window,
                                        width=100,
                                        height=100)
        self.header_instruments = ttk.Label(master=self.datatype_frame,
                                            text='Data Type',
                                            borderwidth=5)
        self.data_type = tk.StringVar()
        self.data_type.set('iCap TQ (Daisy)')
        self.icap_tq_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                   text='iCap TQ (Daisy)',
                                                   variable=self.data_type,
                                                   value='iCap TQ (Daisy)',
                                                   command=self.gui_master.change_of_instrument,
                                                   width=30)
        self.agilent7900_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='Agilent 7900',
                                                       variable=self.data_type,
                                                       value='Agilent 7900',
                                                       command=self.gui_master.change_of_instrument,
                                                       width=30,
                                                       state='disabled')
        self.eic_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='EIC',
                                                       variable=self.data_type,
                                                       value='EIC',
                                                       command=self.gui_master.change_of_instrument,
                                                       width=30)

        self.master_window.grid_columnconfigure(index=0, weight=1)
        self.master_window.grid_columnconfigure(index=1, weight=1)
        self.master_window.grid_columnconfigure(index=2, weight=1)

        # The laser type menu
        self.laser_frame = ttk.Frame(master=self.master_window,
                                               width=100,
                                               height=100)
        self.header_laser = ttk.Label(master=self.laser_frame,
                                                text='Laser Type',
                                                borderwidth=5)
        self.laser_type = tk.StringVar()
        self.laser_type.set('ImageBIO 266')
        self.imagebio_radiobutton = ttk.Radiobutton(master=self.laser_frame,
                                                   text='ImageBIO 266',
                                                   variable=self.laser_type,
                                                   value='ImageBIO 266',
                                                   width=30)
        self.cetac_g2plus_radiobutton = ttk.Radiobutton(master=self.laser_frame,
                                                       text='Cetac G2+',
                                                       variable=self.laser_type,
                                                       value='Cetac G2+',
                                                       width=30)

        #The Synchronization menu
        self.synchronization_frame = ttk.Frame(master=self.master_window,
                                               width=120,
                                               height=100)
        self.header_synchronization = ttk.Label(master=self.synchronization_frame,
                                                text='Data Synchronization',
                                                borderwidth=5)
        self.synchronization = tk.BooleanVar(value=False)
        self.checkbutton_synchronization = ttk.Checkbutton(master=self.synchronization_frame,
                                                           text='Synchronization',
                                                           onvalue=True,
                                                           offvalue=False,
                                                           variable=self.synchronization,
                                                           command=self.gui_master.change_of_synchronization_mode)
        self.button_synchronization = ttk.Button(master=self.synchronization_frame,
                                                 text='Synchronize',
                                                 command=self.gui_master.synchronize_data,
                                                 state='disabled')

    def grid_gui_widgets(self):
        """
        Grids all Tk GUI widgets that have been defined during the innitiation of the the PostAblationGUI Class
        :return: None
        """
        self.import_logfile_button.grid(row=0, column=0, sticky='s', pady=5)
        self.logfile_treeview.column("# 1", anchor=tk.CENTER, stretch=tk.NO, width=250)
        self.logfile_treeview.grid(row=1, column=0, rowspan=3)
        self.import_samples_button.grid(row=0, column=1, sticky='s', pady=5)
        self.samples_treeview.grid(row=1, column=1, rowspan=3)
        self.conversion_frame.grid(row=4, column=0, columnspan=2, sticky='n', pady=10)
        self.go_button.grid(row=0, column=2, padx=(20, 0))
        self.build_laser_duration_button.grid(row=0, column=3)
        self.directory_entry.grid(row=0, column=0)
        self.browse_directory_button.grid(row=0, column=1)
        self.progressbar.grid(row=5, column=0, columnspan=2, sticky='n')

        self.move_up_button.grid(row=1, column=2, sticky='nw', pady=10)
        self.move_down_button.grid(row=1, column=2, sticky='nw', pady=(40, 0))

        self.separator_frame.grid(row=1, column=2, sticky='w', pady=(70, 0))
        self.separator_frame.grid_propagate(False)
        self.separator_header_import.grid(row=0, column=0, pady=(10, 0))
        self.separator_header_export.grid(row=2, column=0, pady=(10, 0))
        self.separator_menu_import.grid(row=1, column=0, sticky='we')
        self.separator_menu_export.grid(row=3, column=0, sticky='we')

        self.fill_value_header.grid(row=4, column=0, pady=(10, 0))
        self.fill_value_entry.grid(row=5, column=0, sticky='we')

        self.datatype_frame.grid(row=2, column=2, sticky='w', pady=0)
        self.datatype_frame.grid_propagate(False)
        self.header_instruments.grid(row=0, column=1, sticky='new', pady=(10, 0))
        self.icap_tq_radiobutton.grid(row=1, column=1)
        self.agilent7900_radiobutton.grid(row=2, column=1, sticky='w')
        self.eic_radiobutton.grid(row=3, column=1, sticky='w')

        self.laser_frame.grid(row=2, column=2, sticky='w', padx=(120, 0))
        self.laser_frame.grid_propagate(False)
        self.header_laser.grid(row=0, column=0, sticky='nw', pady=(10, 0))
        self.imagebio_radiobutton.grid(row=1, column=0)
        self.cetac_g2plus_radiobutton.grid(row=2, column=0, sticky='w')

        self.synchronization_frame.grid(row=3, column=2, sticky='w', pady=0)
        self.synchronization_frame.grid_propagate(False)
        self.header_synchronization.grid(row=0, column=1, sticky='n', pady=(10, 0))
        self.checkbutton_synchronization.grid(row=1, column=1, sticky='w')
        self.button_synchronization.grid(row=2, column=1)
