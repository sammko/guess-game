import ast
import gtk
import socket
import sys
import threading
import time


class CStrings():
    NEXTROUND = "Next round starts in %s seconds."
    SELECTJOB = "Select your job"
    ENTRYJOB = "Job:"
    ENTRYDESCRIPTION = "Description:"
    ID = "Your ID is "
    POINTS = "You currently have %s points"
    SUBMIT = "Submit"
    GUESSTITLE = "You can guess now"
    NOTGUESSED = "Your job has not been guessed yet."
    GUESSED = "Your job has been guessed."
    GUESSBTN = "Guess it!"
    NOTHINGGUESS = "You have nothing else left to guess.."
    TOOSHORT = "Your entry appears to be too short."
    WAIT = "Waiting for other players..."

Strings = CStrings()

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

    def __init__(self, sock):
        self.socket = sock

    def dispatch(self, packet):
        self.socket.send(packet.get_len())
        ack = self.socket.recv(4)
        if ack == "_ACK":
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


class SharedData():
    pts = 0
    v = -1
    jg = -1
    gotinit = False
    job = []  # JOB NAME
    des = []  # JOB DESCRIPTION
    con = []  # CONNECTED?
    gus = []  # GUESSED?
    dif = []  # DIFFICULTY
    gws = False
    idn = 0
    ready = False
    mjob = ''
    mdes = ''


class SelectWindow(gtk.Window):

    def __init__(self):

        self.flag = False
        gtk.Window.__init__(self)
        self.set_title(Strings.SELECTJOB)
        self.set_border_width(12)

        self.vbox = gtk.VBox(spacing=6)
        self.add(self.vbox)

        hbox = gtk.HBox(spacing=6)
        label = gtk.Label(Strings.ENTRYJOB)
        hbox.pack_start(label, False, False, 0)
        self.jobfield = gtk.Entry()
        hbox.pack_start(self.jobfield, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)

        hbox = gtk.HBox(spacing=6)
        label = gtk.Label(Strings.ENTRYDESCRIPTION)
        hbox.pack_start(label, False, False, 0)
        self.descfield = gtk.Entry()
        hbox.pack_start(self.descfield, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)

        label = gtk.Label(Strings.ID + str(shared.idn))
        self.vbox.pack_start(label, False, False, 0)
        label = gtk.Label(Strings.POINTS % str(shared.pts))
        self.vbox.pack_start(label, False, False, 0)

        button = gtk.Button(Strings.SUBMIT)
        button.connect("clicked", self.button_clicked)
        self.vbox.pack_start(button, False, False, 0)


    def button_clicked(self, _):
        submit(self, self.jobfield.get_text(), self.descfield.get_text())

    def warn(self, text):
        if not self.flag:
            self.wlabel = gtk.Label("")
            self.wlabel.set_markup("<span foreground=\"red\">"+text+"</span>")
            self.vbox.pack_start(self.wlabel, False, False, 0)
            self.wlabel.show()
            self.flag = True


class SpinnerWindow(gtk.Window):

    def __init__(self, text):
        gtk.Window.__init__(self)
        self.set_title("")
        self.set_border_width(10)

        vbox = gtk.VBox(spacing=6)
        self.add(vbox)

        label = gtk.Label(text)
        vbox.pack_start(label, False, False, 0)
        spinner = gtk.Spinner()
        spinner.set_size_request(35, 35)
        vbox.pack_start(spinner, True, True, 0)

        spinner.start()


class GuessWindow(gtk.Window):

    def __init__(self, text):
        gtk.Window.__init__(self)
        self.set_title(Strings.GUESSTITLE)
        self.set_border_width(10)

        self.entries = []
        self.buttons = []

        self.vbox = gtk.VBox(spacing=6)
        self.add(self.vbox)

        self.sglabel = gtk.Label(Strings.NOTGUESSED)
        self.vbox.pack_start(self.sglabel, False, False, 0)
        sep = gtk.HSeparator()
        self.vbox.pack_start(sep, False, True, 4)

        for d, i in zip(text, range(len(text))):
            self.entries.append(None)
            self.buttons.append(None)
            if i != shared.idn and shared.con[i] == 1:
                label = gtk.Label(d)
                hbox = gtk.HBox(spacing=6)
                hbox.pack_start(label, False, False, 0)
                entry = gtk.Entry()
                entry.set_size_request(150, -1)
                self.entries[i] = entry
                btn = gtk.Button(Strings.GUESSBTN)
                btn.set_name(str(i))
                entry.connect("activate", self.emulate_clicked, btn)
                self.buttons[i] = btn
                btn.connect("clicked", self.guess_clicked)
                hbox.pack_start(entry, True, True, 0)
                hbox.pack_start(btn, False, False, 0)
                self.vbox.pack_start(hbox, True, True, 0)

        self.label = gtk.Label(Strings.POINTS % str(shared.pts))
        self.vbox.pack_start(self.label, False, False, 0)

    def alldone(self):
        sep = gtk.HSeparator()
        self.vbox.pack_start(sep, False, True, 4)
        self.nlabel = gtk.Label(Strings.NOTHINGGUESS)
        self.vbox.pack_start(self.nlabel, False, False, 0)
        self.spinner = gtk.Spinner()
        self.spinner.set_size_request(35, 35)
        self.vbox.pack_start(self.spinner, True, True, 0)
        self.spinner.start()
        self.nlabel.show()
        self.spinner.show()
        sep.show()

    def selfguess(self):
        self.sglabel.set_text(Strings.GUESSED)

    def nextr(self):
        self.spinner.hide()
        self.nlabel.hide()
        self.resize(100, 100)
        self.time = ROUNDDELAY / 50
        self.prog = gtk.ProgressBar()
        self.vbox.pack_start(self.prog, False, True, 0)
        self.prog.show()
        self.prog.set_text(Strings.NEXTROUND % '5')
        gtk.timeout_add(50, updateprog)

    def updateprog(self):
        self.prog.set_fraction(self.time/100.0)
        self.prog.set_text(Strings.NEXTROUND % str(int(self.time*0.05)+1))
        self.time -= 1.0
        if self.time > 0:
            gtk.timeout_add(50, updateprog)

    def emulate_clicked(self, n, btn):
        btn.clicked()

    def guess_clicked(self, button):
        _id = int(button.get_name())
        ## print(self.entries[_id].get_text())
        guess = self.entries[_id].get_text()
        if guess.lower() == shared.job[_id].lower():
            shared.jg = _id

    def block_field(self, _id):
        self.buttons[_id].set_sensitive(False)
        self.entries[_id].set_sensitive(False)
        self.entries[_id].set_text(shared.job[_id])


class NetThread(threading.Thread):

    def __init__(self, _shared):
        threading.Thread.__init__(self)
        self.shared = _shared
        gtk.gdk.threads_init()
        self._die = False

    def die(self):
        self._die = True

    def checkdie(self):
        if self._die == True:
            raise SystemExit

    def run(self):
        global sw
        try:
            while True:
                self.checkdie()
                while not self.shared.ready:
                    self.checkdie()
                    time.sleep(0.05)
                    pass
                set_jd(self.shared.mjob, self.shared.mdes)
                set_ready()
                while not self.shared.gotinit:
                    self.checkdie()
                    newdat = ast.literal_eval(get_new())
                    if 'jobs' in newdat:
                        self.shared.job = newdat['jobs']
                        self.shared.gotinit = True
                    if 'diffs' in newdat:
                        self.shared.dif = newdat['diffs']
                    if 'descs' in newdat:
                        self.shared.des = newdat['descs']
                    if 'conn' in newdat:
                        self.shared.con = newdat['conn']
                    time.sleep(0.05)
                self.shared.v = 0
                run = True
                self.shared.gus = [0 for _ in range(len(self.shared.job))]
                while run:
                    self.checkdie()
                    if self.shared.jg > -1:
                        set_guessed(self.shared.jg)
                        self.shared.jg = -1
                        shared.pts = get_points()
                    newdat = ast.literal_eval(get_new())
                    time.sleep(0.05)
                    if 'guessed' in newdat:
                        self.shared.gus = newdat['guessed']
                        ## print self.shared.gus
                    for g, i in zip(self.shared.gus, range(len(self.shared.gus))):
                        if g > 0 and i is not self.shared.idn:
                            self.shared.gw.block_field(i)
                        if g > 0 and i is self.shared.idn:
                            self.shared.gw.selfguess()
                    if min([i for i, q, n in zip(self.shared.gus, self.shared.con,
                            range(len(self.shared.con))) if q == 1 and
                            n != self.shared.idn]) == 1:
                            run = False

                self.shared.v = 1
                self.shared.ready = False
                set_end()
                ng = False
                self.shared.gotinit = False

                while not ng:
                    n = ast.literal_eval(get_new())
                    if 'guessed' in n:
                        for g, i in zip(n['guessed'], range(len(n['guessed']))):
                            if g > 0 and i is self.shared.idn:
                                self.shared.gw.selfguess()
                    self.checkdie()
                    ng = ('ng' in n and n['ng'])
                    time.sleep(0.1)

                self.shared.v = 2
        except (KeyboardInterrupt, SystemExit):
            set_disc()
            s.close()

def submit(sender, job, desc):
    desc = desc.strip().lower()
    job = job.strip().lower()
    if len(desc) > 0 and len(job) > 0:
        shared.mdes = desc
        shared.mjob = job
        shared.ready = True
        sw.move(sender.get_position()[0], sender.get_position()[1])
        sw.show_all()
        sender.destroy()
    else:
        sender.warn(Strings.TOOSHORT)


def checkdead():
    gtk.timeout_add(50, checkdead)
    if shared.gws:
        shared.gw.label.set_text(Strings.POINTS % str(shared.pts))
    if shared.v == 0:
        shared.gw = GuessWindow(shared.des)
        connect(shared.gw)
        shared.gws = True
        shared.gw.move(sw.get_position()[0], sw.get_position()[1])
        shared.gw.show_all()
        sw.hide()
    elif shared.v == 1:
        shared.gw.alldone()
    elif shared.v == 2:
        shared.gw.nextr()
        gtk.timeout_add(ROUNDDELAY, nextround)
    shared.v = -1

def nextround():
    shared.aw = SelectWindow()
    connect(shared.aw)
    shared.aw.move(shared.gw.get_position()[0],
                   shared.gw.get_position()[1])
    shared.gw.destroy()
    shared.gws = False
    shared.aw.show_all()

def connect(w):
    w.connect('delete-event', stopall)

def stopall(a, b):
    n.die()
    gtk.main_quit()

def updateprog():
    shared.gw.updateprog()

pos = (400, 400)


try:
    with open('ip') as f:
        TCP_IP = f.read().strip()
    if len(TCP_IP) == 0:
        raise IOError
except IOError:
    try:       
        TCP_IP = sys.argv[1].strip()
    except IndexError:
        TCP_IP = '127.0.0.1'
        pass
    pass

shared = SharedData()

ROUNDDELAY = 5000

TCP_PORT = 28136

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

p = PacketDispatcher(s)

shared.idn = get_id()

gtk.timeout_add(50, checkdead)

w = SelectWindow()
connect(w)
w.move(pos[0], pos[1])
w.show_all()

sw = SpinnerWindow(Strings.WAIT)
connect(sw)

n = NetThread(shared)
n.start()

gtk.main()
