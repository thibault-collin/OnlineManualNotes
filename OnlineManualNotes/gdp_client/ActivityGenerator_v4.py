from comm.IActivityGenerator import IActivityGenerator
import json
from xml.etree.ElementTree import Element
from . import waveform_generator as wfm
import numpy as np
import copy


class ActivityGenerator_v4(IActivityGenerator):
    def __init__(self):
        super().__init__()

        """
        map number of enabled waveforms to enables binary positions
        

        self.enables_lut = [
            '0000000000',
            '1000000000',
            '1100000000',
            '1110000000',
            '1111000000'
        ]
        """

    def create_current_waveforms_json(self,waveforms, amplitudes,frequency,offset,ramping,pulses):
        """
        Can input either a single waveform and a single amplitude, or an equal sized
        list of each

        Output is json format Waveforms which will be serialised to make up part of
        a http request
        """
        waveforms_list = []
        Rows_list = []
        waveforms_count = 0
        if isinstance(waveforms, list) and isinstance(amplitudes, list):
            if (len(waveforms) != len(amplitudes)):
                raise Exception("Waveforms and amplitudes lists do not match")
            for waveform, amplitude, freq, off, ramp, puls in zip(waveforms, amplitudes, frequency, offset, ramping,
                                                                  pulses):
                waveforms_count = waveforms_count + 1
                current_waveform = {}

                current_waveform['Name'] = waveform.name
                current_waveform['Electrodes'] = waveform.electrode_config
                if not np.isnan(waveform.lead_number):
                    current_waveform['LeadNum'] = int(waveform.lead_number)
                if amplitude - 0 < 1e-6:#assumption that an amp == 0 if the same as an empty segment in GDP time mapping
                    current_row = []
                else:
                    current_row = {}
                    current_row['WaveformIndex'] = waveforms_count - 1
                    current_row['Amplitude'] = amplitude
                    current_row['FrequencyPeriod'] = int(1e6 / freq)
                    current_row['FrequencyOffset'] = int(off)
                    current_row['Ramping'] = ramp
                    current_row['Pulses'] = int(puls)
                
                waveforms_list.append(current_waveform)
                Rows_list.append(current_row)

        elif isinstance(waveforms, wfm.Waveform):
            waveforms_count = waveforms_count + 1
            current_waveform = {}
            current_waveform['Name'] = waveforms.name
            current_waveform['Electrodes'] = waveforms.electrode_config
            if not np.isnan(waveforms.lead_number):
                current_waveform['LeadNum'] = int(waveforms.lead_number)

            if amplitudes - 0 < 1e-6:#assumption that an amp == 0 if the same as an empty segment in GDP time mapping
                current_row = []
            else:
                current_row = {}
                current_row['WaveformIndex'] = waveforms_count - 1
                current_row['Amplitude'] = amplitudes
                current_row['FrequencyPeriod'] = int(1e6 / frequency)
                current_row['FrequencyOffset'] = int(offset)
                current_row['Ramping'] = ramping
                current_row['Pulses'] = int(pulses)

            waveforms_list.append(current_waveform)
            Rows_list.append(current_row)
        else:
            raise Exception("Incorrect format, should be Waveform, float or list of Waveform, list of float")



        return waveforms_list, Rows_list

    def get_enables_for_waveforms(self, waveforms):
        if isinstance(waveforms, wfm.Waveform):
            return self.enables_lut[1]

        # else it should be a list of waveforms (checked before)
        num_waveforms = len(waveforms)

        return (self.enables_lut[len(waveforms)])

    def create_json_rows(self,Stim_rows):

        """
        Dear Cathal, one day you'll see this code and say WTF who wrote this,
        it's you, you did it, I'm you from the past
        """

        row_list = []
        Rows = {}
        row_count = 0
        if isinstance(Stim_rows, list):
            for el in Stim_rows:
                row_list.append(el)
                row_count = row_count + 1
                Rows = row_list
            return Rows
        else:
            row_list.append(Stim_rows)

        return row_list

    def create_json_columns(self,durations, Stim_rows, equal=0):

        """
        Dear Cathal, one day you'll see this code and say WTF who wrote this,
        it's you, you did it, I'm you from the past
        """

        column_list = []
        column_count = 0
        for dur in durations:
            column_count = column_count + 1
            current_column = {}
            current_column['Duration'] = dur
            if equal == 0:
                if Stim_rows[len(Stim_rows) - column_count] and len(Stim_rows) - column_count > -1:
                    current_column['StimRows'] = self.create_json_rows(Stim_rows[len(Stim_rows) - column_count])
                else:
                    current_column['StimRows'] = []
            else:
                row_to_use = self.create_json_rows(Stim_rows)
                row_str = str(row_to_use)
                # rr = row_str.replace("'","")
                if row_str:
                    current_column['StimRows'] = row_str  # [row_to_use]
                else:
                    current_column['StimRows'] = []

            current_column['CollisionFreeTimeout'] = 0
            column_list.append(current_column)
            if equal == 1:
                break

        #if we want to have an empty segment to have always the same timings


        return column_list

    def display_tonic_stim(self, waveform, amplitude, frequency, show_segments=False):
        electrode_symbols = []
        for i in range(0, len(waveform.electrode_config) - 1):
            electrode = waveform.electrode_config[i]
            if electrode == -1:
                symbol = '-'
            elif electrode == 1:
                symbol = '+'
            else:
                symbol = 'O'

            electrode_symbols.append(symbol)

        seg = ['  '] * 13

        # Relevant only for MR
        if show_segments:
            seg[4] = 'L1'
            seg[6] = 'L3'
            seg[8] = 'L4'
            seg[10] = 'S1'

        s = electrode_symbols
        freq = str(int(frequency))
        amp = "{:.1f}".format(amplitude)

        if waveform.lead_type == wfm.LeadType.GTX:
            print(seg[0] + '    / ' + '  \\      \n' +
                  seg[1] + '   /  ' + s[1] + '  \\     \n' +
                  seg[2] + '   |' + s[7] + '   ' + s[13] + '|    Frequency:\n' +
                  seg[3] + '   |  ' + s[0] + '  |      ' + freq + ' Hz\n' +
                  seg[4] + '   |' + s[6] + '   ' + s[12] + '|     \n' +
                  seg[5] + '   |  ' + s[15] + '  |    Amplitude:\n' +
                  seg[6] + '   |' + s[5] + '   ' + s[11] + '|      ' + amp + ' mA\n' +
                  seg[7] + '   |  ' + s[14] + '  |     \n' +
                  seg[8] + '   |' + s[4] + '   ' + s[10] + '|     \n' +
                  seg[9] + '   |  ' + '   |     \n' +
                  seg[10] + '   |' + s[3] + s[2] + ' ' + s[8] + s[9] + '|     \n' +
                  '     -------  \n'
                  )
        elif waveform.lead_type == wfm.LeadType.Medtronic:
            print(seg[0] + '    / ' + '  \\      \n' +
                  seg[1] + '   /  ' + s[0] + '  \\     \n' +
                  seg[2] + '   |' + s[1] + '   ' + s[8] + '|    Frequency:\n' +
                  seg[3] + '   |  ' + s[2] + '  |      ' + freq + ' Hz\n' +
                  seg[4] + '   |' + s[3] + '   ' + s[9] + '|     \n' +
                  seg[5] + '   |  ' + s[4] + '  |    Amplitude:\n' +
                  seg[6] + '   |' + s[5] + '   ' + s[10] + '|      ' + amp + ' mA\n' +
                  seg[7] + '   |  ' + s[11] + '  |     \n' +
                  seg[8] + '   |' + s[6] + '   ' + s[12] + '|     \n' +
                  seg[9] + '   |  ' + s[13] + '  |     \n' +
                  seg[10] + '   |' + s[7] + '   ' + s[14] + '|     \n' +
                  seg[11] + '   |  ' + s[15] + '  |     \n' +
                  seg[11] + '   \  ' + '   /     \n' +
                  seg[12] + '    \ ' + '  /      \n'
                  )
        else:
            raise Exception('Lead type visualisation is not supported')

    def create_stim_sequences(self,durations,rows_json,rows_json_standby,equal):

        stim_sequences_list = []
        stim_sequence_standby = {}
        stim_sequence_standby['LoopMode'] = 0
        stim_sequence_standby['SequenceName'] = 'Algov1'
        stim_sequence_standby['StimColumns'] = self.create_json_columns([20], rows_json_standby, equal)
        stim_sequence_standby['Uid'] = 'banana1'

        stim_column_event = {}
        stim_column_event['LoopMode'] = 1 # we have to do 1 for the stim and hold trick
        stim_column_event['SequenceName'] = 'Trigger'
        stim_column_event['StimColumns'] = self.create_json_columns(durations, rows_json, equal)
        stim_column_event['Uid'] ='banana2'

        stim_sequences_list.append(stim_sequence_standby)
        stim_sequences_list.append(stim_column_event)

        return stim_sequences_list

    def make_stim_n_millisecond(self, waveforms, amplitudes, frequency, offset, ramping, durations, LoopMode,pulses, equal = 0 ):
        """
        Create a triggered type activity with a single event of n milliseconds (500
        by default)

        Can input either a single waveform and a single amplitude, or an equal sized
        list of each

        Only a single frequency can be set

        Output is string format to be added to a http request
        """

        if LoopMode < 0 or LoopMode > 2:
            raise Exception("LoopMode not supported")

        if isinstance(waveforms, list):
            wfm = waveforms[0]

        else:
            wfm = waveforms

        #_, rows_json_standby = self.create_current_waveforms_json(wfm, 0.0 , 5, 0, False, 1)


        waveforms_json, rows_json = self.create_current_waveforms_json(waveforms, amplitudes,frequency,offset,ramping,pulses)

        activity_dict = {
            'LoopMode': 2,  # has to be 2
            'Waveforms': waveforms_json,
            'StimColumns': self.create_json_columns(durations, rows_json, equal)
        }



        return "Parameters=" + json.dumps(activity_dict)

    def make_tonic_activity(self, waveforms, amplitudes, frequency, offset, ramping, durations, LoopMode,pulses, equal = 0 ):
        """
        Create a triggered type activity with a single event of n milliseconds (500
        by default)

        Can input either a single waveform and a single amplitude, or an equal sized
        list of each

        Only a single frequency can be set

        Output is string format to be added to a http request
        """

        if LoopMode < 0 or LoopMode > 2:
            raise Exception("LoopMode not supported")
        frequency = int(frequency)

        # amplitudes are checked for validity versus the targetted waveform here
        waveforms_json, rows_json = self.create_current_waveforms_json(waveforms, amplitudes,frequency,offset,ramping,pulses)

        if not isinstance(frequency, int):
            raise Exception('Frequency must be an integer')


        activity_dict = {
            'LoopMode': LoopMode,  # TBD implement amount of time it has to stay up
            'Waveforms': waveforms_json,
            'StimColumns': self.create_json_columns(durations, rows_json, equal)
        }


        return "Parameters=" + json.dumps(activity_dict)



