from apscheduler.schedulers.background import BackgroundScheduler


def main():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(lambda: sched.print_jobs(), 'interval', seconds=5)
    sched.start()

    while 1:
        pass


if __name__ == '__main__':
    main()
