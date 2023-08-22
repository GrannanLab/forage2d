from GrannanLabCore.GrannanLabNWB import GrannanLabNWB
from pynwb.file import Subject
from pynwb.ecephys import ElectricalSeries
from pynwb import NWBHDF5IO
import pandas as pd
import numpy as np
import re
import os


class forage2dNWB(GrannanLabNWB):

    def __init__(self, subject_id, device_name, 
                electrodes_info_path=None,
                ephys_data_path=None,
                board_parameters_path=None,
                fixations_path=None,
                trial_data_path=None,
                triggers_path=None,
                nwb_file_path=None,
                *args, **kwargs):
        super(forage2dNWB, self).__init__(*args, **kwargs)
        self.subject = Subject(subject_id=subject_id)
        self.device = self.create_device(name=device_name)
        self.electrodes_info_path = electrodes_info_path
        if electrodes_info_path is not None:
            self.set_electrodes_info(electrodes_info_path)
        self.ephys_data_path = ephys_data_path
        self.board_parameters_path = board_parameters_path
        self.fixations_path = fixations_path
        self.trial_data_path = trial_data_path
        self.triggers_path = triggers_path
        self.nwb_path = nwb_file_path

    def get_events_dataframe(self): 
        return

    def set_events_table(self):
        return

    def _process_event_text_files(self):
        return

    def align_time_with_triggers(self):
        return

    def load_ephys(self, path):

        df = self.electrodes.to_dataframe()
        # create one table region per values of electrode location column
        for i in df.index:

            contact = int(df.loc[i,'Contact'])            
            
            # generate table region (for linking DynamicTable)
            table_region = self.create_electrode_table_region(
                region=[i],  # reference row indices 0 to N-1
                description=df.loc[i, 'Label'],
                )

            # load csv file for the ephys data for these electrodes
            data = np.loadtxt(os.path.join(self.ephys_data_path,
                            df.loc[i, 'location']+'.csv'), 
                            delimiter=',', dtype=int)[:,contact-1]

            # get sampling freq
            if re.match('m_', df.loc[i, 'location']):
                sampling_fq = 32000.0
            else:
                sampling_fq = 4000.0

            elec_series = ElectricalSeries(
                name="Raw_{}".format(df.loc[i, 'Label']),
                data=data,
                electrodes=table_region,
                starting_time=0.0,
                rate=sampling_fq,
            )

            self.add_acquisition(elec_series)

            print("ElectricalSeries {} loaded.".format(df.loc[i, 'Label']))


if __name__ == '__main__':

    from datetime import datetime
    from dateutil import tz
    from uuid import uuid4

    ff = forage2dNWB(subject_id = "c39f4a",
                device_name = "Neuralynx_Atlas",                    
                session_description="forage2d",
                identifier = str(uuid4()),
                session_start_time = datetime(2025, 3, 9, 
                                              tzinfo=tz.gettz('US/Pacific')),
                session_id = 'OneShot',
                experimenter = 'Sophia Lowe-Hines',
                lab = 'Grannan Lab',
                institution = 'University of Washington',
                electrodes_info_path = "/data/EMU_Data/c39f4a/electrodes/" + \
                    "c39f4a_sEEG_trodes_info.xlsx",
                ephys_data_path = "/data/EMU_Data/c39f4a/neural/forage2d/csv/", 
                board_parameters_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_board_parameters.txt",
                fixations_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_fixations.txt",
                trial_data_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_trial_data.txt",
                triggers_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_triggers.txt",
                nwb_file_path = "/data/EMU_Data/c39f4a/nwb/"
                )
    
    ff.set_electrode_table()

    nwb_file_path = os.path.join(ff.nwb_path, 
                                "{}_{}.nwb".format(ff.subject.subject_id, 
                                ff.session_description))

    ff.load_ephys(nwb_file_path)
    with NWBHDF5IO(nwb_file_path, 'w') as io:
        io.write(ff)

    print('done!')