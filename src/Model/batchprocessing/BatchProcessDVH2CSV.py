import os
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess
import pandas as pd
from pathlib import Path


class BatchProcessDVH2CSV(BatchProcess):
    """
    This class handles batch processing for the DVH2CSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for ISO2ROI
    allowed_classes = {
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        },
        # RT Dose
        "1.2.840.10008.5.1.4.1.1.481.2": {
            "name": "rtdose",
            "sliceable": False
        },
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files,
                 output_path):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param output_path: output of the resulting .csv file.
        """
        # Call the parent class
        super(BatchProcessDVH2CSV, self).__init__(progress_callback,
                                                  interrupt_flag,
                                                  patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('rtss', 'rtdose')
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = output_path
        self.filename = "DVHs_.csv"

    def start(self):
        """
        Goes through the steps of the ISO2ROI conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return

        # Check if the dataset is complete
        self.progress_callback.emit(("Checking dataset...", 40))

        # Attempt to get DVH data from RT Dose
        # TODO: implement this once DVH2RTDOSE in main repo
        #self.progress_callback.emit(("Attempting to get DVH from RT Dose...",
        #                             50))

        # Calculate DVH if not in RT Dose
        self.progress_callback.emit(("Calculating DVH...", 60))
        read_data_dict = self.patient_dict_container.dataset
        dataset_rtss = self.patient_dict_container.dataset['rtss']
        dataset_rtdose = self.patient_dict_container.dataset['rtdose']
        rois = self.patient_dict_container.get("rois")
        try:
            dict_thickness = ImageLoading.get_thickness_dict(dataset_rtss,
                                                         read_data_dict)
            raw_dvh = ImageLoading.calc_dvhs(dataset_rtss,
                                             dataset_rtdose,
                                             rois,
                                            dict_thickness,
                                             self.interrupt_flag)
        except TypeError:
            print("Error when calculating ROI thickness. The dataset may be "
                  "incomplete. \nSkipping DVH2CSV.")
            return

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        # Export DVH to CSV
        self.progress_callback.emit(("Exporting DVH to CSV...", 90))

        # Get path to save to
        path = Path.joinpath(self.output_path, 'CSV')

        # Get patient ID
        patient_id = self.patient_dict_container.dataset['rtss'].PatientID

        # Make CSV directory if it doesn't exist
        if not os.path.isdir(path):
            os.mkdir(path)

        # Save the DVH to a CSV file
        self.dvh2csv(raw_dvh, path, self.filename, patient_id)

    def dvh2csv(self, dict_dvh, path, csv_name, patient_id):
        """
        Export dvh data to csv file.
        Append to existing file

        :param dict_dvh: A dictionary of DVH {ROINumber: DVH}
        :param path: Target path of CSV export
        :param csv_name: CSV file name
        :param patient_id: Patient Identifier
        """
        # full path of the target csv file
        tar_path = Path.joinpath(path, csv_name)

        create_header = not os.path.isfile(tar_path)

        dvh_csv_list = []

        csv_header = []
        csv_header.append('Patient ID')
        csv_header.append('ROI')
        csv_header.append('Volume (mL)')

        max_roi_dose = 0

        for i in dict_dvh:
            dvh_roi_list = []
            dvh = dict_dvh[i]
            name = dvh.name
            volume = dvh.volume
            dvh_roi_list.append(patient_id)
            dvh_roi_list.append(name)
            dvh_roi_list.append(volume)
            dose = dvh.relative_volume.counts

            for i in range(0, len(dose), 10):
                dvh_roi_list.append(dose[i])
                # Update the maximum dose value, if current dose
                # exceeds the current maximum dose
                if i > max_roi_dose:
                    max_roi_dose = i

            dvh_csv_list.append(dvh_roi_list)

        for i in range(0, max_roi_dose + 1, 10):
            csv_header.append(str(i) + 'cGy')

        # Convert the list into pandas dataframe, with 2 digit rounding.
        pddf_csv = pd.DataFrame(dvh_csv_list, columns=csv_header).round(2)
        # Fill empty blocks with 0.0
        pddf_csv.fillna(0.0, inplace=True)
        pddf_csv.set_index('Patient ID', inplace=True)
        # Convert and export pandas dataframe to CSV file
        pddf_csv.to_csv(tar_path, mode='a', header=create_header)

    def set_filename(self, name):
        if name != '':
            self.filename = name
        else:
            self.filename = "DVHs_.csv"
