import xml.etree.ElementTree as ET
import base64
import zlib
import struct
import numpy as np
import warnings
import sys
import re
import os
import xml.sax.saxutils
from xml.sax.saxutils import escape # For escaping attribute values

# Define the standard mzML namespace URI as a fallback
DEFAULT_MZML_NAMESPACE = "http://psi.hupo.org/ms/mzml"

TARGET_CVPARAM_ACCESSION = "MS:1000527"

def find_cv_param(element, accession, ns_map):
    """
    Helper function to find a cvParam with a specific accession within an element.
    Uses the namespace dictionary provided (maps prefix to URI).
    """
    # Find the URI for the 'mzml' prefix, default if not found
    mzml_uri = ns_map.get('mzml', DEFAULT_MZML_NAMESPACE)
    if not mzml_uri: # Should not happen with default, but safety check
         warnings.warn(f"mzML namespace URI not found when searching for {accession}.")
         return None # Cannot search without URI

    # Construct the XPath query using the namespace URI directly (Clark notation)
    xpath_query = f'.//{{{mzml_uri}}}cvParam[@accession="{accession}"]'
    return element.find(xpath_query)

def find_cv_param_ms2(element, accession, ns_map):
    """
    Helper function to find a cvParam with a specific accession within an element.
    Uses the namespace dictionary provided. Handles potential missing namespace.
    """
    # Default to 'mzml' prefix if available in map, otherwise try without prefix
    prefix_to_use = 'mzml' if 'mzml' in ns_map else None

    if not prefix_to_use or not ns_map[prefix_to_use]:
        # Attempt without namespace if map is missing/incomplete or URI is empty
        # This covers cases where the default namespace is used without a prefix in findall
        return element.find(f'.//cvParam[@accession="{accession}"]') # Check children

    ns_uri = ns_map[prefix_to_use]
    # Construct the XPath query using the namespace URI in Clark notation {URI}tag
    # Search relative to the current element '.' and its descendants '//'
    xpath_query = f'.//{{{ns_uri}}}cvParam[@accession="{accession}"]'
    try:
      return element.find(xpath_query)
    except SyntaxError: # Fallback if XPath syntax with {} fails in some versions/cases
        warnings.warn(f"XPath with Clark notation failed for accession {accession}. Retrying without explicit namespace.")
        return element.find(f'.//cvParam[@accession="{accession}"]')


def decode_binary_array(bda_element, ns):
    """
    Decodes a binaryDataArray element based on its cvParams.

    Args:
        bda_element (ET.Element): The <binaryDataArray> element.
        ns (dict): The namespace dictionary.

    Returns:
        np.array or None: A numpy array containing the decoded data,
                         or None if decoding fails or data is unsupported.
    """
    data_type = None
    compression_type = "MS:1000576" # Default: no compression (MS:1000576)
    data_format_char = None
    data_size = None # Size in bytes for one data point

    # Determine data type and precision from cvParams
    if find_cv_param(bda_element, "MS:1000523", ns) is not None: # 64-bit float
        data_type = np.float64
        data_format_char = 'd' # double
        data_size = 8
    elif find_cv_param(bda_element, "MS:1000521", ns) is not None: # 32-bit float
        data_type = np.float32
        data_format_char = 'f' # float
        data_size = 4
    elif find_cv_param(bda_element, "MS:1000522", ns) is not None: # 64-bit int
        data_type = np.int64
        data_format_char = 'q' # long long
        data_size = 8
    elif find_cv_param(bda_element, "MS:1000519", ns) is not None: # 32-bit int
        data_type = np.int32
        data_format_char = 'i' # int
        data_size = 4
    else:
        # Check for other potential types if needed (e.g., MS:1000520 - 64-bit int (signed?), MS:1000518 - 32-bit int (signed?))
        # Currently warns and returns None if none of the common types are found.
        accessions_checked = "MS:1000523 (64f), MS:1000521 (32f), MS:1000522 (64i), MS:1000519 (32i)"
        warnings.warn(f"Unsupported or missing data type cvParam in binary data array. Checked accessions: {accessions_checked}")
        return None

    # Determine compression type from cvParams
    if find_cv_param(bda_element, "MS:1000574", ns) is not None: # zlib compression
        compression_type = "MS:1000574"
    elif find_cv_param(bda_element, "MS:1000576", ns) is not None: # no compression (explicitly stated)
        compression_type = "MS:1000576"
    # If neither is found, the default 'MS:1000576' (no compression) remains.
    # Note: MS-Numpress (e.g., MS:1002312, MS:1002313, MS:1002314) is not supported here.

    # Find the binary data tag
    binary_tag = bda_element.find('./mzml:binary', ns)

    # Handle cases with empty data
    if binary_tag is None or binary_tag.text is None:
        # Check if defaultArrayLength is explicitly 0
        default_len_str = bda_element.get('defaultArrayLength')
        if default_len_str and int(default_len_str) == 0:
             return np.array([], dtype=data_type) # Return empty array if length is 0
        else:
            # If tag is missing/empty but defaultArrayLength is not 0, it's potentially an issue.
            warnings.warn("Binary data tag missing or empty, but defaultArrayLength is not '0'. Returning empty array.")
            return np.array([], dtype=data_type) # Or return None? Empty array seems safer.

    base64_encoded_data = binary_tag.text.strip()
    if not base64_encoded_data:
         # If the binary tag exists but is empty after stripping whitespace
         return np.array([], dtype=data_type)

    # Decode Base64
    try:
        decoded_data = base64.b64decode(base64_encoded_data)
    except Exception as e:
         warnings.warn(f"Base64 decoding failed: {e}. Data snippet: '{base64_encoded_data[:50]}...'")
         return None

    # Decompress if necessary
    decompressed_data = None
    if compression_type == "MS:1000574": # zlib compression
        try:
            decompressed_data = zlib.decompress(decoded_data)
        except zlib.error as e:
             warnings.warn(f"Zlib decompression failed: {e}")
             return None
    elif compression_type == "MS:1000576": # no compression
        decompressed_data = decoded_data
    else:
        warnings.warn(f"Unsupported compression type found: {compression_type}. Only 'zlib' (MS:1000574) and 'no compression' (MS:1000576) are supported.")
        return None

    # Check for empty data after potential decompression
    if not decompressed_data:
        return np.array([], dtype=data_type)

    # Check data integrity: length vs data type size
    if len(decompressed_data) % data_size != 0:
         warnings.warn(f"Decompressed data length ({len(decompressed_data)}) is not a multiple of the expected data size ({data_size} bytes for type {data_type.__name__}). Data might be truncated or corrupted.")
         # Truncate to the largest possible number of full elements.
         # This might hide errors, but attempts to recover some data.
         # Returning None might be safer depending on requirements.
         num_elements = len(decompressed_data) // data_size
         if num_elements == 0:
             return np.array([], dtype=data_type) # Cannot form even one element
         decompressed_data = decompressed_data[:num_elements * data_size] # Keep only full elements
    else:
        num_elements = len(decompressed_data) // data_size

    if num_elements == 0:
        # This case can occur if truncation above results in zero elements,
        # or if the original data represented zero elements.
        return np.array([], dtype=data_type)

    # Unpack the binary data into numbers
    try:
        # Format string for struct.unpack
        # Assumes little-endian byte order ('<'), which is common in mzML,
        # though not strictly guaranteed by the standard.
        format_string = f'<{num_elements}{data_format_char}'
        unpacked_data = struct.unpack(format_string, decompressed_data)
        return np.array(unpacked_data, dtype=data_type)
    except struct.error as e:
        warnings.warn(f"Struct unpacking failed: {e}. Format: '{format_string}', Expected elements: {num_elements}, Data length: {len(decompressed_data)}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during unpacking
        warnings.warn(f"An unexpected error occurred during data unpacking: {e}")
        return None


def parse_mzml_manual(filepath, gui=None):
    """
    Parses an mzML file manually to extract TIC and MS1 scan data.

    Args:
        filepath (str): Path to the mzML file.

    Returns:
        tuple: A tuple containing:
            - tic_data (tuple): (tic_rt_array, tic_intensity_array). Arrays are numpy arrays.
                                Returns (None, None) if TIC not found or decoding fails.
            - ms1_scans (list): A list of dictionaries, where each dict contains
                                'rt' (float, in minutes), 'mz' (np.array),
                                'intensity' (np.array). Returns empty list if no
                                valid MS1 scans are found.
    """
    with open(filepath, 'r') as f:
        for line in f:
            if '<spectrumList' in line:
                match = re.search(r'count="(\d+)"', line)
                if match:
                    number_of_spectra = int(match.group(1))
                    break

    try:
        # Use iterparse for potentially large files, though parse is simpler for moderate sizes
        # For simplicity here, we stick with ET.parse
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file '{filepath}': {e}", file=sys.stderr)
        return (None, None), []
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'", file=sys.stderr)
        return (None, None), []
    except Exception as e:
        print(f"An unexpected error occurred opening or parsing '{filepath}': {e}", file=sys.stderr)
        return (None, None), []

    # --- Namespace Handling ---
    namespace_uri = None
    # Try extracting from the root tag's Clark notation {namespace}tag
    if '}' in root.tag and root.tag.startswith('{'):
        namespace_uri = root.tag.split('}', 1)[0][1:]
    else:
        # Fallback: Check root attributes for xmlns or xmlns:prefix
        if 'xmlns' in root.attrib: # Default namespace
            namespace_uri = root.attrib['xmlns']
        else: # Check for prefixed namespace (less common for root mzML element)
            for key, value in root.attrib.items():
                if key.startswith('xmlns:'):
                    # If multiple prefixes exist, this takes the first one found.
                    # We assume it's the main mzML namespace.
                    namespace_uri = value
                    break

    ns = {}
    if namespace_uri:
        # Use 'mzml' as the prefix in our code, mapped to the detected URI
        ns['mzml'] = namespace_uri
        print(f"Detected mzML namespace: {namespace_uri}")
    else:
        # If detection failed, warn and assume the standard namespace URI.
        # This is a common scenario if the namespace isn't on the root element itself
        # but is used consistently throughout the file.
        warnings.warn(
            "Could not automatically determine mzML namespace from root element. "
            f"Assuming standard namespace: {DEFAULT_MZML_NAMESPACE}. "
            "XPath queries might fail if this is incorrect."
        )
        ns['mzml'] = DEFAULT_MZML_NAMESPACE
        # Alternative: If you are sure the file has NO namespace, use ns = {}
        # and remove 'mzml:' prefixes from all find/findall calls below.

    # --- Extract MS1 Scans ---
    ms1_scans_data = []
    print("Searching for spectrum list...")
    spectrum_list = root.find('.//mzml:spectrumList', ns)


    spec_list_count_str = spectrum_list.get('count')
    if spec_list_count_str:
        print(f"Processing spectra in <spectrumList count='{spec_list_count_str}'>...")
    else:
        print("Processing spectra in <spectrumList> (count attribute missing)...")

    processed_spectra_count = 0
    ms1_count = 0
    invalid_ms1_count = 0

    # Iterate through spectrum elements
    # Using findall('.//mzml:spectrum', ns) is simpler but loads all into memory first.
    # Using iterfind is more memory efficient for very large files:
    # for spectrum in spectrum_list.iterfind('mzml:spectrum', ns):
    # For compatibility with the original structure, let's use findall:
    #all_spectra = spectrum_list.findall('.//mzml:spectrum', ns)
    total_spectra_in_list = number_of_spectra
    print(f"Found {total_spectra_in_list} spectrum elements.")

    tic_intensity = []
    tic_rt = []

    for spectrum in spectrum_list.iterfind('mzml:spectrum', ns):
        gui.increase_progress(float(1 / number_of_spectra) * 100 * processed_spectra_count)
        processed_spectra_count += 1

        # 1. Check MS Level (must be MS1)
        ms_level_param = find_cv_param(spectrum, "MS:1000511", ns) # cvParam for 'ms level'

        if ms_level_param is None or ms_level_param.get('value') != '1':
            continue # Skip if not MS1 or level is missing

        tic_param = find_cv_param(spectrum, "MS:1000285", ns)
        tic_value_str = float(tic_param.get('value'))
        tic_intensity.append(tic_value_str)
        ms1_count += 1
        scan_rt = None
        mz_array = None
        intensity_array = None
        valid_scan = True # Flag to track if all parts are found and valid

        # 2. Get Retention Time
        # Scan time is usually within a <scanList>/<scan> element
        scan_list = spectrum.find('.//mzml:scanList', ns)
        if scan_list is not None:
            # Typically only one <scan> per <scanList> in indexed mzML
            scan_element = scan_list.find('.//mzml:scan', ns)
            if scan_element is not None:
                rt_param = find_cv_param(scan_element, "MS:1000016", ns) # cvParam for 'scan start time'
                if rt_param is not None and rt_param.get('value') is not None:
                    try:
                        rt_value_str = rt_param.get('value')
                        rt_value = float(rt_value_str)
                        # Check units (CV Param UO:0000010 for minute, UO:0000031 for second)
                        unit_accession = rt_param.get('unitAccession')
                        unit_name = rt_param.get('unitName')
                        if unit_accession == 'UO:0000031' or unit_name == 'minute':

                            scan_rt = rt_value * 60.0
                        elif unit_accession == 'UO:0000010' or unit_name == 'second':
                            # Convert minutes to seconds (common unit for chromatography)
                            scan_rt = rt_value # Already in minutes
                        else:
                            # Assume minutes if unit is missing or unrecognized, but warn.
                            warnings.warn(f"Scan at index {spectrum.get('index', 'N/A')}: Retention time unit is missing or unrecognized ('{unit_accession}'/'{unit_name}'). Assuming minutes.")
                            scan_rt = rt_value
                        tic_rt.append(scan_rt)
                    except (ValueError, TypeError):
                         warnings.warn(f"Scan at index {spectrum.get('index', 'N/A')}: Could not parse retention time value '{rt_param.get('value')}'. Skipping scan.")
                         valid_scan = False
                else:
                     warnings.warn(f"Scan at index {spectrum.get('index', 'N/A')}: 'scan start time' (MS:1000016) cvParam missing or has no value. Skipping scan.")
                     valid_scan = False
            else:
                warnings.warn(f"Scan at index {spectrum.get('index', 'N/A')}: <scan> element missing inside <scanList>. Cannot get RT. Skipping scan.")
                valid_scan = False
        else:
            warnings.warn(f"Scan at index {spectrum.get('index', 'N/A')}: <scanList> element missing. Cannot get RT. Skipping scan.")
            valid_scan = False

        # If RT failed, skip decoding binary data for this scan
        if not valid_scan:
            invalid_ms1_count += 1
            continue

        # 3. Get m/z and Intensity arrays
        binary_data_arrays = spectrum.findall('.//mzml:binaryDataArray', ns)
        if not binary_data_arrays:
            warnings.warn(f"MS1 Scan at RT {scan_rt:.4f} (index {spectrum.get('index', 'N/A')}): No binaryDataArray elements found. Skipping scan.")
            valid_scan = False
        else:
            for bda in binary_data_arrays:
                # Check if it's the m/z array (MS:1000514)
                if find_cv_param(bda, "MS:1000514", ns) is not None:
                    if mz_array is None: # Decode only first one found
                        mz_array = decode_binary_array(bda, ns)
                        if mz_array is None:
                            warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Failed to decode m/z array. Skipping scan.")
                            valid_scan = False
                            break # Stop processing BDAs for this scan
                    else:
                         warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Found multiple m/z arrays (MS:1000514). Using the first one.")
                    continue # Check next BDA

                # Check if it's the intensity array (MS:1000515)
                if find_cv_param(bda, "MS:1000515", ns) is not None:
                    if intensity_array is None: # Decode only first one found
                        intensity_array = decode_binary_array(bda, ns)
                        if intensity_array is None:
                            warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Failed to decode intensity array. Skipping scan.")
                            valid_scan = False
                            break # Stop processing BDAs for this scan
                    else:
                         warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Found multiple intensity arrays (MS:1000515). Using the first one.")
                    # Continue checking BDAs even if intensity found, m/z might come after

        # If decoding failed for mz or intensity, skip
        if not valid_scan:
            invalid_ms1_count += 1
            continue

        # 4. Validate arrays were found and have matching lengths
        if mz_array is None or intensity_array is None:
            warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Missing m/z or intensity array after checking all binaryDataArrays. Skipping scan.")
            invalid_ms1_count += 1
            continue

        if len(mz_array) != len(intensity_array):
             warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: m/z array length ({len(mz_array)}) differs from intensity array length ({len(intensity_array)}). Skipping scan.")
             invalid_ms1_count += 1
             continue

        # 5. Store the valid data
        ms1_scans_data.append({
            'rt': scan_rt,
            'mz': mz_array,
            'intensity': intensity_array,
            # Optionally add more info if needed, e.g., spectrum index
            'index': spectrum.get('index')
        })

    # --- End of Spectrum Processing Loop ---

    print(f"\nFinished processing spectra.")
    print(f"  Total spectrum elements processed: {processed_spectra_count} (out of {total_spectra_in_list} found in list)")
    print(f"  Identified as MS1: {ms1_count}")
    print(f"  Skipped due to errors (missing data, decode fail, length mismatch): {invalid_ms1_count}")
    print(f"  Successfully extracted data for {len(ms1_scans_data)} MS1 scans.")

    # Return tuple: ( (tic_rt, tic_intensity), [list_of_ms1_scan_dicts] )
    return (tic_rt, tic_intensity), ms1_scans_data

def parse_mzml_manual_iterative(filepath, gui=None):
    """
    Parses an mzML file iteratively to extract TIC and MS1 scan data,
    suitable for large files.

    Args:
        filepath (str): Path to the mzML file.

    Returns:
        tuple: A tuple containing:
            - tic_data (tuple): (tic_rt_array, tic_intensity_array). Arrays are numpy arrays.
                                Returns (None, None) if TIC not found or decoding fails.
            - ms1_scans (list): A list of dictionaries, where each dict contains
                                'rt' (float, in minutes), 'mz' (np.array),
                                'intensity' (np.array). Returns empty list if no
                                valid MS1 scans are found.
    """
    tic_intensity = []
    tic_rt = []
    ms1_scans_data = []
    ns = {} # Namespace dictionary, will be populated
    context = None # The iterparse iterator

    # Variables to track progress/counts
    processed_spectra_count = 0
    ms1_count = 0
    invalid_ms1_count = 0
    found_tic_chromatogram = False
    spectrum_list_count = None # Store the count from spectrumList if found


    try:
        # Use iterparse, catching 'start' and 'end' events
        context = ET.iterparse(filepath, events=('start', 'end'))
        # Get the root element event to determine namespace
        event, root = next(context)

        # --- Namespace Handling at the Root ---
        namespace_uri = None
        if '}' in root.tag and root.tag.startswith('{'):
            namespace_uri = root.tag.split('}', 1)[0][1:]
            root_tag_name = root.tag # Store the full tag name like {URI}mzML
        else: # No Clark notation, check attributes
             root_tag_name = root.tag # Store the simple tag name like mzML
             if 'xmlns' in root.attrib:
                 namespace_uri = root.attrib['xmlns']
             else:
                 for key, value in root.attrib.items():
                     if key.startswith('xmlns:'):
                         namespace_uri = value
                         break

        if namespace_uri:
            ns['mzml'] = namespace_uri
            print(f"Detected mzML namespace: {namespace_uri}")
        else:
            warnings.warn(f"Could not determine namespace. Assuming standard: {DEFAULT_MZML_NAMESPACE}")
            ns['mzml'] = DEFAULT_MZML_NAMESPACE
            # If we assume a namespace, we need to assume the root tag name too for matching later
            root_tag_name = f"{{{ns['mzml']}}}mzML" # Common root tag


        # Define expected tag names using the namespace URI
        # Use ns.get('mzml', '') to handle potential empty ns dict if no fallback was used
        mzml_ns_uri = ns.get('mzml', '')
        if mzml_ns_uri:
            chromatogram_tag = f"{{{mzml_ns_uri}}}chromatogram"
            spectrum_tag = f"{{{mzml_ns_uri}}}spectrum"
            spectrum_list_tag = f"{{{mzml_ns_uri}}}spectrumList"
            binary_data_array_tag = f"{{{mzml_ns_uri}}}binaryDataArray"
            scan_list_tag = f"{{{mzml_ns_uri}}}scanList"
            scan_tag = f"{{{mzml_ns_uri}}}scan"
        else: # Handle case with no namespace (unlikely for mzML)
            chromatogram_tag = "chromatogram"
            spectrum_tag = "spectrum"
            spectrum_list_tag = "spectrumList"
            binary_data_array_tag = "binaryDataArray"
            scan_list_tag = "scanList"
            scan_tag = "scan"


        print("Starting iterative parsing...")
        # --- Main Iteration Loop ---
        for event, elem in context:

            # --- Process SpectrumList start event ---
            if event == 'start' and elem.tag == spectrum_list_tag:
                spectrum_list_count = elem.get('count')
                if spectrum_list_count:
                    print(f"Found <spectrumList count='{spectrum_list_count}'>.")
                else:
                    print("Found <spectrumList> (no count attribute).")

            # --- Process Spectrum end event ---
            elif event == 'end' and elem.tag == spectrum_tag:
                gui.increase_progress(float(1 / int(spectrum_list_count)) * 100 * processed_spectra_count)
                processed_spectra_count += 1

                # Check MS Level
                ms_level_param = find_cv_param(elem, "MS:1000511", ns)
                if ms_level_param is None or ms_level_param.get('value') != '1':
                    elem.clear() # Clear non-MS1 spectra
                    continue # Skip non-MS1

                tic_param = find_cv_param(elem, "MS:1000285", ns)
                tic_value_str = float(tic_param.get('value'))
                tic_intensity.append(tic_value_str)

                ms1_count += 1
                scan_rt = None
                mz_array = None
                intensity_array = None
                valid_scan = True

                # Get Retention Time from scanList/scan/cvParam
                scan_list = elem.find(f'.//{scan_list_tag}', ns)
                if scan_list is not None:
                    scan_element = scan_list.find(f'.//{scan_tag}', ns)
                    if scan_element is not None:
                        rt_param = find_cv_param(scan_element, "MS:1000016", ns) # scan start time
                        if rt_param is not None and rt_param.get('value') is not None:
                            try:
                                rt_value = float(rt_param.get('value'))
                                unit_acc = rt_param.get('unitAccession')
                                unit_name = rt_param.get('unitName')
                                if unit_acc == 'UO:0000031' or unit_name == 'minute':
                                    scan_rt = rt_value * 60.0 # Convert minutes to seconds
                                    tic_rt.append(scan_rt)
                                else:
                                    scan_rt = rt_value # Assume seconds otherwise (or handle other units)
                                    if not (unit_acc == 'UO:0000010' or unit_name == 'minute'):
                                         warnings.warn(f"Scan index {elem.get('index', 'N/A')}: Unknown RT unit '{unit_acc}/{unit_name}'. Assuming minutes.")
                                    tic_rt.append(scan_rt)
                            except (ValueError, TypeError):
                                warnings.warn(f"Scan index {elem.get('index', 'N/A')}: Invalid RT value '{rt_param.get('value')}'. Skipping.")
                                valid_scan = False
                        else:
                            warnings.warn(f"Scan index {elem.get('index', 'N/A')}: Missing RT cvParam (MS:1000016). Skipping.")
                            valid_scan = False
                    else:
                        warnings.warn(f"Scan index {elem.get('index', 'N/A')}: Missing <scan> element. Skipping.")
                        valid_scan = False
                else:
                    warnings.warn(f"Scan index {elem.get('index', 'N/A')}: Missing <scanList>. Skipping.")
                    valid_scan = False

                # Get m/z and Intensity arrays if RT is valid so far
                if valid_scan:
                    bda_elements = elem.findall('.//mzml:binaryDataArray', ns)
                    if not bda_elements:
                        warnings.warn(f"MS1 Scan at RT {scan_rt:.4f} (idx {elem.get('index', 'N/A')}): No binaryDataArrays found. Skipping.")
                        valid_scan = False
                    else:
                        for bda in bda_elements:
                            if mz_array is None and find_cv_param(bda, "MS:1000514", ns) is not None:
                                mz_array = decode_binary_array(bda, ns)
                                if mz_array is None:
                                    warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Failed to decode m/z array. Skipping.")
                                    valid_scan = False; break
                                continue # Found m/z, check next BDA for intensity

                            if intensity_array is None and find_cv_param(bda, "MS:1000515", ns) is not None:
                                intensity_array = decode_binary_array(bda, ns)
                                if intensity_array is None:
                                    warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Failed to decode intensity array. Skipping.")
                                    valid_scan = False; break
                                # Continue checking in case m/z array comes after intensity

                    # Final validation after checking all BDAs
                    if valid_scan:
                        if mz_array is None or intensity_array is None:
                             warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: Missing m/z or intensity array data. Skipping.")
                             valid_scan = False
                        elif len(mz_array) != len(intensity_array):
                             warnings.warn(f"MS1 Scan at RT {scan_rt:.4f}: m/z ({len(mz_array)}) and intensity ({len(intensity_array)}) array length mismatch. Skipping.")
                             valid_scan = False

                # Store data if valid
                if valid_scan:
                    ms1_scans_data.append({
                        'rt': scan_rt,
                        'mz': mz_array,
                        'intensity': intensity_array,
                        'index': elem.get('index') # Store index attribute if present
                    })
                else:
                    invalid_ms1_count += 1 # Count scans skipped due to errors

                # --- Crucial step: Clear the processed spectrum element ---
                elem.clear()


    except ET.ParseError as e:
        print(f"Error parsing XML file '{filepath}': {e}", file=sys.stderr)
        return (None, None), [] # Return empty/None on parse error
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'", file=sys.stderr)
        return (None, None), []
    except Exception as e:
        # Catch other potential errors during iteration
        print(f"An unexpected error occurred during parsing: {e}", file=sys.stderr)
        # Depending on where it happened, some data might have been collected
        # Decide whether to return partial data or fail completely
        return (tic_rt, tic_intensity), ms1_scans_data # Return potentially partial data

    finally:
        # Clean up the root element context if iterparse didn't finish naturally
        # This helps release resources if an error occurred mid-parse
        if context and hasattr(context, '_parser') and context._parser is not None:
             try:
                 # This is a bit of an internal detail access, might change between versions
                 # A safer way might just be to let Python's GC handle it when 'context' goes out of scope
                 # print("Attempting final cleanup of parser context.")
                 pass # Avoid relying on internal _parser if possible
             except Exception as cleanup_e:
                 warnings.warn(f"Exception during parser cleanup: {cleanup_e}")
        pass


    # --- Final Summary ---
    print(f"\nFinished iterative parsing.")
    if spectrum_list_count:
        print(f"  Expected spectra count from spectrumList: {spectrum_list_count}")
    print(f"  Total spectrum elements processed: {processed_spectra_count}")
    print(f"  Identified as MS1: {ms1_count}")
    print(f"  MS1 scans skipped due to errors: {invalid_ms1_count}")
    print(f"  Successfully extracted data for {len(ms1_scans_data)} MS1 scans.")


    return (tic_rt, tic_intensity), ms1_scans_data

# --- New Helper Function to reconstruct attributes with prefixes ---
def format_attributes_with_ns(attrs, ns_map_reversed):
    """
    Formats attributes, converting Clark notation back to prefixes where possible.

    Args:
        attrs (dict): Dictionary of attributes (may use Clark notation for keys).
        ns_map_reversed (dict): Dictionary mapping namespace URI back to prefix.

    Returns:
        str: Space-separated string of formatted attributes.
    """
    formatted_attrs = []
    for key, value in attrs.items():
        escaped_value = escape(value) # Escape special chars like <, &, "
        if key.startswith('{'):
            uri, localname = key.split('}', 1)
            uri = uri[1:] # Remove leading '{'
            prefix = ns_map_reversed.get(uri)
            if prefix: # Found a registered prefix
                formatted_attrs.append(f'{prefix}:{localname}="{escaped_value}"')
            else:
                # Should not happen if all namespaces were registered, but fallback:
                # Keep Clark notation (though this indicates an issue) OR skip?
                # Let's warn and skip for cleaner output, assuming registration worked.
                 warnings.warn(f"Could not find registered prefix for attribute URI '{uri}' in key '{key}'. Skipping attribute.")
                 # Alternative: Keep Clark notation (less ideal output)
                 # formatted_attrs.append(f'{key}="{escaped_value}"')
        else: # Not a namespaced attribute
             formatted_attrs.append(f'{key}="{escaped_value}"')

    return " ".join(formatted_attrs)

def filter_mzml_by_scan_id(input_filepath, output_filepath, gui, ms2_ids_to_keep, user_param_x, user_param_y):
    """
    Creates a new mzML file containing metadata, TIC, all MS1 scans,
    and specific MS2 scans from the input mzML file. Uses iterative parsing
    and attempts to preserve original namespace prefixes.

    Args:
        input_filepath (str): Path to the large input mzML file.
        output_filepath (str): Path where the filtered mzML file will be saved.
        ms2_ids_to_keep (set): A set of strings, where each string is the 'id'
                               attribute value of an MS2 scan to retain.
    """
    print(f"Starting filtering process...")
    print(f"Input file: {input_filepath}")
    print(f"Output file: {output_filepath}")
    print(f"Keeping {len(ms2_ids_to_keep)} specific MS2 scan IDs.")

    # --- Namespace storage ---
    ns_map = {}
    root_declarations = []
    ns_map_reversed = {}
    context = None
    kept_spectra_count = 0
    original_spectrum_count = None
    in_spectrum_list = False
    in_index_section = False
    processed_spectra_count = 0
    root_element = None
    root_tag_local_name = None

    # --- Indentation Settings ---
    indent_l1 = "  " # e.g., for <spectrumList>
    indent_l2 = "    " # e.g., for <spectrum>
    indent_l3 = "      " # e.g., for children of <spectrum>

    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            # Write XML declaration
            outfile.write('<?xml version="1.0" encoding="utf-8"?>\n') # Use utf-8 consistent with open()

            # Use iterparse with 'start-ns' to capture namespace declarations
            context = ET.iterparse(input_filepath, events=('start', 'end', 'start-ns'))

            root_element = None
            root_tag_local_name = None # Tag name without namespace URI

            # --- Process initial events to find root and its namespaces ---
            for event, elem in context:
                if event == 'start-ns':
                    prefix, uri = elem
                    # Store declarations found at the root level
                    if root_element is None: # Only capture those before/on the root element start
                        # Register for potential use by ET.tostring later
                        ET.register_namespace(prefix, uri)
                        # Store for writing the root tag manually
                        root_declarations.append((prefix, uri))
                        # Build maps for lookups
                        ns_map[prefix] = uri
                        ns_map_reversed[uri] = prefix

                elif event == 'start':
                    if root_element is None: # This is the root element
                        root_element = elem
                        # Extract local name (strip Clark notation if present)
                        if '}' in elem.tag and elem.tag.startswith('{'):
                             root_uri, root_tag_local_name = elem.tag.split('}', 1)
                             # Store the detected default ns if not already found by start-ns
                             if '' not in ns_map and root_uri[1:] : # and root_uri[1:] != DEFAULT_MZML_NAMESPACE :
                                  default_uri = root_uri[1:]
                                  ns_map[''] = default_uri # Clark notation implies default ns
                                  ns_map_reversed[default_uri] = ''
                                  root_declarations.append(('', default_uri))
                                  ET.register_namespace('', default_uri)
                                  print(f"Inferred default namespace from root tag: {default_uri}")

                        else: # No clark notation on root tag
                             root_tag_local_name = elem.tag
                             # Check if default xmlns attribute exists
                             if 'xmlns' in elem.attrib and '' not in ns_map:
                                default_uri = elem.attrib['xmlns']
                                ns_map[''] = default_uri
                                ns_map_reversed[default_uri] = ''
                                root_declarations.append(('', default_uri))
                                ET.register_namespace('', default_uri)
                                print(f"Found default namespace attribute: {default_uri}")


                        # --- Write the Root Element Start Tag Manually ---
                        outfile.write(f'<{root_tag_local_name}')
                        # Write namespace declarations collected
                        for prefix, uri in root_declarations:
                            if prefix:
                                outfile.write(f' xmlns:{prefix}="{escape(uri)}"')
                            else:
                                outfile.write(f' xmlns="{escape(uri)}"')
                        # Write other attributes using the helper function
                        # Exclude xmlns attributes as they are handled above
                        other_attrs = {k: v for k, v in elem.attrib.items() if not k.startswith('xmlns')}
                        if other_attrs:
                            outfile.write(f' {format_attributes_with_ns(other_attrs, ns_map_reversed)}')
                        outfile.write('>\n')

                        # Now that root is processed, break this initial loop
                        break # Move to the main processing loop
                # Skip 'end' events during this initial phase

            # --- Resume Main Parsing Loop (context continues from where we left off) ---
            # Need to get the correct mapping for 'mzml' prefix for find_cv_param
            # Usually it's the default namespace or a specific 'mzml' prefix
            # Let's prioritize the default namespace if it's the PSI standard one
            psi_uri = "http://psi.hupo.org/ms/mzml"
            if ns_map.get('') == psi_uri:
                 ns_map['mzml'] = psi_uri # Use 'mzml' key internally for find_cv_param
            elif psi_uri not in ns_map_reversed:
                 # If standard URI not found, use fallback (might be wrong ns)
                 warnings.warn(f"Standard mzML namespace '{psi_uri}' not found. Using fallback for internal lookups.")
                 ns_map['mzml'] = DEFAULT_MZML_NAMESPACE
            else:
                 # Found the standard URI with a specific prefix, ensure 'mzml' key exists
                 found_prefix = ns_map_reversed[psi_uri]
                 ns_map['mzml'] = psi_uri # Ensure 'mzml' key points to the correct URI

            mzml_uri_for_tags = ns_map.get('mzml', DEFAULT_MZML_NAMESPACE)
            spectrum_list_tag = f"{{{mzml_uri_for_tags}}}spectrumList"
            spectrum_tag = f"{{{mzml_uri_for_tags}}}spectrum"
            index_list_tag = f"{{{mzml_uri_for_tags}}}indexList"
            index_list_offset_tag = f"{{{mzml_uri_for_tags}}}indexListOffset"
            file_checksum_tag = f"{{{mzml_uri_for_tags}}}fileChecksum"
            binary_data_array_list_tag = f"{{{mzml_uri_for_tags}}}binaryDataArrayList" # Need this for fallback insertion
            cv_param_tag = f"{{{mzml_uri_for_tags}}}cvParam" # Need this for checking children

            for event, elem in context:

                # --- Skip processing anything if we are inside the index section ---
                if in_index_section and elem.tag != index_list_tag: # Allow indexList end event through
                     #elem.clear() # Clear children, but might not be needed if parent clears
                     continue
                # --- Handle START events ---
                if event == 'start':

                    # --- Check for spectrumList FIRST ---
                    if elem.tag in (index_list_tag, index_list_offset_tag, file_checksum_tag):
                        if elem.tag == index_list_tag:
                            warnings.warn("Entering <indexList> section. Skipping content.")
                            in_index_section = True  # Set flag to ignore children
                        # Do not write the start tag for these elements

                    elif elem.tag == spectrum_list_tag:
                        in_spectrum_list = True  # <<< SET FLAG HERE
                        original_spectrum_count = elem.get('count')
                        indent = "  "
                        # Write the <spectrumList> opening tag
                        local_tag = elem.tag.split('}', 1)[-1]
                        outfile.write(
                            f'{indent}<{local_tag} {format_attributes_with_ns(elem.attrib, ns_map_reversed)}>\n')
                        print(f"Processing <spectrumList> (original count: {original_spectrum_count})...")

                    # --- THEN check for other elements BEFORE spectrumList ---
                    elif elem.tag != root_element.tag and not in_spectrum_list:
                        # This handles elements like <run>, <cvList>, etc. that appear
                        # after the root tag but before <spectrumList> starts.
                        indent = "  "
                        # Write start tag, handling attributes
                        # Use local name for cleaner output
                        local_tag = elem.tag.split('}', 1)[-1]
                        outfile.write(
                            f'{indent}<{local_tag} {format_attributes_with_ns(elem.attrib, ns_map_reversed)}>\n')

                    # We don't need to explicitly handle the start of <spectrum> or other elements
                    # inside <spectrumList> here, as they are processed at their 'end' event.

                # --- Handle END events ---
                elif event == 'end':
                    # ... (rest of the 'end' event logic remains the same) ...

                    # 1. Is it the root element? (This is the absolute last end tag)
                    if elem.tag == root_element.tag:
                        outfile.write(f'</{root_tag_local_name}>\n')
                        # Optional: clear root if needed, though script ends here
                        # elem.clear()

                    # 2. Is it the end of indexList section or related tags?
                    elif elem.tag in (index_list_tag, index_list_offset_tag, file_checksum_tag):
                        if elem.tag == index_list_tag:
                            in_index_section = False # Reset flag
                            warnings.warn("Exiting and clearing skipped <indexList> section.")
                        # warnings.warn(f"Clearing skipped footer element: {elem.tag.split('}',1)[-1]}")
                        elem.clear() # Clear the element, DO NOT write closing tag

                    # --- Process elements based on whether we are inside spectrumList ---
                    elif in_spectrum_list:  # <<< THIS CHECK NOW WORKS
                        if elem.tag == spectrum_tag:
                            processed_spectra_count += 1  # Moved count here for accuracy
                            keep = False
                            ms_level_param = find_cv_param(elem, "MS:1000511", ns_map)  # Use ns_map here
                            scan_id = elem.get('index')
                            scan_id = scan_id.removeprefix('scan=')

                            # ... (logic to decide if 'keep = True' based on MS level and ID) ...
                            if ms_level_param is not None:
                                ms_level = ms_level_param.get('value')
                                if ms_level == '1':
                                    keep = False
                                elif ms_level == '2' and scan_id in ms2_ids_to_keep:
                                    keep = True
                            else:
                                warnings.warn(
                                    f"Spectrum index {elem.get('index', 'N/A')} (id: {scan_id}) has no MS level. Discarding.")

                            if keep:
                                gui.increase_progress(
                                    float(1 / int(len(ms2_ids_to_keep))) * 100 * kept_spectra_count)
                                kept_spectra_count += 1
                                add_params = True

                                index = ms2_ids_to_keep.index(scan_id)
                                x_value = user_param_x[index]
                                y_value = user_param_y[index]
                                up_elem_x = ET.Element('userParam', {'name': 'x_position', 'value': str(x_value)})
                                up_elem_y = ET.Element('userParam', {'name': 'y_position', 'value': str(y_value)})


                                # --- *** START Manual Spectrum Serialization *** ---
                                local_spec_tag = elem.tag.split('}', 1)[-1]
                                outfile.write(f'{indent_l2}<{local_spec_tag} {format_attributes_with_ns(elem.attrib, ns_map_reversed)}>\n')

                                inserted_user_params = False # Flag to track if params were inserted
                                target_cvparam_found = False # Flag to track if target was found

                                # Iterate through children (scanList, precursorList, cvParams, binaryDataArrayList etc.)
                                for child in elem:
                                    # Write the current child element
                                    try:
                                        child_xml_string = ET.tostring(child, encoding='unicode', method='xml')
                                        outfile.write(f'{indent_l3}{child_xml_string.strip()}\n')
                                    except Exception as serial_e:
                                        warnings.warn(
                                            f"Error serializing child {child.tag} in spectrum {scan_id}: {serial_e}")
                                        continue  # Skip this child if serialization fails

                                    # Check if this child is the target cvParam for insertion
                                    if add_params and not inserted_user_params and \
                                            child.tag == cv_param_tag and child.get(
                                        'accession') == TARGET_CVPARAM_ACCESSION:
                                        target_cvparam_found = True
                                        # Insert user params AFTER this target
                                        try:
                                            up_xml_string_x = ET.tostring(up_elem_x, encoding='unicode', method='xml')
                                            outfile.write(f'{indent_l3}{up_xml_string_x.strip()}\n')
                                            up_xml_string_y = ET.tostring(up_elem_y, encoding='unicode', method='xml')
                                            outfile.write(f'{indent_l3}{up_xml_string_y.strip()}\n')
                                        except Exception as serial_e:
                                            warnings.warn(
                                                f"Error serializing userParams in spectrum {scan_id}: {serial_e}")
                                        inserted_user_params = True  # Mark as inserted

                                    # Fallback: Insert before binaryDataArrayList if target wasn't found yet
                                    if add_params and not inserted_user_params and not target_cvparam_found and \
                                            child.tag == binary_data_array_list_tag:
                                        warnings.warn(
                                            f"Target CV {TARGET_CVPARAM_ACCESSION} not found before <binaryDataArrayList> in scan {scan_id}. Inserting userParams now.")

                                        try:
                                            up_xml_string_x = ET.tostring(up_elem_x, encoding='unicode', method='xml')
                                            outfile.write(f'{indent_l3}{up_xml_string_x.strip()}\n')
                                            up_xml_string_y = ET.tostring(up_elem_y, encoding='unicode', method='xml')
                                            outfile.write(f'{indent_l3}{up_xml_string_y.strip()}\n')
                                        except Exception as serial_e:
                                            warnings.warn(
                                                f"Error serializing userParams in spectrum {scan_id}: {serial_e}")
                                        inserted_user_params = True  # Mark as inserted (before binary list)

                                # Fallback: If user params should be added but weren't inserted yet (e.g., no target, no binary list)
                                if add_params and not inserted_user_params:
                                    warnings.warn(
                                        f"Target CV {TARGET_CVPARAM_ACCESSION} and <binaryDataArrayList> not found in scan {scan_id}. Appending userParams at the end.")


                                    try:
                                        up_xml_string_x = ET.tostring(up_elem_x, encoding='unicode', method='xml')
                                        outfile.write(f'{indent_l3}{up_xml_string_x.strip()}\n')
                                        up_xml_string_y = ET.tostring(up_elem_y, encoding='unicode', method='xml')
                                        outfile.write(f'{indent_l3}{up_xml_string_y.strip()}\n')
                                    except Exception as serial_e:
                                        warnings.warn(
                                            f"Error serializing userParams in spectrum {scan_id}: {serial_e}")

                                # Write the closing spectrum tag
                                outfile.write(f'{indent_l2}</{local_spec_tag}>\n')
                                # --- *** END Manual Spectrum Serialization *** ---

                            elem.clear()  # Clear element AFTER processing

                        # 3b. Is it the end of the spectrum list itself?
                        elif elem.tag == spectrum_list_tag:
                            local_tag = elem.tag.split('}', 1)[-1]
                            outfile.write(f'{indent_l1}</{local_tag}>\n') # Close spectrumList
                            in_spectrum_list = False # Update flag
                            print(f"Finished processing <spectrumList>. Processed {processed_spectra_count} spectra within it.")
                            elem.clear() # Clear spectrumList element


                    # 4. Handle end tags for elements OUTSIDE spectrumList
                    # (and not root or indexList)
                    else:
                        # This handles </cvList>, </fileDescription>, </softwareList>, </run>, </chromatogramList> etc.
                        local_tag = elem.tag.split('}', 1)[-1]
                        # Assume they are children of root or run -> use indent_l1
                        outfile.write(f'{indent_l1}</{local_tag}>\n')
                        elem.clear()  # Clear the element

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'", file=sys.stderr)
        return False
    except ET.ParseError as e:
        print(f"Error parsing input XML file '{input_filepath}': {e}", file=sys.stderr)
        # Clean up potentially incomplete output file
        if os.path.exists(output_filepath): os.remove(output_filepath)
        return False
    except IOError as e:
         print(f"Error writing to output file '{output_filepath}': {e}", file=sys.stderr)
         return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        # Clean up potentially incomplete output file
        if os.path.exists(output_filepath): os.remove(output_filepath)
        return False


    print("\nFiltering process completed.")
    print(f"Total spectra kept: {kept_spectra_count}")
    if original_spectrum_count:
        print(f"Original file reported {original_spectrum_count} spectra in <spectrumList>.")
        if str(kept_spectra_count) != original_spectrum_count:
             warnings.warn(f"The 'count' attribute ({original_spectrum_count}) in the output file's <spectrumList> tag does not match the actual number of spectra written ({kept_spectra_count}). Most tools will ignore this attribute.")
    else:
         warnings.warn("Could not read original spectrum count.")

    return True






def filter_and_annotate_mzml(input_filepath, output_filepath, ms2_scan_ids, x_positions, y_positions):
    """
    Parses an input mzML file iteratively, filters for specific MS2 scans based on their
    spectrum 'id' attribute, removes all MS1 scans, adds x/y position userParams
    to the kept MS2 scans, and writes the result to a new mzML file, preserving
    structure and formatting as much as possible.
    (Args and Raises descriptions remain the same)
    """

    # 1. Input Validation (remains the same)
    if not os.path.exists(input_filepath):
        raise FileNotFoundError(f"Input file not found: {input_filepath}")
    if not (len(ms2_scan_ids) == len(x_positions) == len(y_positions)):
        raise ValueError("Input lists ('ms2_scan_ids', 'x_positions', 'y_positions') must have the same length.")
    print(f"Input file: {input_filepath}")
    print(f"Output file: {output_filepath}")
    print(f"Number of MS2 scan IDs provided: {len(ms2_scan_ids)}")

    # 2. Prepare annotation lookup dictionary (remains the same)
    scan_annotations = { str(scan_id): (x, y) for scan_id, x, y in zip(ms2_scan_ids, x_positions, y_positions) }
    print(f"Created annotation lookup for {len(scan_annotations)} unique scan IDs.")
    if len(scan_annotations) != len(ms2_scan_ids):
         warnings.warn("Duplicate scan IDs detected. Only the last occurrence's annotation will be used.")

    # 3. Iterative Parsing and Writing Setup (remains the same)
    ns = {}
    ns_prefix_map_for_writing = {}
    default_namespace_uri = None
    context = None
    written_spectrum_count = 0
    mzml_ns_uri = ""
    root_tag_clark = ""
    spectrum_list_tag_clark = "spectrumList"
    spectrum_tag_clark = "spectrum"
    scan_tag_clark = "scan"
    scan_list_tag_clark = "scanList"

    print("Starting iterative parsing and writing...")
    try:
        with open(output_filepath, 'wb') as outfile:
            outfile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            context = ET.iterparse(input_filepath, events=('start', 'end', 'start-ns', 'end-ns'))

            current_element_depth = 0
            in_spectrum_list = False
            in_spectrum_element = False
            skip_current_spectrum = False
            spectrum_buffer = []
            spectrum_list_attrs_str = ""
            spectrum_list_tag_local = "spectrumList"

            for event, elem_or_ns in context:
                # Namespace Handling ('start-ns', 'end-ns') - No changes needed
                if event == 'start-ns':
                    prefix, uri = elem_or_ns
                    if prefix:
                        ns[prefix] = uri
                        ns_prefix_map_for_writing[uri] = prefix
                        if uri == DEFAULT_MZML_NAMESPACE and prefix == 'mzml': mzml_ns_uri = uri
                    else:
                        default_namespace_uri = uri
                        if uri == DEFAULT_MZML_NAMESPACE: mzml_ns_uri = uri
                        ns_prefix_map_for_writing[uri] = ""
                elif event == 'end-ns': pass

                # Element Start Handling ('start')
                elif event == 'start':
                    elem = elem_or_ns
                    current_element_depth += 1

                    # --- Define Namespaced Tags (once mzml_ns_uri is known) ---
                    if not root_tag_clark and current_element_depth == 1:
                        # (Logic to determine namespace and define *_tag_clark variables remains the same)
                        root_tag_clark = elem.tag
                        if not mzml_ns_uri:
                            if default_namespace_uri == DEFAULT_MZML_NAMESPACE: mzml_ns_uri = default_namespace_uri
                            elif '}' in elem.tag and elem.tag.startswith('{'):
                                uri = elem.tag.split('}', 1)[0][1:]
                                if uri == DEFAULT_MZML_NAMESPACE: mzml_ns_uri = uri
                        if not mzml_ns_uri:
                            warnings.warn(f"Could not definitively identify mzML namespace. Assuming standard: {DEFAULT_MZML_NAMESPACE}")
                            mzml_ns_uri = DEFAULT_MZML_NAMESPACE
                        spectrum_list_tag_clark = f"{{{mzml_ns_uri}}}spectrumList" if mzml_ns_uri else "spectrumList"
                        spectrum_tag_clark = f"{{{mzml_ns_uri}}}spectrum" if mzml_ns_uri else "spectrum"
                        scan_tag_clark = f"{{{mzml_ns_uri}}}scan" if mzml_ns_uri else "scan"
                        scan_list_tag_clark = f"{{{mzml_ns_uri}}}scanList" if mzml_ns_uri else "scanList"
                        print(f"Identified mzML Namespace: '{mzml_ns_uri}'")
                        print(f"Root Element: {root_tag_clark}")

                    # --- Construct attributes string with CORRECTED escape ---
                    attrs = ' '.join([f'{k}="{xml.sax.saxutils.escape(v)}"' for k, v in elem.attrib.items()]) # <-- FIX HERE

                    # --- Special Handling for <spectrumList> ---
                    if elem.tag == spectrum_list_tag_clark:
                        in_spectrum_list = True
                        spectrum_list_tag_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        # --- Use CORRECTED escape for attributes here too ---
                        spectrum_list_attrs_str = ' '.join([f'{k}="{xml.sax.saxutils.escape(v)}"' for k, v in elem.attrib.items() if k != 'count']) # <-- FIX HERE
                        # Do not write the tag yet

                    # --- Special Handling for <spectrum> ---
                    elif elem.tag == spectrum_tag_clark and in_spectrum_list:
                        in_spectrum_element = True
                        skip_current_spectrum = False
                        spectrum_buffer = []

                        # Filtering Decision (remains the same)
                        is_ms1, is_ms2 = False, False
                        ms_level_cv = find_cv_param(elem, "MS:1000511", {'mzml': mzml_ns_uri})
                        if ms_level_cv is not None:
                            level_val = ms_level_cv.get('value')
                            if level_val == '1': is_ms1 = True
                            elif level_val == '2': is_ms2 = True
                        if is_ms1: skip_current_spectrum = True
                        elif is_ms2:
                            scan_id = elem.get('id')
                            scan_id = scan_id.removeprefix('scan=')
                            if not scan_id or scan_id not in scan_annotations: skip_current_spectrum = True
                        else: skip_current_spectrum = True

                        # Buffering kept spectrum start tag
                        if not skip_current_spectrum:
                            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                            start_tag = f"<{tag_name}" + (f" {attrs}" if attrs else "") + ">"
                            spectrum_buffer.append(start_tag.encode('utf-8'))
                            # Handle text content using CORRECTED escape
                            if elem.text and elem.text.strip():
                                 spectrum_buffer.append(xml.sax.saxutils.escape(elem.text.strip()).encode('utf-8')) # <-- FIX HERE

                    # --- Default: Write other tags ---
                    elif not in_spectrum_element:
                         if not in_spectrum_list: # Write header tags immediately
                            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                            outfile.write(f"<{tag_name}".encode('utf-8'))
                            if attrs: outfile.write(f" {attrs}".encode('utf-8'))
                            outfile.write(b'>\n')
                            # Handle text content using CORRECTED escape
                            if elem.text and elem.text.strip():
                                outfile.write(xml.sax.saxutils.escape(elem.text.strip()).encode('utf-8')) # <-- FIX HERE
                                outfile.write(b'\n')

                    # --- Buffering within kept spectra ---
                    elif in_spectrum_element and not skip_current_spectrum:
                        tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        start_tag = f"<{tag_name}" + (f" {attrs}" if attrs else "") + ">"
                        spectrum_buffer.append(start_tag.encode('utf-8'))
                        # Handle text content using CORRECTED escape
                        if elem.text and elem.text.strip():
                                 spectrum_buffer.append(xml.sax.saxutils.escape(elem.text.strip()).encode('utf-8')) # <-- FIX HERE

                # Element End Handling ('end')
                elif event == 'end':
                    elem = elem_or_ns
                    tag_name_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                    # --- Write/Process Spectrum on End Tag ---
                    if elem.tag == spectrum_tag_clark and in_spectrum_list:
                        # (Logic for annotation, insertion, and writing buffer remains the same)
                        if not skip_current_spectrum:
                            scan_id = elem.get('id')
                            scan_id = scan_id.removeprefix('scan=')
                            x_pos, y_pos = scan_annotations[scan_id]
                            x_param_str = f'<userParam name="x_position" type="xsd:float" value="{str(x_pos)}"/>'
                            y_param_str = f'<userParam name="y_position" type="xsd:float" value="{str(y_pos)}"/>'

                            insert_pos = -1
                            scan_tag_local = scan_tag_clark.split('}')[-1] if '}' in scan_tag_clark else scan_tag_clark
                            scan_list_tag_local = scan_list_tag_clark.split('}')[-1] if '}' in scan_list_tag_clark else scan_list_tag_clark

                            for i in range(len(spectrum_buffer) - 1, -1, -1):
                                line = spectrum_buffer[i].decode('utf-8').strip()
                                if line == f"</{scan_tag_local}>" or line == f"</{scan_list_tag_local}>":
                                    insert_pos = i + 1
                                    break
                                elif line.startswith(f"<{scan_tag_local}") or line.startswith(f"<{scan_list_tag_local}"):
                                     break

                            if insert_pos != -1:
                                spectrum_buffer.insert(insert_pos, y_param_str.encode('utf-8'))
                                spectrum_buffer.insert(insert_pos, x_param_str.encode('utf-8'))
                            else:
                                warnings.warn(f"Could not find suitable insertion point for userParams in spectrum id='{scan_id}'. Appending before </spectrum>.")
                                spectrum_buffer.append(x_param_str.encode('utf-8'))
                                spectrum_buffer.append(y_param_str.encode('utf-8'))

                            spectrum_buffer.append(f"</{tag_name_local}>".encode('utf-8'))

                            for line_bytes in spectrum_buffer:
                                outfile.write(line_bytes)
                                outfile.write(b'\n')

                            written_spectrum_count += 1
                            if written_spectrum_count % 1000 == 0: print(f"  ... wrote spectrum {written_spectrum_count}")
                            spectrum_buffer = []
                            elem.clear()

                        in_spectrum_element = False
                        skip_current_spectrum = False

                    # --- Write SpectrumList End Tag ---
                    elif elem.tag == spectrum_list_tag_clark:
                        # Write the stored <spectrumList> START tag now, with correct count
                        outfile.write(f"<{spectrum_list_tag_local}".encode('utf-8'))
                        if spectrum_list_attrs_str: outfile.write(f" {spectrum_list_attrs_str}".encode('utf-8'))
                        outfile.write(f' count="{written_spectrum_count}"'.encode('utf-8'))  # Add correct count
                        outfile.write(b'>\n')  # Close start tag

                        # Write the closing tag for spectrumList
                        outfile.write(f"</{spectrum_list_tag_local}>\n".encode('utf-8'))
                        in_spectrum_list = False  # Reset flag

                    # *** --- ADD CLOSING TAGS FOR BUFFERED ELEMENTS --- ***
                    elif in_spectrum_element and not skip_current_spectrum:
                        # This 'end' event is for an element INSIDE a spectrum we are keeping.
                        # Add its closing tag to the buffer.
                        spectrum_buffer.append(f"</{tag_name_local}>".encode('utf-8'))
                        # Also add tail text if present (text after the closing tag)
                        if elem.tail and elem.tail.strip():
                            spectrum_buffer.append(xml.sax.saxutils.escape(elem.tail.strip()).encode('utf-8'))


                    # --- Write closing tags for non-spectrum, non-buffered elements ---
                    elif not in_spectrum_element and not in_spectrum_list:
                        # These are header/footer elements written directly
                        outfile.write(f"</{tag_name_local}>\n".encode('utf-8'))
                        # Handle tail text for these elements
                        if elem.tail and elem.tail.strip():
                            outfile.write(xml.sax.saxutils.escape(elem.tail.strip()).encode('utf-8'))
                            outfile.write(b'\n')

                    # --- Clear element to free memory ---
                    if elem.tag != spectrum_tag_clark or skip_current_spectrum:
                         try: elem.clear()
                         except Exception: pass

                    current_element_depth -= 1

            # --- End of loop ---
            print(f"\nFinished processing input file.")
            print(f"Total MS2 spectra written to output: {written_spectrum_count}")

    # Error handling and finally block remain the same
    except ET.ParseError as e:
        print(f"Error parsing XML file '{input_filepath}' at line ~{e.position[0]}: {e}", file=sys.stderr)
        raise
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'", file=sys.stderr)
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        raise
    finally:
        context = None









# --- Example Usage ---
if __name__ == "__main__":
    # Default file path (can be changed)
    default_mzml_file = '20250403_ChiBa3_1_LockmassCorr.mzML' # <--- CHANGE THIS or provide path via command line

    mzml_file_path = None

    # Check if a file path was provided as a command-line argument
    if len(sys.argv) > 1:
        mzml_file_path = sys.argv[1]
        print(f"Using mzML file provided as argument: {mzml_file_path}")
        if not os.path.exists(mzml_file_path):
             print(f"Error: Provided file path does not exist: '{mzml_file_path}'")
             sys.exit(1)
    else:
        print(f"No command-line argument provided. Using default path: '{default_mzml_file}'")
        if not os.path.exists(default_mzml_file):
            print(f"Error: Default file '{default_mzml_file}' not found.")
            print("Please change the default path in the script or provide the path as a command-line argument:")
            # Use os.path.basename to show just the script name
            script_name = os.path.basename(__file__)
            print(f"Example: python {script_name} /path/to/your/file.mzML")
            sys.exit(1)
        mzml_file_path = default_mzml_file

    # Call the main parsing function
    print(f"\nStarting mzML parsing for: {mzml_file_path}")
    #filter_and_annotate_mzml(input_filepath=mzml_file_path, output_filepath='output.mzML', ms2_scan_ids=['2','4','6','8','10'], x_positions=[2,4,6,8,10], y_positions=[2,4,6,8,10])
    filter_mzml_by_scan_id(input_filepath=mzml_file_path, output_filepath='output.mzML', gui=None, ms2_ids_to_keep=['2','4','6','8','10'], user_param_x=[2,4,6,8,10], user_param_y=[2,4,6,8,10])
    print("\nParsing complete.")

