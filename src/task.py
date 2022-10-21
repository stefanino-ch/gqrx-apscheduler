"""
:Author: Stefan Feuz
:License: General Public License GNU GPL 3.0
"""
import os
import sys

from communicator import Communicator


class Task:
    exec_vals = ["all",
                 "one_by_one"]

    sched_vals = ["date",
                  "interval",
                  "cron"]

    date_props = ["run_date",
                  "timezone"]

    interval_props = ["weeks",
                      "days",
                      "hours",
                      "minutes",
                      "seconds",
                      "start_date",
                      "end_date",
                      "timezone",
                      "jitter"]

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
        param_dict = {}
        if self.cmd_sched is None:
            return param_dict
        else:
            for prop in self.props_list[self.cmd_sched]:
                if getattr(self, prop) is not None:
                    param_dict[prop] = getattr(self, prop)
            return param_dict

    def run_cmd(self, hostname, port):
        try:
            comm = Communicator(hostname, port)
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
