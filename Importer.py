import pandas as pd
import numpy as np
import os

class Importer:
    def __init__(self, gui):
        self.gui = gui

    def import_laser_logfile(self, logfile, laser_type, rectangular_data_calculation, iolite_file=False, logfile_viewer=False):
        if laser_type == 'Cetac G2+':
            if rectangular_data_calculation is False:
                with open(logfile) as file:
                    logfile_dataframe = pd.read_csv(file, skiprows=1, header=None)
                logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                             'Comment',
                                             'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                             'Scan Velocity (um/s)',
                                             'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)',
                                             'Spot Type', 'Spot Size', 'Spot Angle', 'MFC1', 'MFC2']
                return logfile_dataframe
            else:
                with open(logfile) as file:
                    iolite_dataframe = pd.read_csv(file, skiprows=1, header=None)
                iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                            'Comment',
                                            'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                            'Scan Velocity (um/s)',
                                            'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)',
                                            'Spot Type', 'Spot Size', 'Spot Angle', 'MFC1', 'MFC2']
                logfile_dictionary = {}
                area_ablation = False

                if 'Area' in iolite_dataframe.loc[0, 'Comment']:
                    iolite_dataframe = iolite_dataframe.drop(index=0).reset_index(drop=True)
                    area_ablation = True

                scan_speed_array = iolite_dataframe['Scan Velocity (um/s)'].dropna().values
                scan_speed_array[1::2] = np.nan

                if area_ablation is True:
                    reference_array = iolite_dataframe['Comment'].dropna().values
                    run_queue_array = np.arange(1, len(reference_array) + 1)
                    pattern_number_array = run_queue_array.copy()
                    pattern_number_array = pattern_number_array.repeat(2)
                    new_length = 2 * len(run_queue_array)

                    # Create a new array filled with np.nan
                    run_queue_order_array = np.full(new_length, np.nan)

                    # Place original values at even indices
                    run_queue_order_array[::2] = run_queue_array
                else:
                    pattern_number_array = iolite_dataframe['Sequence Number'].dropna().values
                    pattern_number_array = pattern_number_array.repeat(2)
                    run_queue_order_array = pattern_number_array.copy()
                    pattern_number_array[1::2] = np.nan

                    run_queue_order_array = run_queue_order_array - 1
                    run_queue_order_array[1::2] = np.nan

                name_array = iolite_dataframe['Comment'].dropna().values
                name_array = name_array.repeat(2)
                name_array[1::2] = np.nan

                if area_ablation is True:
                    type_array = iolite_dataframe['Spot Type'].to_numpy()
                    type_array = type_array[:, 0]
                    type_array = type_array[0::6]
                    type_array = type_array.repeat(2)
                    type_array[1::2] = np.nan

                    spotsize_array = iolite_dataframe['Spot Size (um)'].to_numpy()
                    spotsize_array = spotsize_array[0::6]
                    spotsize_array = spotsize_array.repeat(2)
                    spotsize_array = spotsize_array.astype(float)
                    spotsize_array[1::2] = np.nan
                else:
                    type_array = iolite_dataframe['Spot Type'].to_numpy()
                    type_array = type_array[:, 0]
                    type_array = type_array[0::7]
                    type_array = type_array.repeat(2)
                    type_array[1::2] = np.nan

                    spotsize_array = iolite_dataframe['Spot Size (um)'].to_numpy()
                    spotsize_array = spotsize_array[0::7]
                    spotsize_array = spotsize_array.repeat(2)
                    spotsize_array = spotsize_array.astype(float)
                    spotsize_array[1::2] = np.nan

                x_array = iolite_dataframe['Intended X(um)'].dropna().values
                y_array = iolite_dataframe['Intended Y(um)'].dropna().values

                logfile_dictionary['Pattern #'] = pattern_number_array
                logfile_dictionary['Name'] = name_array
                logfile_dictionary['Type'] = type_array
                logfile_dictionary['Run Queue Order'] = run_queue_order_array
                logfile_dictionary['Scan Speed(Î¼m/sec)'] = scan_speed_array
                logfile_dictionary['X(um)'] = x_array
                logfile_dictionary['Y(um)'] = y_array
                logfile_dictionary['Spotsize'] = spotsize_array

                logfile_dataframe = pd.DataFrame(logfile_dictionary)

                return logfile_dataframe

        if laser_type == 'ImageBIO 266':
            if iolite_file and rectangular_data_calculation:
                with open(logfile) as file:
                    iolite_dataframe = pd.read_csv(file, skiprows=1, header=None)
                try:
                    iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                 'Comment',
                                                 'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                 'Scan Velocity (um/s)',
                                                 'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)']
                except ValueError:
                    self.gui.notifications.notification_error(header='Data Type Error',
                                                              body='Your Logfile Data does not match your chosen Laser Type')
                    return False

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

                spotsize_array = iolite_dataframe['Spot Size (um)'].to_numpy()
                spotsize_array = spotsize_array[0::6]
                spotsize_array = spotsize_array.repeat(2)
                spotsize_array[1::2] = np.nan

                x_array = iolite_dataframe['Intended X(um)'].dropna().values
                y_array = iolite_dataframe['Intended Y(um)'].dropna().values

                logfile_dictionary['Pattern #'] = pattern_number_array
                logfile_dictionary['Name'] = name_array
                logfile_dictionary['Type'] = type_array
                logfile_dictionary['Run Queue Order'] = run_queue_order_array
                logfile_dictionary['Scan Speed(Î¼m/sec)'] = scan_speed_array
                logfile_dictionary['X(um)'] = x_array
                logfile_dictionary['Y(um)'] = y_array

                logfile_dictionary['Spotsize'] = spotsize_array

                logfile_dataframe = pd.DataFrame(logfile_dictionary)

                return logfile_dataframe

            if iolite_file and rectangular_data_calculation is False:
                with open(logfile) as file:
                    logfile_dataframe = pd.read_csv(file, skiprows=1, header=None)
                try:
                    logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                 'Comment',
                                                 'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                 'Scan Velocity (um/s)',
                                                 'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)']
                except ValueError:
                    self.gui.notifications.notification_error(header='Data Type Error',
                                                              body='Your Logfile Data does not match your chosen Laser Type')
                    return False
                return logfile_dataframe

            else:
                try:
                    with open(logfile) as f:
                        # pattern_dataframe = pd.read_csv(f, skipinitialspace=True).fillna('Faulty Line')

                        logfile_dataframe = pd.read_csv(f, usecols=['Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                                    'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                                    'Y(um)'], index_col=False)
                except:
                    with open(logfile) as f:
                        logfile_dataframe = pd.read_csv(f, usecols=['ï»¿Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                                    'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                                    'Y(um)'], index_col=False)
                return logfile_dataframe


    def import_sample_file(self, data_type, synchronized):
        sample_rawdata_dictionary: dict = {}
        if data_type == 'iCap TQ (Daisy)':
            for n, m in enumerate(self.gui.list_of_files):
                if synchronized:
                    with open(m) as f:
                        # First 15 lines have to be skipped (in Qtegra files)
                        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                       sep=self.gui.get_separator_import(),
                                                       skiprows=13)
                    sample_rawdata_dictionary[f'{self.gui.filename_list[n]}'] = df
                    break
                else:
                    with open(m) as f:
                        # First 15 lines have to be skipped (in Qtegra files)
                        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                       sep=self.gui.get_separator_import())
                    sample_rawdata_dictionary[f'{self.gui.filename_list[n]}'] = df

            return sample_rawdata_dictionary

        if data_type == 'Agilent 7900':
            # Loop through the imported directorys one by one
            for n, m in enumerate(self.gui.list_of_files):
                individual_lines_dictionary = {}
                directory = os.fsencode(m)
                # Loop trough the files inside the directory
                for ticker, file in enumerate(os.listdir(directory)):
                    filename = os.fsdecode(file)
                    # Only use the files that are csv data
                    if filename.endswith(".csv"):
                        with open(f'{m}/{filename}') as f:
                            df = pd.read_csv(filepath_or_buffer=f,
                                             sep=self.gui.get_separator_import(),
                                             skiprows=3,
                                             skipfooter=1,
                                             engine='python')
                        individual_lines_dictionary[f'Line_{ticker + 1}'] = df
                    sample_rawdata_dictionary[f'{self.gui.filename_list[n]}'] = individual_lines_dictionary

            return sample_rawdata_dictionary

        if data_type == 'EIC':
            for n, m in enumerate(self.gui.list_of_files):
                with open(m) as f:
                    df: pd.DataFrame = pd.read_csv(f, sep=self.gui.get_separator_import(), skiprows=2, engine='python')
                df.drop(columns=[df.columns[-1]], inplace=True)
                sample_rawdata_dictionary, list_of_unique_masses_in_file, time_data_sample = self.gui.synchronizer.get_data(sample_name='Full Data')

            return sample_rawdata_dictionary

    

        