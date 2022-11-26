import libtmux
import os
from tqdm import tqdm
import argparse

from secrets import token_hex
from contextlib import closing
import socket

import random
import time


# def find_open_ports_hard(num_ports):
#     ports = []
#     for port in range(65535):
#         if len(ports) == num_ports:
#             break
#         with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
#             res = sock.connect_ex(('localhost', port))
#             if res == 0:
#                 ports.append(port)
#         time.sleep(120)
#     find_open_ports(num_ports, ports)
#     return ports


def find_open_ports(num_ports, ports=[]):
    while len(ports) < num_ports:
        ports.append(random.randint(0, 65535))
    return ports


def start(num_users, base_dir='./', ports=[], session_name="main"):
    """
    Запускает $num_users jupyter notebook-ов. У каждого working directory $base_dir+$folder_num.
    params:
    num_users -- количество запускаемых ноутбуков;
    -d, --base_dir -- корневая директория для работы;
    -s, --session_name -- имя создаваемой сессии, имя по умолчанию main;
    """

    ports = find_open_ports(num_users, ports)
    os.chdir(base_dir)
    server = libtmux.Server()
    server.new_session(session_name)
    session = server.list_sessions()[-1]
    log_template = "The environment {} was created in the folder {} in the window named {} !"

    print("Our session: ", session)

    with tqdm(desc="creating environments...", total=num_users) as progress_bar:
        for i in range(0, num_users):
            os.system("mkdir {}".format(i))
            os.system("chmod -R 777 {}".format(i))

            if i == 0:
                window = session.list_windows()[-1]
            else:
                window = session.new_window(attach=False, window_name=str(i))
            print("window {} created!".format(i))
            pane = window.split_window(attach=False)
            pane.send_keys('cd {}'.format(i), enter=True)
            pane.send_keys("python -m venv venv{}".format(i), enter=True)
            pane.send_keys("source  venv{}/bin/activate".format(i), enter=True)
            pane.send_keys(
                'jupyter notebook --ip {} --port {} --no-browser --NotebookApp.token={} --NotebookApp.notebook_dir={}'.format(
                    "127.0.0.1", ports[i], token_hex(16), "."), enter=True)

            progress_bar.update(1)
            tqdm.write(log_template.format(i, base_dir + "/" + str(i), i))

    # print(session.list_windows())


def stop(session_name, num):
    """
    Убивает окружение с нужным номером.
    params:
    num -- номер окружения;
    -s, --session_name -- имя сессии, в которой надо убить окружение с именем num; по умолчанию окружение убивается
    в последней запущенной сессии
    """
    server = libtmux.Server()
    session = server.find_where({"session_name": session_name})
    if session is None:
        session = server.list_sessions()[-1]
    session.kill_window(str(num))


def stop_all(session_name=None):
    """
     Убивает указанную сессию. Если сессия не была указана, то убьет последнюю запущенную.
     params:
    -s, --session_name -- имя сессии, которую надо убить
    """
    server = libtmux.Server()
    if session_name is None:
        server.kill_session(server.list_sessions()[-1].id)
    else:
        server.kill_session(session_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Linux & Tmux')
    subparsers = parser.add_subparsers(dest='command')

    start_ = subparsers.add_parser('start', help="start -- " + start.__doc__)
    start_.add_argument('num_users',
                        type=int,
                        help='number of jupyter notebooks to run'
                        )
    start_.add_argument('-d',
                        '--base_dir',
                        type=str,
                        help='the directory where environment subfolders are created',
                        default="./"
                        )
    start_.add_argument('-',
                        '--ports',
                        type=int,
                        nargs='*',
                        help='list of ports for environments',
                        default=[]
                        )
    start_.add_argument('-s',
                        '--session_name',
                        type=str,
                        help='name for the  session to be created',
                        default="main"
                        )

    stop_ = subparsers.add_parser('stop', help="stop -- " + stop.__doc__)
    stop_.add_argument('-s', '--session_name',
                       type=str,
                       help='the name of the tmux session in which the environments are running',
                       default="main"
                       )
    stop_.add_argument('num',
                       type=int,
                       help='the number of the environment to be killed'
                       )

    stop_all_ = subparsers.add_parser('stop_all', help="stop_all -- " + stop_all.__doc__)
    stop_all_.add_argument('-s', '--session_name',
                           type=str,
                           help='the name of the tmux session to be killed',
                           )

    args = parser.parse_args()

    if args.command is None:
        print("You didn't give the program any arguments and it didn't do anything :c")
        print("Please use --help or -h to familiarize yourself with the functionality.")
    if args.command == 'start':
        start(args.num_users, args.base_dir, args.ports, args.session_name)
    if args.command == 'stop':
        stop(args.session_name, args.num)
    if args.command == 'stop_all':
        stop_all(args.session_name)
