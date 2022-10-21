"""
:Author: Stefan Feuz
:License: General Public License GNU GPL 3.0
"""
import os
import sys
import telnetlib
import threading

from datetime import datetime
from singleton import Singleton

sem = threading.Semaphore()


class Communicator(metaclass=Singleton):
    """
    Handles all communication with gqrx
    """

    def __init__(self, ip='127.0.0.1', port=7356):
        """
        Class initialization
        :param ip: IP address of the computer where gqrx is running
        :param port: Port on which gqrx is listening
        """
        self.con = None
        self.__check_connection(ip, port)

    def __check_connection(self, ip, port):
        """
        Check if there is already a connection setup. If not a new connection
        is opened.
        :param ip: IP address of the computer where gqrx is running
        :param port: Port on which gqrx is listening
        """
        try:
            if not self.con:
                self.con = telnetlib.Telnet(ip, port)
        except Exception as err:
            raise err

    def __send(self, cmd):
        """
        Sends a single command string to gqrx
        :param cmd: The command as expected and understood by gqrx
        :return: String containing the answer received from gqrx
        """
        self.con.write(f'{cmd}\n'.encode('ascii'))
        raw = self.con.read_some()
        response = raw.decode('ascii').strip()
        return response

    def send_cmd(self, cmd):
        """
        Entry port of communicator for all commands to be sent to gqrx.
        Assures there is only one command set at a time.
        :param cmd: The command as expected and understood by gqrx
        """
        sem.acquire()

        resp = self.__send(cmd)

        now = datetime.now()
        dtstring = now.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(f'{dtstring} {cmd} {resp} {os.linesep}')

        sem.release()

    def send_cmd_list(self, cmd_list):
        """
        Entry port of communicator if a list of commands shall be sent to gqrx.
        :param cmd_list: List containing string elements representing command
                         strings to be sent to gqrx
        """
        for single_cmd in cmd_list:
            self.send_cmd(single_cmd)
