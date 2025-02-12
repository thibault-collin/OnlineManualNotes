import socket
import os
import yaml
from gdp_client import GdpHttpClient

class TCP_client():
    def __init__(self, tcp_ip, tcp_port, gdp_clients, tcp_flag = False):
        self.__tcp_ip = tcp_ip
        self.__tcp_port = tcp_port
        self.__gdp_clients = gdp_clients
        self.__tcp_flag = tcp_flag
        self.communicating_with_mapper()

    def communicating_with_mapper(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if self.__tcp_flag:
                    s.connect((self.__tcp_ip, int(self.__tcp_port)))
                sFlag = None
                while True:
                    if sFlag is None:
                        answer = input('s or m: ')
                    elif sFlag == 's':
                        answer = input('1-shoulder, 2-arm, 3-forearm, 4-hand, 5-finger, 6-thumb: ')
                    elif sFlag == 'm':
                        answer = input('1-DELant, 2-DELmed, 3-LD, 4-PM, 5-BB, 6-TB, 7-BR, 8-FD, 9-FC, 10-ED, 11-EC, 12-The: ')
                    match answer:
                        case 's':
                            sFlag = 's'
                            answer = 's'
                        case 'm':
                            sFlag = 'm'
                        case 'sp':
                            answer = 'spasticity'

                        case '1' if sFlag == 's':
                            sFlag = None
                            answer = 'shoulder'
                        case '2' if sFlag == 's':
                            sFlag = None
                            answer = 'arm'
                        case '3' if sFlag == 's':
                            sFlag = None
                            answer = 'forearm'
                        case '4' if sFlag == 's':
                            sFlag = None
                            answer = 'hand'
                        case '5' if sFlag == 's':
                            sFlag = None
                            answer = 'finger'
                        case '6' if sFlag == 's':
                            sFlag = None
                            answer = 'thumb'

                        case '1' if sFlag == 'm':
                            sFlag = None
                            answer = 'DELant'
                        case '2' if sFlag == 'm':
                            sFlag = None
                            answer = 'DELmed'
                        case '3' if sFlag == 'm':
                            sFlag = None
                            answer = 'LD'
                        case '4' if sFlag == 'm':
                            sFlag = None
                            answer = 'PM'
                        case '5' if sFlag == 'm':
                            sFlag = None
                            answer = 'BB'
                        case '6' if sFlag == 'm':
                            sFlag = None
                            answer = 'TB'
                        case '7' if sFlag == 'm':
                            sFlag = None
                            answer = 'BR'
                        case '8' if sFlag == 'm':
                            sFlag = None
                            answer = 'FD'
                        case '9' if sFlag == 'm':
                            sFlag = None
                            answer = 'FC'
                        case '10' if sFlag == 'm':
                            sFlag = None
                            answer = 'ED'
                        case '11' if sFlag == 'm':
                            sFlag = None
                            answer = 'EC'
                        case '12' if sFlag == 'm':
                            sFlag = None
                            answer = 'The'

                        case _:
                            sFlag = None

                    if self.__tcp_flag:
                        s.sendall(answer.encode())
                        data = s.recv(1024)

                    if answer == 's':
                        msg2GDP = 'sensation'
                    elif answer == 'm':
                        msg2GDP = 'motor activity'
                    else:
                        msg2GDP = answer

                    self.__sendToGDPs(msg2GDP)

                    if self.__tcp_flag:
                        print(f"Received {data!r}")
        except KeyboardInterrupt:
            print('Connection closed.')

    def __sendToGDPs(self, answer):
        for gdpClient in self.__gdp_clients:
            cmdd = gdpClient.make_Command(GdpHttpClient.SetRelativeAmplitude,'OnlineNotesFlag_' + answer)
            cmdd.Send()

if __name__ == "__main__":
    configFilePath = os.getcwd() + '\\Config\\config_communication.yaml'
    with open(configFilePath) as f:
        _config = yaml.safe_load(f)

    gdp_clients = []
    for c in range(len(_config["gdp_ip"])):
        gdp_clients.append(GdpHttpClient.GdpHttpClient(_config["client_name"], _config["gdp_ip"][c], _config["gdp_http_port"][c], _config["gdp_key"][c]))

    TCP_client(_config["TCP_log_ip"][0], _config["TCP_log_port"][0], gdp_clients, _config["TCP_flag"][0])