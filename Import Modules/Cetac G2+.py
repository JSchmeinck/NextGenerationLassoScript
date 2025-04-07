import pandas as pd
import numpy as np

def run(logfile):
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

        run_queue_order_array = run_queue_order_array - 1

    timestamp_array = \
    iolite_dataframe[iolite_dataframe['Laser State'] == 'On'][
        'Timestamp'].to_numpy()
    timestamp_array = np.unique(timestamp_array)

    name_array = iolite_dataframe['Comment'].dropna().values
    name_array = name_array.repeat(2)

    if area_ablation is True:
        type_array = iolite_dataframe['Spot Type'].to_numpy()
        type_array = type_array[:, 0]
        type_array = type_array[0::6]
        type_array = type_array.repeat(2)

        spotsize_array = iolite_dataframe['Spot Size (um)'].to_numpy()
        spotsize_array = spotsize_array[0::6]
        spotsize_array = spotsize_array.repeat(2)
        spotsize_array = spotsize_array.astype(float)
    else:
        type_array = iolite_dataframe['Spot Type'].to_numpy()
        type_array = type_array[:, 0]
        type_array = type_array[0::7]
        type_array = type_array.repeat(2)

        spotsize_array = iolite_dataframe['Spot Size (um)'].to_numpy()
        spotsize_array = spotsize_array[0::7]
        spotsize_array = spotsize_array.repeat(2)
        spotsize_array = spotsize_array.astype(float)

    x_array = iolite_dataframe['Intended X(um)'].dropna().values
    y_array = iolite_dataframe['Intended Y(um)'].dropna().values

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

    return logfile_dataframe