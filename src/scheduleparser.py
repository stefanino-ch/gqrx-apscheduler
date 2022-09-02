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

    def __init__(self, file_path_name):
        self.filename = file_path_name

    def __read_file(self):
        try:
            with open(self.filename, mode="rb") as fp:
                schedule = tomllib.load(fp)
                fp.close()
                return schedule
        except OSError as err:
            raise err

    def get_connection_settings(self):
        try:
            schedule = self.__read_file()
            hostname = schedule["connection-settings"]["hostname"]
            port = schedule["connection-settings"]["port"]
            return hostname, port
        except (OSError, KeyError) as err:
            raise err

    def get_setup_cmd(self):
        try:
            schedule = self.__read_file()
            setup_cmd = schedule["initial-setup"]["commands"]
            return setup_cmd
        except (OSError, KeyError) as err:
            raise err

    def get_task_list(self):
        task_list = []
        try:
            schedule = self.__read_file()
            tlist = schedule["task"]
            for task in tlist:
                new_task = Task()
                task_list.append(new_task)

                # loop through and build the list based on task class
                for key, value in task.items():

                    if key == "execution":
                        if value in Task.exec_vals:
                            new_task.cmd_exec \
                                = Task.exec_vals.index(value)
                        else:
                            raise(SchedParseExc
                                  (f'Unknown execution type found: {value}'))

                    elif key == 'commands':
                        new_task.cmd_list = value

                    elif key == "sched_type":
                        if value in Task.sched_vals:
                            new_task.cmd_sched \
                                = Task.sched_vals.index(value)
                        else:
                            raise(SchedParseExc
                                  (f'Unknown schedule type found: {value}'))

                    else:
                        # scheduler specific element
                        if new_task.cmd_sched is None:
                            raise(SchedParseExc
                                  ('Scheduler property found before scheduler '
                                   f'was defined: {key}'))
                        else:
                            if (key in new_task.props_list
                                    [new_task.cmd_sched]):
                                setattr(new_task, key, value)
                            else:
                                raise(SchedParseExc
                                      (f'Unknown scheduler property {key}'))

            return task_list

        except (OSError, KeyError) as err:
            raise err
