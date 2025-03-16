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
                                                text='Import Sample',
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
                                          width=820,
                                          height=70)
        self.export_path = tk.StringVar()
        self.directory_entry = ttk.Entry(master=self.conversion_frame,
                                         state='readonly',
                                         textvariable=self.export_path,
                                         width=50)
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
        self.progressbar = ttk.Progressbar(master=self.conversion_frame,
                                           mode='determinate',
                                           maximum=100,
                                           orient=tk.HORIZONTAL,
                                           length=810,
                                           variable=self.progress)

        # The Move Sample Menu
        self.move_frame = ttk.Frame(master=self.master_window,
                                         width=110,
                                         height=80)
        self.move_up_button = ttk.Button(master=self.move_frame,
                                         text="Move Up",
                                         command=lambda: self.gui_master.moveup(),
                                         width=15)
        self.move_down_button = ttk.Button(master=self.move_frame,
                                           text="Move Down",
                                           command=lambda: self.gui_master.movedown(),
                                           width=15)
        # The separator menu
        self.separator_frame = ttk.Frame(master=self.master_window,
                                         width=110,
                                         height=170,
                                         relief='groove')
        self.separator_header_import = ttk.Label(master=self.separator_frame,
                                                 text='Delimiter import')
        self.separator_import = tk.StringVar(value=';')
        option_list = ('Semicolon', 'Comma', 'Tab', 'Space')
        self.separator_menu_import = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_import,
                                                    *option_list)
        self.separator_header_export = ttk.Label(master=self.separator_frame,
                                                 text='Delimiter export')
        self.separator_export = tk.StringVar(value='Semicolon')
        self.separator_menu_export = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_export,
                                                    *option_list)
        self.fill_value = tk.IntVar(value=0)
        self.fill_value_header = ttk.Label(master=self.separator_frame,
                                           text='Fill Value',
                                           borderwidth=5)
        self.fill_value_entry = ttk.Entry(master=self.separator_frame,
                                          textvariable=self.fill_value,
                                          width=10)
        # The data type menu
        self.datatype_frame = ttk.Frame(master=self.master_window,
                                        width=240,
                                        height=100,
                                        relief='groove')
        self.header_instruments = ttk.Label(master=self.datatype_frame,
                                            text='Data Type',
                                            borderwidth=5)
        self.data_type = tk.StringVar()
        self.data_type.set('iCap TQ (Daisy)')
        self.icap_tq_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                   text='iCap TQ (Daisy)',
                                                   variable=self.data_type,
                                                   value='iCap TQ (Daisy)',
                                                   command=self.gui_master.change_of_instrument)
        self.agilent7900_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='Agilent 7900',
                                                       variable=self.data_type,
                                                       value='Agilent 7900',
                                                       command=self.gui_master.change_of_instrument)
        self.eic_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='EIC',
                                                       variable=self.data_type,
                                                       value='EIC',
                                                       command=self.gui_master.change_of_instrument)
        self.mzml_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='mzml',
                                                       variable=self.data_type,
                                                       value='mzml',
                                                       command=self.gui_master.change_of_instrument)

        self.master_window.grid_columnconfigure(index=0, weight=1)
        self.master_window.grid_columnconfigure(index=1, weight=1)
        self.master_window.grid_columnconfigure(index=2, weight=1)

        # The laser type menu
        self.header_laser = ttk.Label(master=self.datatype_frame,
                                                text='Laser Type',
                                                borderwidth=5)
        self.laser_type = tk.StringVar()
        self.laser_type.set('ImageBIO 266')
        self.imagebio_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                   text='ImageBIO 266',
                                                   variable=self.laser_type,
                                                   value='ImageBIO 266')
        self.cetac_g2plus_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='Cetac G2+',
                                                       variable=self.laser_type,
                                                       value='Cetac G2+')

        #The Synchronization menu
        self.full_synchronization_frame = ttk.Frame(master=self.master_window,
                                               width=820,
                                               height=120)
        self.synchronization_frame = ttk.Frame(master=self.full_synchronization_frame,
                                               width=240,
                                               height=110,
                                               relief='groove')
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
        self.multiple_samples = tk.BooleanVar(value=False)
        self.checkbutton_multiple_samples = ttk.Checkbutton(master=self.synchronization_frame,
                                                           text='Multiple Samples',
                                                           onvalue=True,
                                                           offvalue=False,
                                                           variable=self.multiple_samples,
                                                           command=self.gui_master.change_of_synchronization_mode,
                                                            state='disabled')
        self.button_synchronization = ttk.Button(master=self.synchronization_frame,
                                                 text='Synchronize',
                                                 command=self.gui_master.synchronize_data,
                                                 state='disabled')
        self.view_logfile_button = ttk.Button(master=self.synchronization_frame,
                                                 text='View Logfile',
                                                 command=self.gui_master.logfile_viewer.show_logfile,
                                                 state='disabled')
        self.first_line_synchronization = tk.BooleanVar(value=False)
        self.checkbutton_first_line_synchronization = ttk.Checkbutton(master=self.synchronization_frame,
                                                                      text='Use first Line for Synchronization',
                                                                      onvalue=True,
                                                                      offvalue=False,
                                                                      variable=self.first_line_synchronization,
                                                                      command=self.gui_master.change_of_synchronization_mode,
                                                                      state='disabled')

        self.data_status_frame = ttk.Frame(master=self.full_synchronization_frame,
                                          width=525,
                                          height=100)
        self.logfile_status_frame = ttk.Frame(master=self.data_status_frame,
                                           width=253,
                                           height=100,
                                           relief='groove')
        self.multiple_samples_detected = tk.BooleanVar(value=False)
        self.multiple_samples_detected_checkbutton = ttk.Checkbutton(master=self.logfile_status_frame,
                                                                     text='Multiple Samples Found',
                                                                     variable=self.multiple_samples_detected,
                                                                     state='disabled',
                                                                     onvalue=True,
                                                                     offvalue=False)
        self.sample_status_frame = ttk.Frame(master=self.data_status_frame,
                                              width=254,
                                              height=100,
                                              relief='groove')
        self.data_is_synchronized = tk.BooleanVar(value=False)
        self.data_is_synchronized_checkbutton = ttk.Checkbutton(master=self.sample_status_frame,
                                                                text='Data is Synchronized',
                                                                variable=self.data_is_synchronized,
                                                                state='disabled',
                                                                onvalue=True,
                                                                offvalue=False)
        self.first_line_for_synchronization = tk.BooleanVar(value=False)
        self.first_line_for_synchronization_checkbutton = ttk.Checkbutton(master=self.sample_status_frame,
                                                                          text='First Line Used for Synchronization',
                                                                          variable=self.first_line_for_synchronization,
                                                                          state='disabled',
                                                                          onvalue=True,
                                                                          offvalue=False)
        self.background_corrected = tk.BooleanVar(value=False)
        self.background_corrected_checkbutton = ttk.Checkbutton(master=self.sample_status_frame,
                                                                text='Data is Background Corrected',
                                                                variable=self.background_corrected,
                                                                state='disabled',
                                                                onvalue=True,
                                                                offvalue=False)

    def grid_gui_widgets(self):
        """
        Grids all Tk GUI widgets that have been defined during the innitiation of the PostAblationGUI Class
        :return: None
        """

        self.treeview_frame.grid(row=0, column=0, columnspan=1, rowspan=5, sticky='w', padx=(24, 0))
        self.treeview_frame.grid_propagate(False)
        self.import_logfile_button.grid(row=0, column=0, pady=5, padx=10)
        self.logfile_treeview.column("# 1", anchor=tk.CENTER, stretch=tk.NO, width=250)
        self.logfile_treeview.grid(row=1, column=0, rowspan=2, pady=5)
        self.import_samples_button.grid(row=0, column=1, pady=5, padx=10)
        self.samples_treeview.grid(row=1, column=1, rowspan=2, pady=5)



        self.move_frame.grid(row=0, column=1, sticky='nw')
        self.move_frame.grid_propagate(False)
        self.move_up_button.grid(row=0, column=0, pady=(5, 0), padx=5)
        self.move_down_button.grid(row=1, column=0, pady=10, padx=5)

        self.separator_frame.grid(row=1, column=1, rowspan=3, sticky='w')
        self.separator_frame.grid_propagate(False)
        self.separator_header_import.grid(row=0, column=0, pady=(10, 0), padx=(10, 0))
        self.separator_header_export.grid(row=2, column=0, pady=(10, 0), padx=(10, 0))
        self.separator_menu_import.grid(row=1, column=0, sticky='we', padx=(10, 0))
        self.separator_menu_export.grid(row=3, column=0, sticky='we', padx=(10, 0))
        self.fill_value_header.grid(row=4, column=0, pady=(10, 0), padx=(10, 0))
        self.fill_value_entry.grid(row=5, column=0, sticky='we', padx=(10, 0))

        self.datatype_frame.grid(row=4, column=1, pady=(10,0), rowspan=2, sticky='w')
        self.datatype_frame.grid_propagate(False)
        self.header_instruments.grid(row=0, column=0, pady=(5, 0))
        self.icap_tq_radiobutton.grid(row=1, column=0, padx=(5,0))
        self.agilent7900_radiobutton.grid(row=2, column=0, sticky='w', padx=(5,0))
        self.eic_radiobutton.grid(row=3, column=0, sticky='w', padx=(5,0))
        self.mzml_radiobutton.grid(row=4, column=0, sticky='w', padx=(5, 0))
        self.header_laser.grid(row=0, column=1, pady=(10, 0))
        self.imagebio_radiobutton.grid(row=1, column=1, padx=(10,0))
        self.cetac_g2plus_radiobutton.grid(row=2, column=1, sticky='w', padx=(10,0))

        self.full_synchronization_frame.grid(row=6, column=0, pady=(10,0), columnspan=2, sticky='w', padx=(24, 0))
        self.full_synchronization_frame.grid_propagate(False)

        self.synchronization_frame.grid(row=0, column=1, pady=(5, 0), padx=(36, 0))
        self.synchronization_frame.grid_propagate(False)
        self.header_synchronization.grid(row=0, column=0, sticky='n', pady=(5, 0), columnspan=2)
        self.checkbutton_synchronization.grid(row=1, column=0, sticky='w', padx=(5,0), pady=(5,0))
        self.checkbutton_multiple_samples.grid(row=1, column=1, sticky='w', pady=(5,0))
        self.button_synchronization.grid(row=2, column=0, pady=(5,0))
        self.view_logfile_button.grid(row=2, column=1, pady=(5,0))
        self.checkbutton_first_line_synchronization.grid(row=3, column=0, sticky='w', columnspan=2, padx=(5,0), pady=(5,0))

        self.data_status_frame.grid(row=0, column=0, pady=5, padx=9)
        self.data_status_frame.grid_propagate(False)
        self.logfile_status_frame.grid(row=0, column=0)
        self.logfile_status_frame.grid_propagate(False)
        self.sample_status_frame.grid(row=0, column=1, padx=(16, 0))
        self.sample_status_frame.grid_propagate(False)

        self.conversion_frame.grid(row=7, column=0, pady=10, columnspan=2, sticky='w', padx=(24,0))
        self.conversion_frame.grid_propagate(False)
        self.directory_entry.grid(row=0, column=0, pady=(5, 0), columnspan=4, padx=(10, 0))
        self.browse_directory_button.grid(row=0, column=4, pady=(5, 0), sticky='w')
        self.go_button.grid(row=0, column=18, pady=(5, 0), sticky='w')
        self.build_laser_duration_button.grid(row=0, column=19, pady=(5,0), sticky='e')
        self.progressbar.grid(row=5, column=0, columnspan=20, pady=(10, 0), padx=(10, 0))
