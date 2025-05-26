import sqlite3
import numpy as np
import os # Added for example usage


def extract_ms1_data(db_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Opens the 'Frames' table in a SQLite database, extracts 'Time' and
    'SummedIntensities' for MS1 scans (MsMsType = 0).

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A tuple containing two NumPy arrays:
        - ms1_times: Array of time values for MS1 scans.
        - ms1_intensities: Array of summed intensities for MS1 scans.
    """
    ms1_times_list = []
    ms1_intensities_list = []
    conn = None
    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the table and columns exist
        cursor.execute("PRAGMA table_info(Frames)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        required_columns = ['Time', 'SummedIntensities', 'MsMsType']
        if not all(col in column_names for col in required_columns):
            raise ValueError(f"Table 'Frames' is missing one or more required columns: {required_columns}")

        # Select Time and SummedIntensities for MS1 scans (MsMsType = 0)
        query = "SELECT Time, SummedIntensities FROM Frames WHERE MsMsType = 0"
        cursor.execute(query)

        for row in cursor.fetchall():
            ms1_times_list.append(row[0])
            ms1_intensities_list.append(row[1])

        print(f"Extracted data for {len(ms1_times_list)} MS1 scans.")

    except sqlite3.Error as e:
        print(f"SQLite error occurred in extract_ms1_data: {e}")
        # Return empty arrays in case of error during DB operations
        return np.array([]), np.array([])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return np.array([]), np.array([])
    except ValueError as e:
        print(f"Error: {e}")
        return np.array([]), np.array([])
    finally:
        if conn:
            conn.close()

    return np.array(ms1_times_list), np.array(ms1_intensities_list)


def create_maldi_table(
    db_path: str,
    pixeltimes: np.ndarray,
    pixelxpos: np.ndarray,
    pixelypos: np.ndarray,
    spot_size: float,
    scans_per_ms1,
    line_length: np.ndarray# Argument for SpotSize
) -> None:
    """
    Creates/populates MALDI tables, updates ScanMode. Uses INTEGER type for
    IDs, counts, indices, flags and REAL for floating-point values.

    Args:
        db_path: Path to the SQLite database file.
        pixeltimes: NumPy array of target time points for pixels.
        pixelxpos: NumPy array of X coordinates corresponding to pixeltimes.
        pixelypos: NumPy array of Y coordinates corresponding to pixeltimes.
        spot_size: The value to be inserted into the SpotSize column (REAL).
        time_tolerance: Max time difference for matching (REAL).
    """
    conn = None
    try:
        # --- Input Validation ---
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        if not all(isinstance(arr, np.ndarray) for arr in [pixeltimes, pixelxpos, pixelypos]):
             raise TypeError("pixeltimes, pixelxpos, and pixelypos must be NumPy arrays.")
        if not (len(pixeltimes) == len(pixelxpos) == len(pixelypos)):
            raise ValueError("Lookup arrays must have the same length.")
        if not isinstance(spot_size, (int, float)):
             raise TypeError("spot_size must be numeric.")
        spot_size = float(spot_size) # Ensure spot_size is float

        # Calculate Min/Max for metadata (these represent indices, so keep as int in Python)
        if pixeltimes.size == 0:
             print("Warning: Pixel lookup arrays empty. Defaulting bounds to 0.")
             min_x_idx, max_x_idx, min_y_idx, max_y_idx = 0, 0, 0, 0
        else:
            # Get integer min/max from index arrays
            min_x_idx = int(np.min(pixelxpos))
            max_x_idx = int(np.max(pixelxpos))
            min_y_idx = int(np.min(pixelypos))
            max_y_idx = int(np.max(pixelypos))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- Verify required tables and columns ---
        # (Verification logic remains the same)
        cursor.execute("PRAGMA table_info(Frames)")
        frames_columns_info = cursor.fetchall(); frames_column_names = [c[1] for c in frames_columns_info]
        required_frames_columns = ['Time', 'MsMsType', 'ScanMode']
        id_column_present = 'Id' in frames_column_names
        if not all(col in frames_column_names for col in required_frames_columns):
            raise ValueError(f"Frames table missing columns: {[c for c in required_frames_columns if c not in frames_column_names]}")

        cursor.execute("PRAGMA table_list"); tables = [t[1] for t in cursor.fetchall()]
        can_insert_metadata = False
        if 'GlobalMetadata' in tables:
            cursor.execute("PRAGMA table_info(GlobalMetadata)"); metadata_columns_info = cursor.fetchall()
            if all(c in [m[1] for m in metadata_columns_info] for c in ['Key', 'Value']): can_insert_metadata = True
            else: print(f"Warning: 'GlobalMetadata' missing Key/Value columns.")
        else: print("Warning: 'GlobalMetadata' not found.")

        # --- 0. Update ScanMode in Frames table (using INTEGER) ---
        print("Updating 'ScanMode' in 'Frames' table to 20...")
        # Ensure ScanMode column exists and has compatible type affinity if possible
        if 'ScanMode' in frames_column_names:
             cursor.execute("UPDATE Frames SET ScanMode = ?", (20,)) # Use integer 20
             print("'ScanMode' updated successfully.")
        else:
             print("Warning: ScanMode column not found in Frames table, skipping update.")


        # --- 0.5 Add entries to GlobalMetadata table (Value remains TEXT) ---
        if can_insert_metadata:
            print("Adding/Updating MALDI metadata in 'GlobalMetadata' table...")
            # Convert integer indices to string for storage in TEXT Value column
            metadata_to_insert = [
                ('MaldiApplicationType', 'Imaging'), # TEXT
                ('ImagingAreaMinXIndexPos', str(min_x_idx)), # Store int index as TEXT
                ('ImagingAreaMaxXIndexPos', str(max_x_idx)), # Store int index as TEXT
                ('ImagingAreaMinYIndexPos', str(min_y_idx)), # Store int index as TEXT
                ('ImagingAreaMaxYIndexPos', str(max_y_idx))  # Store int index as TEXT
            ]
            meta_insert_sql = "INSERT OR REPLACE INTO GlobalMetadata (Key, Value) VALUES (?, ?)"
            cursor.executemany(meta_insert_sql, metadata_to_insert)
            print("MALDI metadata added/updated successfully.")

        # --- 0.7 Create and populate MaldiFrameLaserInfo table (Mixed INTEGER/REAL/TEXT) ---
        print("Creating and populating 'MaldiFrameLaserInfo' table...")
        cursor.execute("DROP TABLE IF EXISTS MaldiFrameLaserInfo")
        # Define column types explicitly
        cursor.execute("""
            CREATE TABLE MaldiFrameLaserInfo (
                Id INTEGER PRIMARY KEY,
                LaserApplicationName TEXT,
                LaserParameterName TEXT,
                LaserBoost REAL,
                LaserFocus REAL,
                BeamScan INTEGER,
                BeamScanSizeX INTEGER,
                BeamScanSizeY INTEGER,
                WalkOnSpotMode INTEGER,
                WalkOnSpotShots INTEGER,
                SpotSize REAL
            )
        """)
        # Prepare data tuple with correct Python types (int for INTEGER, float for REAL)
        laser_info_data = (
            1,            # Id (INTEGER)
            'Custom',     # LaserApplicationName (TEXT)
            'Single',     # LaserParameterName (TEXT)
            0.0,          # LaserBoost (REAL)
            85.0,         # LaserFocus (REAL)
            1,            # BeamScan (INTEGER)
            16,           # BeamScanSizeX (INTEGER)
            16,           # BeamScanSizeY (INTEGER)
            0,            # WalkOnSpotMode (INTEGER)
            50,           # WalkOnSpotShots (INTEGER)
            spot_size     # SpotSize (REAL)
        )
        laser_insert_sql = """INSERT INTO MaldiFrameLaserInfo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor.execute(laser_insert_sql, laser_info_data)
        print("'MaldiFrameLaserInfo' table created and populated successfully.")

        # --- 1. Create the MaldiFrameInfo table (Mixed INTEGER/REAL/TEXT) ---
        print("Creating 'MaldiFrameInfo' table...")
        cursor.execute("DROP TABLE IF EXISTS MaldiFrameInfo")
        # Define column types explicitly
        cursor.execute("""
            CREATE TABLE MaldiFrameInfo (
                Frame INTEGER PRIMARY KEY,
                Chip INTEGER,
                SpotName TEXT,
                RegionNumber INTEGER,
                XIndexPos INTEGER,
                YIndexPos INTEGER,
                LaserPower INTEGER,
                NumLaserShots INTEGER,
                LaserRepRate INTEGER,
                MotorPositionX REAL,
                MotorPositionY REAL,
                MotorPositionZ REAL,
                LaserInfo INTEGER
            )
        """)
        print("Table 'MaldiFrameInfo' created successfully.")

        # --- 2. Fetch necessary data from Frames table ---
        print("Fetching data from 'Frames' table for coordinate assignment...")
        frame_id_col = "Id" if id_column_present else "ROWID"
        if not id_column_present: print(f"Warning: Using 'ROWID' as Frame identifier.")
        select_query = f"SELECT {frame_id_col}, Time, MsMsType FROM Frames ORDER BY {frame_id_col}"
        cursor.execute(select_query); all_frames_data = cursor.fetchall()

        if not all_frames_data:
            print("Warning: 'Frames' table empty. No MaldiFrameInfo data.")
            conn.commit(); print("Database changes (ScanMode, Metadata, LaserInfo) committed.")
            return

        frame_details = {row[0]: {'time': row[1], 'type': row[2]} for row in all_frames_data}
        sorted_frame_ids = sorted(frame_details.keys())

        # --- 3. Initialize data structures for coordinate assignment (using ints for coords) ---
        frame_xy_map = {frame_id: (0, 0) for frame_id in sorted_frame_ids} # Initialize with ints
        pixel_used_flags = np.zeros(len(pixeltimes), dtype=bool)
        num_pixels = len(pixeltimes)

        # --- 4. First Pass: Assign coordinates (casting to int) ---
        print(f"Starting first pass: Matching MS1 scans...")
        ms1_frames_processed_pass1 = 0; pixels_assigned_pass1 = 0

        ms1_frames = {fid: details['time'] for fid, details in frame_details.items() if details['type'] == 0}
        if not ms1_frames:
            print("Warning: No MS1 scans found for second pass.")
        else:
            ms1_ids = np.array(list(ms1_frames.keys()));
            ms1_times_only = np.array(list(ms1_frames.values()))
        line_start_ids = []
        for time in pixeltimes:
            closest_ms1_frame_id = ms1_ids[np.argmin(np.abs(ms1_times_only - time))]
            line_start_ids.append(closest_ms1_frame_id)
        in_line = False
        for i, frame_id in enumerate(sorted_frame_ids):
            details = frame_details[frame_id]; frame_time = details['time']; ms_type = details['type']
            if ms_type == 0:
                ms1_frames_processed_pass1 += 1
                current_x, current_y = 0, 0 # Default to integers
                if frame_id in line_start_ids:
                    in_line = True
                    pixel_number = 1
                    index = line_start_ids.index(frame_id)
                    number_of_pixels = line_length[index]
                    current_x = int(pixelxpos[index])
                    current_y = int(pixelypos[index])

                    start_x = current_x
                    static_y = current_y
                    pixel_used_flags[index] = True
                    pixels_assigned_pass1 += 1
                    start_frame_id = frame_id
                elif in_line:
                    if frame_id == start_frame_id + pixel_number*(scans_per_ms1+1):
                        current_x = start_x+pixel_number
                        current_y = static_y
                        pixels_assigned_pass1 += 1
                        pixel_number += 1
                        if pixel_number > number_of_pixels:
                            in_line = False
                frame_xy_map[frame_id] = (current_x, current_y)
                for scan_number in range(scans_per_ms1):
                    potential_ms2_id = frame_id + scan_number + 1
                    if potential_ms2_id in frame_details and frame_details[potential_ms2_id]['type'] != 0:
                        next_frame_id_in_sequence = sorted_frame_ids[i+scan_number + 1] if i + scan_number + 1 < len(sorted_frame_ids) else None
                        if potential_ms2_id == next_frame_id_in_sequence: frame_xy_map[potential_ms2_id] = (current_x, current_y)
        print(f"First pass complete. Processed {ms1_frames_processed_pass1} MS1 scans. Assigned {pixels_assigned_pass1} pixels.")

        # --- 6. Final Data Preparation for MaldiFrameInfo (using correct Python types) ---
        print("Preparing final data for insertion into 'MaldiFrameInfo'...")
        maldi_data_to_insert = []
        # Define fixed values with correct types (int or float)
        fixed_chip = 0                   # INTEGER
        fixed_region_number = 0          # INTEGER
        fixed_laser_power = 5            # INTEGER (chosen based on previous value)
        fixed_num_shots = 100            # INTEGER
        fixed_laser_rep_rate = 100       # INTEGER
        fixed_motor_z = 0.0              # REAL
        fixed_laser_info = 1             # INTEGER (links to Id=1)

        for frame_id in sorted_frame_ids:
            # Ensure retrieved coords are ints
            x_pos, y_pos = map(int, frame_xy_map.get(frame_id, (0, 0)))
            # SpotName remains TEXT
            spot_name = f'R{fixed_region_number:02d}X{x_pos}Y{y_pos}'
            # Motor positions should be floats for REAL columns
            motor_x = float(x_pos)
            motor_y = float(y_pos)
            # Assemble data tuple with correct Python types matching table definition
            row_data = (
                int(frame_id),            # Frame (INTEGER)
                fixed_chip,               # Chip (INTEGER)
                spot_name,                # SpotName (TEXT)
                fixed_region_number,      # RegionNumber (INTEGER)
                x_pos,                    # XIndexPos (INTEGER)
                y_pos,                    # YIndexPos (INTEGER)
                fixed_laser_power,        # LaserPower (INTEGER)
                fixed_num_shots,          # NumLaserShots (INTEGER)
                fixed_laser_rep_rate,     # LaserRepRate (INTEGER)
                motor_x,                  # MotorPositionX (REAL)
                motor_y,                  # MotorPositionY (REAL)
                fixed_motor_z,            # MotorPositionZ (REAL)
                fixed_laser_info          # LaserInfo (INTEGER)
            )
            maldi_data_to_insert.append(row_data)

        # --- 7. Bulk Insert into MaldiFrameInfo ---
        print(f"Inserting {len(maldi_data_to_insert)} rows into 'MaldiFrameInfo'...")
        if maldi_data_to_insert:
            insert_sql = """INSERT INTO MaldiFrameInfo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            cursor.executemany(insert_sql, maldi_data_to_insert)
            print("Insertion into 'MaldiFrameInfo' complete.")
        else:
            print("No data generated for MaldiFrameInfo.")

        # --- 8. Commit all changes ---
        conn.commit()
        print("Database changes committed successfully.")

    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")
        if conn: conn.rollback()
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except (ValueError, TypeError) as e:
        print(f"Input or Data error: {e}")
        if conn: conn.rollback()
    except Exception as e:
         print(f"An unexpected error occurred: {e}")
         if conn: conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
# --- Example Usage ---
if __name__ == "__main__":
    # Create a dummy database for demonstration
    DB_FILE = 'test_mass_spec.db'
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS Frames")
    cursor.execute("""
        CREATE TABLE Frames (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Time REAL,
            MsMsType INTEGER,
            SummedIntensities REAL
        )
    """)

    # Add some sample data
    # Case 1: MS1 alone, time not near pixel time
    # Case 2: MS1 -> MS2, time not near pixel time
    # Case 3: MS1 alone, time near pixel time
    # Case 4: MS1 -> MS2, time near pixel time
    # Extra MS1 for cleanup phase
    sample_data = [
        (10.0, 0, 1000.0), # Frame 1: MS1, far from pixel times -> should be (0,0) later
        (10.5, 0, 1100.0), # Frame 2: MS1, far from pixel times
        (10.6, 1, 500.0),  # Frame 3: MS2, follows Frame 2 -> should be (0,0) later
        (20.1, 0, 1200.0), # Frame 4: MS1, near pixel time 20.0 -> should get (1, 0)
        (30.8, 0, 1300.0), # Frame 5: MS1, near pixel time 31.0 -> should get (0, 1)
        (30.9, 1, 600.0),  # Frame 6: MS2, follows Frame 5 -> should get (0, 1)
        (40.0, 0, 1400.0), # Frame 7: MS1, exactly pixel time 40.0 -> should get (1, 1)
        (55.5, 0, 1500.0), # Frame 8: MS1, closest to unmatched pixel time 55.0 -> gets (2,1) in cleanup
        (55.6, 1, 700.0),  # Frame 9: MS2, follows Frame 8 -> gets (2,1) in cleanup
        (65.2, 0, 1600.0), # Frame 10: MS1, near used pixel time 40.0 (tolerance 0.25), but also near 66 (unmatched). Cleanup might assign 66.0 to it.
    ]
    cursor.executemany("INSERT INTO Frames (Time, MsMsType, SummedIntensities) VALUES (?, ?, ?)", sample_data)
    conn.commit()
    conn.close()
    print(f"Created dummy database '{DB_FILE}' with sample data.")

    # --- Function 1 Call ---
    print("\n--- Running extract_ms1_data ---")
    ms1_t, ms1_i = extract_ms1_data(DB_FILE)
    if ms1_t.size > 0:
        print(f"Extracted MS1 Times: {ms1_t}")
        print(f"Extracted MS1 Intensities: {ms1_i}")
    else:
        print("No MS1 data extracted.")


    # --- Function 2 Call ---
    print("\n--- Running create_maldi_table ---")
    # Define the pixel lookup tables
    # Pixel times chosen to demonstrate different cases, including one potentially unused
    pixel_times = np.array([20.0, 31.0, 40.0, 55.0, 66.0])
    pixel_x = np.array([    1,    0,    1,    2,    2]) # X coordinates
    pixel_y = np.array([    0,    1,    1,    1,    2]) # Y coordinates

    create_maldi_table(DB_FILE, pixel_times, pixel_x, pixel_y, time_tolerance=0.25)

    # --- Verify Results (Optional) ---
    print("\n--- Verifying MaldiFrameInfo contents ---")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT Frame, SpotName, XIndexPos, YIndexPos FROM MaldiFrameInfo ORDER BY Frame")
        results = cursor.fetchall()
        print("Frame | SpotName | X | Y")
        print("--------------------------")
        for row in results:
            print(f"{row[0]:<5} | {row[1]:<10} | {row[2]:<1} | {row[3]:<1}")
        conn.close()
    except sqlite3.Error as e:
        print(f"Could not verify results: {e}")

    # Expected Output Verification:
    # Frame 1: R00X0Y0 (Time 10.0, no close pixel)
    # Frame 2: R00X0Y0 (Time 10.5, no close pixel)
    # Frame 3: R00X0Y0 (MS2, follows Frame 2)
    # Frame 4: R00X1Y0 (Time 20.1, close to 20.0)
    # Frame 5: R00X0Y1 (Time 30.8, close to 31.0)
    # Frame 6: R00X0Y1 (MS2, follows Frame 5)
    # Frame 7: R00X1Y1 (Time 40.0, close to 40.0)
    # Frame 8: R00X2Y1 (Time 55.5, not close initially, but closest MS1 to unused pixel 55.0 in cleanup)
    # Frame 9: R00X2Y1 (MS2, follows Frame 8)
    # Frame 10: R00X2Y2 (Time 65.2, closest MS1 to unused pixel 66.0 in cleanup)