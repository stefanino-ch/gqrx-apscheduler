"""
:Author: Stefan Feuz
:License: General Public License GNU GPL 3.0
"""

import argparse
import os
import sys
import time
import telnetlib
import threading

from datetime import datetime

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ModuleNotFoundError:
    print('Python module apscheduler not found. Try "pip install apscheduler"')
    exit(0)

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        print('Python modules tomllib or tomli not found.')
        print('-> Try "pip install tomlib" or')
        print('-> Try "pip install tomli" or')
        exit(0)

sem = threading.Semaphore()


class Singleton(type):
    """
    Helper class needed to get only one single Communicator.
    If multiple Communicators are instantiated, you might run into communication
    errors if multiple messages are sent during overlapping timeslots.

    Many thanks to:
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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
        is opened
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
        Assures there is only one command set at a time
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
        Entry port of communicator if a list of commands shall be sent to gqrx
        :param cmd_list: List containing string elements representing command
                         strings to be sent to gqrx
        """
        for single_cmd in cmd_list:
            self.send_cmd(single_cmd)


class SchedParseExc(Exception):
    """
    Exception class for schedule parser
    """
    def __init__(self, message):
        """
        Class initialization
        """
        self.message = message

        super().__init__(message)

    def __str__(self):
        """
        :return: Exception text as string
        """
        return self.message


class ScheduleParser:

    def __init__(self, path_file_name):
        """
        Class initialization
        """
        self.setup_cmd = None
        self.new_task = None
        self.port = None
        self.hostname = None
        self.path_file_name = path_file_name
        self.task_list = []

    def __read_file(self):
        """
        Reads the tomlib file containing the schedule to be executed.
        :return: Content of the schedule file as tomlib structure
        """
        try:
            with open(self.path_file_name, mode="rb") as fp:
                schedule = tomllib.load(fp)
                fp.close()
                return schedule
        except OSError as err:
            raise err

    def get_connection_settings(self):
        """
        Extracts the connection setup parameters from the schedule file.
        :return: hostname and port number of the gqrx instance to connect
        """
        try:
            schedule = self.__read_file()
            self.hostname = schedule["connection-settings"]["hostname"]
            self.port = schedule["connection-settings"]["port"]
            return self.hostname, self.port
        except (OSError, KeyError) as err:
            raise err

    def get_setup_cmd(self):
        """
        Extracts the initial gqrx setup commands to be executed once the
        connection is set up
        :return: List containing all setup commands
        """
        try:
            schedule = self.__read_file()
            self.setup_cmd = schedule["initial-setup"]["commands"]
            return self.setup_cmd
        except (OSError, KeyError) as err:
            raise err

    def get_task_list(self):
        """
        Extracts all scheduler tasks from the schedule file.
        :return: List containing instances of l_task representing a single l_task
        """
        self.task_list = []
        try:
            schedule = self.__read_file()
            tlist = schedule["task"]
            for l_task in tlist:
                self.new_task = Task()
                self.task_list.append(self.new_task)

                # loop through and build the list based on l_task class
                for key, value in l_task.items():
                    if key == "execution":
                        if value in Task.exec_vals:
                            self.new_task.cmd_exec \
                                = Task.exec_vals.index(value)
                        else:
                            raise(SchedParseExc
                                  (f'Unknown execution type found: {value}'))

                    elif key == 'commands':
                        self.new_task.cmd_list = value

                    elif key == "sched_type":
                        if value in Task.sched_vals:
                            self.new_task.cmd_sched \
                                = Task.sched_vals.index(value)
                        else:
                            raise(SchedParseExc
                                  (f'Unknown schedule type found: {value}'))

                    else:
                        # scheduler specific element
                        if self.new_task.cmd_sched is None:
                            raise(SchedParseExc
                                  ('Scheduler property found before scheduler '
                                   f'was defined: {key}'))
                        else:
                            if (key in self.new_task.props_list
                                    [self.new_task.cmd_sched]):
                                setattr(self.new_task, key, value)
                            else:
                                raise(SchedParseExc
                                      (f'Unknown scheduler property {key}'))
            return self.task_list

        except (OSError, KeyError) as err:
            raise err


class Task:
    """
    Internal representation of a single task defined in the schedule file
    """
    # Allowed values for exec_vals
    exec_vals = ["all",
                 "one_by_one"]

    # Allowed values sched_vals
    sched_vals = ["date",
                  "interval",
                  "cron"]

    # Allowed values for date_props
    date_props = ["run_date",
                  "timezone"]

    # Allowed values interval props
    interval_props = ["weeks",
                      "days",
                      "hours",
                      "minutes",
                      "seconds",
                      "start_date",
                      "end_date",
                      "timezone",
                      "jitter"]

    # Allowed values cron_props
    cron_props = ["year",
                  "month",
                  "day",
                  "day_of_week",
                  "hour",
                  "minute",
                  "second",
                  "start_date",
                  "end_date",
                  "timezone",
                  "jitter"]

    props_list = [date_props, interval_props, cron_props]

    def __init__(self):
        """
        Class initialization
        """
        self.cmd_exec = None
        self.cmd_sched = None
        self.cmd_list = None
        self.next_cmd = 0
        # date
        self.run_date = None
        self.timezone = None
        # interval
        self.weeks = None
        self.days = None
        self.hours = None
        self.minutes = None
        self.seconds = None
        # interval and cron
        self.start_date = None
        self.end_date = None
        self.jitter = None
        self.timezone = None
        # cron
        self.year = None
        self.month = None
        self.day = None
        self.week = None
        self.day_of_week = None
        self.hour = None
        self.minute = None
        self.second = None

    def get_param_dict(self):
        """
        Extracts all parameters set for a specific task.
        :return: Dict containing property value pairs
        """
        param_dict = {}
        if self.cmd_sched is None:
            return param_dict
        else:
            for prop in self.props_list[self.cmd_sched]:
                if getattr(self, prop) is not None:
                    param_dict[prop] = getattr(self, prop)
            return param_dict

    def run_cmd(self, ip, port):
        """
        Sends the commands of a specific task to the communicator.
        Here in we take care about if the full command list, or one by one
        commands will be sent out
        :param ip: IP address of the computer where gqrx is running
        :param port: Port on which gqrx is listening
        """
        try:
            comm = Communicator(ip, port)
        except Exception as err:
            sys.stderr.write(f'Problems during connection setup: {err} {os.linesep}')
            exit(1)

        if self.cmd_exec == Task.exec_vals.index('one_by_one'):
            comm.send_cmd(self.cmd_list[self.next_cmd])

            self.next_cmd += 1
            if self.next_cmd >= len(self.cmd_list):
                # Jump back to start
                self.next_cmd = 0
        else:
            comm.send_cmd_list(self.cmd_list)


def main():
    """
    Main routine.
    """
    setup_cmd = []

    parser = argparse.ArgumentParser(prog='qgrx-scheduler',
                                     description='Remote controls qqrx based \
                                                  on a scheduling file.')
    parser.add_argument('schedule_file', help='Name of the file containing \
                                              the scheduling information. ')
    args = parser.parse_args()

    # Open scheduling file
    sched_parser = ScheduleParser(args.schedule_file)
    try:
        hostname, port = sched_parser.get_connection_settings()
    except OSError as err:
        sys.stderr.write(f'Problems during schedule file read: {err} {os.linesep}')
        exit(1)
    except KeyError as err:
        sys.stderr.write(f'Problems to detect the connection settings: {err} {os.linesep}')
        exit(1)

    # Read the initial_setup commands and tasks
    try:
        setup_cmd = sched_parser.get_setup_cmd()
        task_list = sched_parser.get_task_list()
    except OSError as err:
        # Just for safety, should not happen here as file
        # was already used before
        sys.stderr.write(f'Problem during schedule file read: {err} {os.linesep}')
        exit(1)
    except KeyError as err:
        sys.stderr.write(f'Problem to detect setup commands: {err} {os.linesep}')
        exit(1)
    except SchedParseExc as err:
        sys.stderr.write(f'Problem during task parsing: {err} {os.linesep}')
        exit(1)

    # Send initial_setup commands out
    try:
        comm = Communicator(hostname, port)
    except Exception as err:
        sys.stderr.write(f'Problems during connection setup: {err} {os.linesep}')
        exit(1)

    comm.send_cmd_list(setup_cmd)

    # Setup scheduler
    sched = BackgroundScheduler(daemon=True)

    # Establish scheduler based on tasklist
    for task in task_list:
        if task.cmd_sched == Task.sched_vals.index('date'):
            task_params = task.get_param_dict()
            sched.add_job(task.run_cmd,
                          'date',
                          args=[hostname, port],
                          **task_params)
        elif task.cmd_sched == Task.sched_vals.index('interval'):
            task_params = task.get_param_dict()
            sched.add_job(task.run_cmd,
                          'interval',
                          args=[hostname, port],
                          **task_params)
        else:
            task_params = task.get_param_dict()
            sched.add_job(task.run_cmd,
                          'cron',
                          args=[hostname, port],
                          **task_params)

    # Start the scheduler
    sched.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()


if __name__ == '__main__':
    main()
