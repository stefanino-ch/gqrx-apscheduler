import time

from apscheduler.schedulers.background import BackgroundScheduler


def main():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(lambda: sched.print_jobs(), 'interval', seconds=5)
    sched.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()


if __name__ == '__main__':
    main()
