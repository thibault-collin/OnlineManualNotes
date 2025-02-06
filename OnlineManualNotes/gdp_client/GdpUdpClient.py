import socket
import numpy as np
import threading
import time
from collections import deque
import itertools
from . import SensorList

# todo: Decide whether the constructor, or "start" is what takes "SensorList" as
# input
DELSYS_EMG_SAMPLING_RATE = 1259
DELSYS_IMU_SAMPLING_RATE = 148
QUATERNIONS_SAMPLING_RATE = 30

MAX_BUFFER_SECONDS = 20

PACKET_TYPES = ['EMG', 'IMU', 'Quaternion', 'Kinematics']

class GdpUdpClient():

    # Static variables section
    is_instantiated = False

    def __init__(self, ip, port, sensor_list, extra_listener=None):
        """
        There can only be one UDP Client running extra_listener is an optional
        method parameter which will be called at each packet receive fro the UDP
        server, which takes the bytestream directly as an input
        """

        # if GdpUdpClient.is_instantiated == True:
        #     raise Exception('There is already a UDP Client running')
        # GdpUdpClient.is_instantiated = True

        if isinstance(ip, str) != True:
            raise Exception('Ip is not in correct format')
        self.ip = ip
        self.port = port

        if isinstance(sensor_list, SensorList.SensorList) == False:
            raise Exception('sensor list has incorrect format')

        self.sensor_list = sensor_list
        self.sensor_queue_dict = {}

        if (extra_listener != None):
            self.extra_listener = extra_listener
        else:
            self.extra_listener = self.data_do_nothing

        self.packet_size = 65000 # 30 # bytes, or what?
        self.running = False
        self.thread = None
        self.udp_server_socket = None

        self.queue_lock = threading.Lock()

    def thread_receive(self):
        count = 0
        while(self.running):
            try:
                # How quickly do we lose old data with UDP? Not very, I don't think
                # so it is a valid place to buffer is what you're saying?
                data_string, address = self.udp_server_socket.recvfrom(self.packet_size)
                # ask the time -- save it or see it compare python ms -- time stamps -- htpp command so we know python time == gdp app -- logging of gdp
                count = count + 1
            except socket.timeout:
               continue

            if len(data_string) == 0:
                continue

            data_bytes = np.array(bytearray(data_string), dtype=np.uint8) # in the data we have time -- constant offset between gdp and python mac time
            data_as_float = data_bytes.view(dtype=np.float32)

            # print("GDP time = " + str(gdp_time))
            # print('packet type = ' + str(packet_type) + ', num samples =' + str(number_of_samples))
            
            self.queue_lock.acquire()

            self.decode(data_as_float)

            self.queue_lock.release()

            self.extra_listener(data_as_float)

            # cheap debug
            # if count % 100 == 0:
            #     print(list(itertools.islice(self.sensor_queue_dict['EMG']['trigger'], 3, 13)))
        return

    def make_quaternions_buffer(self):
        deque_dict = {}

        def q_factory():
            return deque(maxlen=QUATERNIONS_SAMPLING_RATE*MAX_BUFFER_SECONDS) 

        deque_dict['Time'] = q_factory()
        for sensor_name in self.sensor_list.sensor_dict['Quaternion']:
            for dimension in ['Q1', 'Q2', 'Q3', 'Q4']:
                deque_dict[sensor_name + '_' + dimension] = q_factory()

        deque_dict['ActiveLine'] = q_factory()
        self.sensor_queue_dict['Quaternion'] = deque_dict

    def make_emgs_buffer(self):
        deque_dict = {}

        def q_factory():
            return deque(maxlen=DELSYS_EMG_SAMPLING_RATE*MAX_BUFFER_SECONDS) 

        deque_dict['Time'] = q_factory()
        for sensor_name in self.sensor_list.sensor_dict['EMG']:
            deque_dict[sensor_name] = q_factory()

        deque_dict['ActiveLine'] = q_factory()
        self.sensor_queue_dict['EMG'] = deque_dict;

    def make_imus_buffer(self):
        deque_dict = {}

        def q_factory():
            return deque(maxlen=DELSYS_IMU_SAMPLING_RATE * MAX_BUFFER_SECONDS)

        deque_dict['Time'] = q_factory()

        for sensor_name in self.sensor_list.sensor_dict['IMU']:

            for dimension in ['AccX', 'AccY', 'AccZ','GyrX', 'GyrY', 'GyrZ']:
                deque_dict[sensor_name + '_' + dimension] = q_factory()


        deque_dict['ActiveLine'] = q_factory()
        self.sensor_queue_dict['IMU'] = deque_dict;


    def decode(self, data_as_float):
        """
        input is entire data packet, including the packet type
        """

        packet_type = int(data_as_float[0])
        packet_key = PACKET_TYPES[packet_type]
        num_samples = data_as_float[1]
        
        offset = 2 # first index of time
        for i in range(0,int(num_samples)):
            for sensor_name in self.sensor_queue_dict[packet_key].keys():
                queue = self.sensor_queue_dict[packet_key][sensor_name]
                data_point = data_as_float[offset]
                queue.append(data_point)

                offset = offset + 1
        #print('banana')



    def get_last_s_seconds(self, key, seconds):
        """
        takes key in set  ['EMG', 'Quaternion'] and seconds and returns a dictionary
        of the last n samples for all queues related to that key. This is a copy 
        operation, so the deques behind remain unchanged.

        We keep the default behaviour of itertools.islice - that is, if a slice longer
        than the length of the underlying object is requested, then we give the max size available

        todo: reconsider
        """
        
        if (key == 'EMG'):
            n = DELSYS_EMG_SAMPLING_RATE * seconds
        elif (key == 'Quaternion'):
            n = QUATERNIONS_SAMPLING_RATE * seconds
        elif (key == 'IMU'):
            n = DELSYS_IMU_SAMPLING_RATE * seconds

        requested_list_dict = {}
        
        deque_dict = self.sensor_queue_dict[key]
        self.queue_lock.acquire()

        for inner_key in deque_dict.keys():
            most_recent_sample_idx = len(deque_dict[inner_key]) - 1
            oldest_sample_requested_idx = int(max(most_recent_sample_idx - n, 0))
            requested_list_dict[inner_key] = list(itertools.islice(
                deque_dict[inner_key], 
                oldest_sample_requested_idx, 
                most_recent_sample_idx
            ))

        self.queue_lock.release()

        return requested_list_dict

    def test_pause_thread(self, pause_length):
        self.queue_lock.acquire()
        time.sleep(0.5) 
        self.queue_lock.release()

    def start(self):

        self.running = True

        # Create a datagram socket
        self.udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_server_socket.settimeout(1) # second(s) timeout
        # Bind to address and ip
        self.udp_server_socket.bind((self.ip, int(self.port)))

        print('UDP server up and listening')

        # create all of the deques to be used to buffer the UDP datastreaM
        for packet_type in self.sensor_list.sensor_dict.keys():
            if (packet_type == 'EMG'):
                self.make_emgs_buffer()
            if (packet_type == 'IMU'):
                self.make_imus_buffer()
            if (packet_type == 'Quaternion'):
                self.make_quaternions_buffer()

        self.thread = threading.Thread(target=self.thread_receive)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
        print('Thread successfully stopped')

    def data_do_nothing(self, message): 
        pass

class CountPackets: 
    def __init__(self): 
        self.packets = 0

    def data_count_packets_per_second(self, message):
        self.packets = self.packets + 1
        print(self.packets)

class SaveTimeStamps:
    def __init__(self, filename):
        self.filename = filename
        self.saving = False

    def start(self):
        if not self.saving:
            self.file = open(self.filename, 'w')
            self.saving = True

    def listener(self, data_as_float):
        if self.saving:
            self.file.write(str(int(data_as_float[2])) + '\n')

    def stop(self):
        if self.saving:
            self.saving = False
            self.file.close()

class SaveByteStream:
    def __init__(self, filename):
        self.filename = filename
        self.saving = False

    def start(self):
        if not self.saving:
            self.file = open(self.filename, 'wb')
            self.saving = True

    def listener(self, data_as_float):
        if self.saving:
            self.file.write(bytearray(data_as_float))

    def stop(self):
        if self.saving:
            self.saving = False
            self.file.close()

class CheckTimeBetweenSamples:
    def __init__(self):
        self.get_first_sample = False
        self.first_and_last = False
        self.max_between_samples = False

    def start_first_and_last(self):
        self.samples_collected = 0

        # avoid race condition, set inner booleans first
        self.got_last_sample = False
        self.get_last_sample = False
        self.get_first_sample = True

        # only then set the outer boolean for listener
        self.first_and_last = True

    def start_max_between_samples(self):

        self.get_first_sample_max_between = True
        self.prev_sample = 0
        self.max_val_between_samples = 0

        # set the outer boolean for the listener last
        self.max_between_samples = True
        

    def listener(self, data_as_float):
        sample_time = int(data_as_float[2])
        if self.first_and_last:
            self.samples_collected = self.samples_collected + 1

            if self.get_first_sample:
                self.first_sample_time = sample_time
                self.get_first_sample = False
            if self.get_last_sample:
                self.last_sample_time = sample_time
                self.got_last_sample = True
                self.first_and_last = False

        if self.max_between_samples:
            if self.get_first_sample_max_between:
                self.prev_sample = sample_time
                self.get_first_sample_max_between = False

            time_between_samples = sample_time - self.prev_sample

            self.max_val_between_samples = max (
                self.max_val_between_samples, 
                time_between_samples
            )
            self.prev_sample = sample_time

    def stop(self):
        """ 
        Stop any and all checking listeners and get the timing results
        """

        if self.first_and_last:
            self.get_last_sample = True
            while self.got_last_sample == False:
                pass

            return ( self.last_sample_time - self.first_sample_time ) / (self.samples_collected - 1)

        if self.max_between_samples:
            self.max_between_samples = False
            return self.max_val_between_samples
    


if __name__ == "__main__": # Unit tests

    print ('Testing that a second instance cannot be made of the UDP class without closing the first')

    ip = '127.0.0.1'
    port = 12345
    client_1 = GdpUdpClient(ip, port, None)

    try:
        client_2 = GdpUdpClient(ip, port, None)
    except:
        testSuccess = True
    else:
        testSuccess = False

    print("Test success is " + str(testSuccess))
    

