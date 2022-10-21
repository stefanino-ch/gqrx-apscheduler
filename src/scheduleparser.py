"""
:Author: Stefan Feuz
:License: General Public License GNU GPL 3.0
"""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from task import Task


class SchedParseExc(Exception):
    def __init__(self, message):
        self.message = message

        super().__init__(message)

    def __str__(self):
        return self.message


class ScheduleParser:

    def __init__(self, path_file_name):
        self.setup_cmd = None
        self.new_task = None
        self.port = None
        self.hostname = None
        self.path_file_name = path_file_name
        self.task_list = []

    def __read_file(self):
        try:
            with open(self.path_file_name, mode="rb") as fp:
                schedule = tomllib.load(fp)
                fp.close()
                return schedule
        except OSError as err:
            raise err

    def get_connection_settings(self):
        try:
            schedule = self.__read_file()
            self.hostname = schedule["connection-settings"]["hostname"]
            self.port = schedule["connection-settings"]["port"]
            return self.hostname, self.port
        except (OSError, KeyError) as err:
            raise err

    def get_setup_cmd(self):
        try:
            schedule = self.__read_file()
            self.setup_cmd = schedule["initial-setup"]["commands"]
            return self.setup_cmd
        except (OSError, KeyError) as err:
            raise err

    def get_task_list(self):
        try:
            schedule = self.__read_file()
            tlist = schedule["task"]
            for task in tlist:
                self.new_task = Task()
                self.task_list.append(self.new_task)

                # loop through and build the list based on task class
                for key, value in task.items():
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
