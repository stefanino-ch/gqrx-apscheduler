import argparse
import time

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except:
    print('Python module apscheduler not found. Try "pip install apscheduler"')
    exit(0)

from communicator import Communicator
from schedule_parser import Schedule_parser, SchedParseExc
from task import Task


def main():
    setup_cmd = []

    parser = argparse.ArgumentParser(prog='qgrx-scheduler',
                                     description='Remote controls Gqrx based \
                                                  on a scheduling file.')
    parser.add_argument('schedule_file', help='Name of the file containing \
                                              the scheduling information. ')
    args = parser.parse_args()

    # Open scheduling file
    sched_parser = Schedule_parser(args.schedule_file)
    try:
        hostname, port = sched_parser.get_connection_settings()
    except OSError as err:
        print(f'Problems during schedule file read: {err}')
        exit(1)
    except KeyError as err:
        print(f'Problems to detect the connection settings: {err}')
        exit(1)

    # Read the initial_setup commands and tasks
    try:
        setup_cmd = sched_parser.get_setup_cmd()
        task_list = sched_parser.get_task_list()
    except OSError as err:
        # Just for safety, should not happen anymore here as file
        # was already used before
        print(f'Problem during schedule file read: {err}')
        exit(1)
    except KeyError as err:
        print(f'Problem to detect setup commands: {err}')
        exit(1)
    except SchedParseExc as err:
        print(f'Problem during taks parsing: {err}')
        exit(1)

    # Send initial_setup commands out
    try:
        comm = Communicator(hostname, port)
    except Exception as err:
        print(f'Problems during connection setup: {err}')
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
    print(sched.get_jobs())

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()


if __name__ == '__main__':
    main()
