from GrannanLabCore.GrannanLabNWB import GrannanLabNWB
from pynwb.file import Subject
import pandas as pd
import numpy as np
import re
import os


class forage2dNWB(GrannanLabNWB):

    def __init__(self, subject_id, device_name, 
                electrodes_info_path=None,
                board_parameters_path=None,
                fixations_path=None,
                trial_data_path=None,
                triggers_path=None,
                *args, **kwargs):
        super(forage2dNWB, self).__init__(*args, **kwargs)
        self.subject = Subject(subject_id=subject_id)
        self.device = self.create_device(name=device_name)
        self.electrodes_info_path = electrodes_info_path
        if electrodes_info_path is not None:
            self.set_electrodes_info(electrodes_info_path)
        self.board_parameters_path = board_parameters_path
        self.fixations_path = fixations_path
        self.trial_data_path = trial_data_path
        self.triggers_path = triggers_path

    def get_events_dataframe(self): 
        return

    def set_events_table(self):
        return

    def _process_event_text_files(self):
        return

    def align_time_with_triggers(self):
        return

    def load_ephys(self):

        # create table region (link for ephys and electrode_table)
        table_region_ = self.create_electrode_table_region(
            region=list(range(self.electrodes.to_dataframe().shape[0])),  # reference row indices 0 to N-1
            description="all electrodes",
            )

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
                board_parameters_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_board_parameters.txt",
                fixations_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_fixations.txt",
                trial_data_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_trial_data.txt",
                triggers_path = "/data/EMU_Data/c39f4a/behavior/" + \
                    "forage2d/c39f4a-2023-8_14-17-57-1_triggers.txt",
                )
    
    ff.set_electrode_table()