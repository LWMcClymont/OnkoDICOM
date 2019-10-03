"""
./src/Model/LoadPatients.py
This file contains basic functions for loading original dicom files.
The output returned consists of two dictionaries, one contains the
file paths of read files and the other the data obtained from each file
after reading the data.
"""

import glob
import re
import logging
import pydicom
import os
from PyQt5 import QtCore, QtWidgets


# For sorting dicom file names by numbers
# Input is a list of dcm file names.
# Return the sorted list of all file names.
def natural_sort(file_list):
    # Logger info
    print('Natural Sorting...')
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(file_list, key=alphanum_key)


# 
def get_datasets(path):
    """
    :param path: str
    :return read_data_dict: dict
    :return file_names_dict: dict
    """

    # Data contains data read from files
    # Key is int for ct images and str (rtdose, rtss, rtplan) for RT files
    read_data_dict = {}

    # Data contains file paths
    # Key is int for ct images and str (rtdose, rtss, rtplan) for RT files
    file_names_dict = {}

    # Sort files based on name
    dcm_files = natural_sort(glob.glob(path + '/*'))
    i = 0  # For key values for ct images

    # For each file in path
    for file in dcm_files:
        # If file exists and the first two letters in the name are CT, RD, RP, RS, or RT
        if os.path.isfile(file) and os.path.basename(file)[0:2].upper() in ['CT', 'RD', 'RP', 'RS', 'RT']:
            try:
                read_file = pydicom.dcmread(file)
            except:
                print('ERROR: Cannot read file ' + file)
            else:
                if read_file.Modality == 'CT':
                    read_data_dict[i] = read_file
                    file_names_dict[i] = file
                    i += 1
                elif read_file.Modality == 'RTSTRUCT':
                    read_data_dict['rtss'] = read_file
                    file_names_dict['rtss'] = file
                elif read_file.Modality == 'RTDOSE':
                    read_data_dict['rtdose'] = read_file
                    file_names_dict['rtdose'] = file
                elif read_file.Modality == 'RTPLAN':
                    read_data_dict['rtplan'] = read_file
                    file_names_dict['rtplan'] = file

    return read_data_dict, file_names_dict

if __name__ == '__main__':
    file = '/home/sohaib/992/test'
    get_datasets(file)
