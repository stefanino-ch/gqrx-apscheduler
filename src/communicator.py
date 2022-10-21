"""
:Author: Stefan Feuz
:License: General Public License GNU GPL 3.0
"""
import os
import sys
import telnetlib

from datetime import datetime


class Communicator:

    con = None

    def __init__(self, hostname='127.0.0.1', port=7356):
        self.__check_connection(hostname, port)

    def __check_connection(self, hostname, port):
        try:
            if not self.con:
                self.con = telnetlib.Telnet(hostname, port)
        except Exception as err:
            raise err

    def __send(self, cmd):
        self.con.write(f'{cmd}\n'.encode('ascii'))
        raw = self.con.read_some()
        response = raw.decode('ascii').strip()
        return response

    def send_cmd(self, cmd):

        # TODO: make sure commands are not send in parallel
        resp = self.__send(cmd)

        now = datetime.now()
        dtstring = now.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(f'{dtstring} {cmd} {resp} {os.linesep}')

        if resp == 'RPRT 0':
            return True
        else:
            return False

    def send_cmd_list(self, cmd_list):
        resp = True
        for single_cmd in cmd_list:
            resp = resp and self.send_cmd(single_cmd)
        return resp
