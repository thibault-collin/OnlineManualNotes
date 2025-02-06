import socket
import os
import yaml
from gdp_client import GdpHttpClient

class TCP_client():
    def __init__(self, tcp_ip, tcp_port, gdp_clients):
        self.__tcp_ip = tcp_ip
        self.__tcp_port = tcp_port
        self.__gdp_clients = gdp_clients
        self.communicating_with_mapper()

    def communicating_with_mapper(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.__tcp_ip, int(self.__tcp_port)))
                while True:
                    answer = input('s or m: ')
                    self.__sendToGDPs(answer)
                    s.sendall(answer.encode())
                    data = s.recv(1024)
                    print(f"Received {data!r}")
        except KeyboardInterrupt:
            print('Connection closed.')

    def __sendToGDPs(self, answer):
        for gdpClient in self.__gdp_clients:
            cmdd = gdpClient.make_Command(GdpHttpClient.SetRelativeAmplitude,'OnlineNotesFlag_' + answer)
            cmdd.Send()

if __name__ == "__main__":
    configFilePath = os.getcwd() + '\\OnlineManualNotes\\Config\\config_communication.yaml'
    with open(configFilePath) as f:
        _config = yaml.safe_load(f)

    gdp_clients = []
    for c in range(len(_config["gdp_ip"])):
        gdp_clients.append(GdpHttpClient.GdpHttpClient(_config["client_name"], _config["gdp_ip"][c], _config["gdp_http_port"][c], _config["gdp_key"][c]))

    TCP_client(_config["TCP_log_ip"][0], _config["TCP_log_port"][0], gdp_clients)