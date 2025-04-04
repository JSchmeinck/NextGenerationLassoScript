import pandas as pd
import numpy as np



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
                if 'Area' in logfile_dataframe.loc[0, 'Comment']:
                    logfile_dataframe = logfile_dataframe.drop(index=0).reset_index(drop=True)
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
                    iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                'Comment',
                                                'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                'Scan Velocity (um/s)',
                                                'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)', 'A', 'B', 'C', 'D', 'E']

                logfile_dictionary = {}
                self.area_ablation = False

                if 'Lasso' in iolite_dataframe.loc[0, 'Comment']:
                    iolite_dataframe = iolite_dataframe.drop(index=0).reset_index(drop=True)
                    self.area_ablation = True

                if self.area_ablation is True:


                    x_array = iolite_dataframe[(iolite_dataframe['Laser State'] == 'On') & (iolite_dataframe['Intended X(um)'].notna())]['Intended X(um)'].to_numpy()
                    y_array = iolite_dataframe[
                        (iolite_dataframe['Laser State'] == 'On') & (iolite_dataframe['Intended Y(um)'].notna())][
                        'Intended Y(um)'].to_numpy()
                    scan_speed_array = iolite_dataframe[(iolite_dataframe['Laser State'] == 'On') & (iolite_dataframe['Scan Velocity (um/s)'].notna())]['Scan Velocity (um/s)'].to_numpy()
                    spotsize = iolite_dataframe[
                        (iolite_dataframe['Laser State'] == 'On') & (iolite_dataframe['Spot Size (um)'].notna())][
                        'Spot Size (um)'].to_numpy()


                    if np.all(spotsize == spotsize[0]):
                        spotsize_array = np.full(len(x_array), spotsize[0])
                    else:
                        return print('Not all spot sizes the same size')


                    pattern_number_array = np.repeat(np.arange(1, len(x_array) // 2 + 1), 2)
                    name_array = pattern_number_array
                    name_array = name_array.astype(str)
                    type_array = pattern_number_array
                    run_queue_order_array = pattern_number_array


                else:
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
                    spotsize_array[0] = spotsize_array[1]
                    spotsize_array[0] = spotsize_array[1]
                    if isinstance(spotsize_array[0], np.int64):
                        pass
                    else:
                        if 'x' in spotsize_array[0]:
                            # Extract the number before 'x' using vectorized string operations
                            updated_value = spotsize_array[0].split(' x ')[0]  # Extract the number before 'x'
                            updated_arr = np.full(spotsize_array.shape, int(updated_value))
                            spotsize_array = updated_arr
                    spotsize_array = spotsize_array.repeat(2)

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

                if self.area_ablation:
                    try:
                        logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                    'Comment',
                                                    'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                    'Scan Velocity (um/s)',
                                                    'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type',
                                                    'Spot Size (um)']
                    except ValueError:
                        logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                    'Comment',
                                                    'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                    'Scan Velocity (um/s)',
                                                    'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type',
                                                    'Spot Size (um)', 'A', 'B', 'C', 'D', 'E']

                    logfile_dictionary = {}

                    x_array = logfile_dataframe[
                        (logfile_dataframe['Laser State'] == 'On') & (logfile_dataframe['Intended X(um)'].notna())][
                        'Intended X(um)'].to_numpy()
                    y_array = logfile_dataframe[
                        (logfile_dataframe['Laser State'] == 'On') & (logfile_dataframe['Intended Y(um)'].notna())][
                        'Intended Y(um)'].to_numpy()
                    scan_speed_array = logfile_dataframe[(logfile_dataframe['Laser State'] == 'On') & (
                        logfile_dataframe['Scan Velocity (um/s)'].notna())]['Scan Velocity (um/s)'].to_numpy()
                    spotsize = logfile_dataframe[
                        (logfile_dataframe['Laser State'] == 'On') & (logfile_dataframe['Spot Size (um)'].notna())][
                        'Spot Size (um)'].to_numpy()
                    timestamp_array =  logfile_dataframe[(logfile_dataframe['Laser State'] == 'On') & logfile_dataframe['Intended X(um)'].notna()]['Timestamp'].to_numpy()

                    if np.all(spotsize == spotsize[0]):
                        spotsize_array = np.full(len(x_array), spotsize[0])
                    else:
                        return print('Not all spot sizes the same size')

                    pattern_number_array = np.repeat(np.arange(1, len(x_array) // 2 + 1), 2)
                    name_array = pattern_number_array
                    name_array = name_array.astype(str)
                    type_array = pattern_number_array
                    run_queue_order_array = pattern_number_array

                    logfile_dictionary['Timestamp'] = timestamp_array
                    logfile_dictionary['Pattern #'] = pattern_number_array
                    logfile_dictionary['Name'] = name_array
                    logfile_dictionary['Type'] = type_array
                    logfile_dictionary['Run Queue Order'] = run_queue_order_array
                    logfile_dictionary['Scan Speed(Î¼m/sec)'] = scan_speed_array
                    logfile_dictionary['X(um)'] = x_array
                    logfile_dictionary['Y(um)'] = y_array

                    logfile_dictionary['Spotsize'] = spotsize_array

                    logfile_dataframe = pd.DataFrame(logfile_dictionary)

                    self.gui.synchronizer.standard_logfile = True

                    return logfile_dataframe
                try:
                    logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                 'Comment',
                                                 'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                 'Scan Velocity (um/s)',
                                                 'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)']
                except ValueError:
                    logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                 'Comment',
                                                 'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                 'Scan Velocity (um/s)',
                                                 'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)', 'A', 'B', 'C', 'D', 'E']
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



    

        