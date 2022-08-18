import sys
import telnetlib
import argparse
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


class Communicator:

    def __init__(self, hostname='127.0.0.1', port=7356):
        self.hostname = hostname
        self.port = port
        self.con = telnetlib.Telnet(self.hostname, self.port)

    def __send(self, cmd):
        self.con.write(f'{cmd}\n'.encode('ascii'))
        response = self.con.read_some().decode('ascii').strip()
        self.con.write('c\n'.encode('ascii'))
        return response


def main():
    parser = argparse.ArgumentParser(prog='qgrx-scheduler',
                                     description='Remote controls Gqrx based on a scheduling file. ')
    parser.add_argument('config_file', help='Name of the file containing the scheduling information. ')
    args = parser.parse_args()

    try:
        with open(args.config_file, mode="rb") as fp:
            config = tomllib.load(fp)

            print(config)

    except OSError as err:
        print(err)
        sys.exit(1)

    try:
        hostname = config["connection-settings"]["hostname"]
        port = config["connection-settings"]["port"]
    except KeyError as err:
        print(f'Typo in .toml file: {err}')


if __name__ == '__main__':
    main()
