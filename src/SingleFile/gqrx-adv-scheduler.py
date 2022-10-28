"""
:Author: Stefan Feuz
:License: General Public License GNU GPL 3.0
"""

import argparse
import os
import sys
import time

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except:  # noqa E722
    print('Python module apscheduler not found. Try "pip install apscheduler"')
    exit(0)

from communicator import Communicator
from scheduleparser import ScheduleParser, SchedParseExc
from task import Task




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
