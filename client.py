import socket
import time
import ast
import sys

COLOR = True

try:
    TCP_IP = sys.argv[1]
except:
    TCP_IP = '127.0.0.1'
    pass


class Colors():
    ESC = chr(0x1B) + '['
    RED = ESC + '31m'
    YELLOW = ESC + '33m'
    CYAN = ESC + '36m'
    GREEN = ESC + '32m'
    BLUE = ESC + '34m'
    RESET = ESC + '0m'


colors = Colors()

if not COLOR:
    colors.RED = ''
    colors.YELLOW = ''
    colors.CYAN = ''
    colors.GREEN = ''
    colors.BLUE = ''
    colors.RESET = ''
else:
    try:
        import colorama

        colorama.init()
        colors.RED = colorama.Fore.RED
        colors.YELLOW = colorama.Fore.YELLOW
        colors.CYAN = colorama.Fore.CYAN
        colors.GREEN = colorama.Fore.GREEN
        colors.BLUE = colorama.Fore.BLUE
        colors.RESET = colorama.Fore.RESET
    except:
        pass


class Packet():
    def __init__(self, payload):
        self.payload = payload

    def get_len_int(self):
        return len(self.payload)

    def get_len(self):
        return str(len(self.payload)).zfill(4)

    def get_payload(self):
        return self.payload


class PacketDispatcher():
    def __init__(self, socket):
        self.socket = socket

    def dispatch(self, packet):
        self.socket.send(packet.get_len())
        ack = self.socket.recv(4)
        if (ack == "_ACK"):
            self.socket.send(packet.get_payload())
        return ack

    def receive(self):
        l = int(self.socket.recv(4))
        self.socket.send("_ACK")
        return Packet(self.socket.recv(l))


def _ssget(idn):
    p.dispatch(Packet(idn))
    return p.receive().get_payload()


def _ssset(idn, dat):
    p.dispatch(Packet(idn))
    p.dispatch(Packet(dat))


def _ssnd(idn):
    p.dispatch(Packet(idn))


def get_points():
    return int(_ssget('-GPT'))


def get_id():
    return int(_ssget('-GID'))


def get_new():
    return _ssget('-NEW')


def set_jd(job, desc):
    _ssset('+SEJ', job)
    _ssset('+SED', desc)


def set_ready():
    _ssnd('/RED')


def set_end():
    _ssnd('/END')


def set_disc():
    _ssnd('/DSC')


def set_guessed(num):
    _ssset('+GUS', str(num))


def printpoints(pts):
    print(colors.BLUE + "\nYou currently have " + str(pts) + " points..."
                      + colors.RESET)


def promptjd(un):
    jp = colors.YELLOW + "Job: " + colors.RESET
    dp = colors.YELLOW + "Description: " + colors.RESET
    if un:
        #DONT CARE ABOUT LEN
        return raw_input(jp), raw_input(dp)
    else:
        #CHECK LEN
        jdone = False
        while not jdone:
            _j = raw_input(jp)
            if len(_j) > 0:
                jdone = True
        ddone = False
        while not ddone:
            _d = raw_input(dp)
            if len(_d) > 0:
                ddone = True
        return _j, _d


def pump(s_gus):
    newdat = ast.literal_eval(get_new())
    if 'guessed' in newdat:
        s_gus = newdat['guessed']
    s_gus[s_id] = 1
    return s_gus


TCP_PORT = 28136

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

p = PacketDispatcher(s)

print(colors.CYAN + "Welcome to my amazing game!\n")
s_id = get_id()
print(colors.CYAN + "Your ID is " + str(s_id) + "...\n")

while True:
    ### Server Variables
    rd = False
    job, desc = '', ''
    while True:
        ### JOB user input
        if len(job) > 0 and len(desc) > 0:
            print(colors.YELLOW + 'Leave field empty to leave unchanged')
            _job, _desc = promptjd(True)
            if len(_job) > 0:
                job = _job
            if len(_desc) > 0:
                desc = _desc
        else:
            job, desc = promptjd(False)

        ### RECHECK
        ok = raw_input(colors.CYAN + "\nIs everything ok? [Y/n]: "
                                   + colors.RESET).strip()
        if len(ok) == 0:
            break
        elif ok.lower().startswith('y'):
            break
    ### POPULATE
    set_jd(job, desc)
    set_ready()

    gotinit = False
    s_job = []
    s_des = []
    s_dif = []
    s_con = []
    s_points = get_points()
    printpoints(s_points)
    print(colors.BLUE + "Waiting for other players....")

    while not gotinit:
        newdat = ast.literal_eval(get_new())
        if 'jobs' in newdat:
            s_job = newdat['jobs']
            gotinit = True
        if 'diffs' in newdat:
            s_dif = newdat['diffs']
        if 'descs' in newdat:
            s_des = newdat['descs']
        if 'conn' in newdat:
            s_con = newdat['conn']
        time.sleep(0.05)

    cnt = len(s_job)

    s_gus = [0 for _ in range(cnt)]
    #List guessables
    for i in range(cnt):
        if i != s_id and s_con[i] == 1:
            print(colors.GREEN + str(i) + ")  " + colors.RESET + s_des[i])

    #Still something to guess
    while min([i for i, q in zip(s_gus, s_con) if q == 1]) == 0:
        while True:
            try:
                num = int(raw_input(colors.YELLOW + "\nEnter a NUMBER you want to guess: "))
            except ValueError:
                continue
            break
        #CHECK GUESSED
        if not num > cnt - 1:
            if s_con[num] == 0:
                print(colors.RED + "This person is not connected anymore..")
            if num == s_id:
                print(colors.RED + "Ha! you really thought I would allow you to guess your own thing?")
            else:
                guess = raw_input(colors.YELLOW + ":" + colors.RESET)
                s_gus = pump(s_gus)

                if s_gus[num] == 1:
                    print(colors.RED + "This has already been guessed by someone...")
                else:

                    if guess.lower() == s_job[num].lower():
                        print(colors.GREEN + "\n!!! You have indeed guessed it !!!")
                        set_guessed(num)
                        s_gus[num] = 1
                    else:
                        print(colors.RED + "\nSorry, better luck next time...")
                    s_points = get_points()
                printpoints(s_points)
                print('\n')

            for i in range(cnt):
                if s_gus[i] == 0 and i != s_id and s_con[i] == 1:
                    print(colors.GREEN + str(i) + ")  "
                                       + colors.RESET + s_des[i])

    print(
        colors.CYAN + '\n\n\nThere is nothing left for you to guess. You finished with ' + str(s_points) + ' points.')

    set_end()

    ng = False
    while not ng:
        n = ast.literal_eval(get_new())
        ng = ('ng' in n and n['ng'])
        time.sleep(0.1)

set_disc()
s.close()
