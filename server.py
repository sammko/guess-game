#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: sammko
# @Date:   2014-03-26 17:59:06
# @Last Modified by:   sammko
# @Last Modified time: 2014-04-17 11:49:27

import socket
import threading
import time

ANSI = True


class Colors():
    ESC = chr(0x1B) + '['
    RED = ESC + '31m'
    YELLOW = ESC + '33m'
    CYAN = ESC + '36m'
    GREEN = ESC + '32m'
    BLUE = ESC + '34m'
    RESET = ESC + '0m'


colors = Colors()

if not ANSI:
    colors.RED = ''
    colors.YELLOW = ''
    colors.CYAN = ''
    colors.GREEN = ''
    colors.BLUE = ''
    colors.RESET = ''

try:
    import colorama
    colorama.init()
    colors.RED = colorama.Fore.RED
    colors.YELLOW = colorama.Fore.YELLOW
    colors.CYAN = colorama.Fore.CYAN
    colors.GREEN = colorama.Fore.GREEN
    colors.BLUE = colorama.Fore.BLUE
    colors.RESET = colorama.Fore.RESET
except ImportError:
    pass

diacritics = [['á', 'a'],['Á', 'A'],['č', 'c'],['Č', 'C'],['ď', 'd'],['Ď', 'D'],['é', 'e'],['É', 'E'],['í', 'i'], 
              ['Í', 'I'],['ľ', 'l'],['Ľ', 'L'],['ĺ', 'l'],['Ĺ', 'L'],['ň', 'n'],['Ň', 'N'],['ó', 'o'],['Ó', 'O'], 
              ['ô', 'o'],['ŕ', 'r'],['Ŕ', 'R'],['š', 's'],['Š', 'S'],['ť', 't'],['Ť', 'T'],['ú', 'u'],['Ú', 'U'], 
              ['ý', 'y'],['Ý', 'Y'],['ž', 'z'],['Ž', 'Z'],['ä', 'a']]

class SharedData():
    #TREE INTITIALIZER

    des =     []
    red =    [  ]
    con =   [    ]
    pnt =  [      ]
    job = [        ]
    dat =     []
    gus =     []

    gupdate = False
    run = True
    accept = True
    dif = []
    end = []



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
    def __init__(self, _socket):
        self.socket = _socket

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


class LoopThread(threading.Thread):
    def __init__(self, shared):
        threading.Thread.__init__(self)
        self.shared = shared
        self.gupsec = False

    def broadcast(self, data):
        for _i in range(len(self.shared.red)):
            if self.shared.con[_i] == 1:
                self.shared.dat[_i].update(data)

    def is_ready(self):
        try:
            return min([r for r, c in
                        zip(self.shared.red, self.shared.con) if c == 1])
        except:
            return None

    def getend(self):
        try:
            return min([r for r, c in
                        zip(self.shared.end, self.shared.con) if c == 1])
        except:
            return None

    def getgus(self):
        try:
            return min([r for r, c in
                        zip(self.shared.gus, self.shared.con) if c == 1])
        except:
            return None

    def printstat(self):
        print(colors.YELLOW + "\nPoints:  " + str(self.shared.pnt))
        print("Playing: " + str(self.shared.con))
        print("Guessed: " + str(self.shared.gus) + '\n' + colors.RESET)

    def run(self):
        while self.shared.run:
            time.sleep(0.05)
            cnt = len(self.shared.red)

            if cnt > 1 and self.shared.accept and self.is_ready() > 0:

                print(colors.RED + "EVERYONE READY")
                self.shared.accept = False
                self.shared.red = [0 for _ in range(cnt)]

                self.broadcast({'descs': self.shared.des,
                                'jobs': self.shared.job,
                                'diffs': self.shared.dif,
                                'conn': self.shared.con})

            if self.shared.gupdate:
                print(colors.CYAN + 'Guess BCAST')
                self.broadcast({'guessed': self.shared.gus})
                self.shared.gupdate = False
                self.gupsec = True
                self.printstat()

            if self.gupsec:
                print(colors.CYAN + 'Guess SEC BCAST')
                self.broadcast({'guessed': self.shared.gus})
                self.gupsec = False

            if cnt > 1 and self.getgus() > 0:
                print(colors.RED + 'EVERYTHING GUESSED; NEW ROUND')
                while self.getend() == 0:
                    time.sleep(0.1)
                print(colors.RED + 'ALL CLIENTS DONE')
                self.broadcast({'ng': True})
                self.shared.accept = True
                self.shared.gus = [0 for _ in range(cnt)]
                self.shared.end = [0 for _ in range(cnt)]


class ClientThread(threading.Thread):
    def __init__(self, _ip, _port, _socket, _i, shared):
        threading.Thread.__init__(self)
        self.ip = _ip
        self.port = _port
        self.socket = _socket
        self.i = _i
        self.a = 1
        self.disp = PacketDispatcher(_socket)
        self.shared = shared
        shared.job.append("If you see this something is broken.")
        shared.des.append("If you see this something is broken.")
        shared.red.append(0)
        shared.pnt.append(0)
        shared.dat.append({})
        shared.end.append(0)
        shared.gus.append(0)
        shared.dif.append(1)
        shared.con.append(1)
        print(colors.GREEN + "[+]" + colors.RESET + " New thread ("
                           + str(_i) + ") for " + _ip + ":" + str(_port))

    def run(self):

        data = "."
        try:
            while True and self.a and self.shared.run:
                data = self.disp.receive().get_payload()
                if not len(data):
                    break
                self.parse_cmd(data)
            self.socket.close()
        except IOError:
            pass
        self.shared.con[self.i] = 0
        print(colors.RED + "[-]" + colors.RESET
                         + " Client (" + str(self.i) + ") disconnected...\n")

    def parse_cmd(self, data):
        if data == "+SEJ":
            dmp = self.disp.receive().get_payload()
            dmp = dmp.strip().lower()
            for u in diacritics:
                dmp = dmp.replace(u[0], u[1])
            self.shared.job[self.i] = dmp

        if data == "+SEI":
            dmp = self.disp.receive().get_payload()
            self.shared.dif[self.i] = dmp

        if data == "-NEW":
            self.disp.dispatch(Packet(str(self.shared.dat[self.i])))
            self.shared.dat[self.i] = {}

        if data == "+SED":
            dmp = self.disp.receive().get_payload()
            self.shared.des[self.i] = dmp

        if data == "+GUS":
            dmp = int(self.disp.receive().get_payload())
            self.shared.gus[dmp] = 1
            self.shared.gupdate = True
            self.shared.pnt[self.i] += 10
            print(colors.CYAN + "Client (" + str(self.i)
                              + ") GUESSED " + str(dmp))

        if data == "-GID":
            self.disp.dispatch(Packet(str(self.i)))

        if data == "-GPT":
            self.disp.dispatch(Packet(str(self.shared.pnt[self.i])))

        if data == "/RED":
            self.shared.red[self.i] = 1
            print(colors.CYAN + "Client (" + str(self.i)
                              + ") READY" + colors.YELLOW)
            print('\t' + str(self.shared.job[self.i]))
            print('\t' + str(self.shared.des[self.i]))
            print('\t' + str(self.shared.dif[self.i]))

        if data == "/DSC":
            self.a = 0

        if data == "/END":
            self.shared.end[self.i] = 1


host = "0.0.0.0"
port = 28136

tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

tcpsock.bind((host, port))
threads = []
i = 0

print(colors.BLUE + "Listening on " + host + ":"
                  + str(port) + colors.RESET + "\n\n")

s = SharedData()

LoopThread(s).start()

try:
    while True:
        tcpsock.listen(4)
        (clientsock, (ip, port)) = tcpsock.accept()
        if s.accept:
            newthread = ClientThread(ip, port, clientsock, i, s)
            i += 1
            newthread.start()
            threads.append(newthread)
        else:
            clientsock.close()
except (KeyboardInterrupt, SystemExit):
    print("Quitting")
    s.run = False
for t in threads:
    t.join()
