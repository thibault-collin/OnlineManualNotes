from abc import ABC, abstractmethod

class IActivityGenerator(ABC):
    @abstractmethod
    def make_tonic_activity(self,waveforms, amplitudes, frequency, pulses):
        """
        Can input either a single waveform and a single amplitude, or
        an equal sized list of each

        Only a single frequency can be set

        Output is string format to be added to a http request
        """
        raise NotImplementedError

    @abstractmethod
    def make_stim_n_millisecond(self,waveforms, amplitudes, frequency, pulses, duration_ms):
        """
        Create a triggered type activity with a single event of n milliseconds (500
        by default)

        Can input either a single waveform and a single amplitude, or an equal sized
        list of each

        Only a single frequency can be set

        Output is string format to be added to a http request
        """
        raise NotImplementedError


    