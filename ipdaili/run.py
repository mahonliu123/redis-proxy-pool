from Scheduler import Schedule
from webapi import app


def main():
    s = Schedule()
    s.run()
    app.run()


if __name__ == '__main__':
    main()