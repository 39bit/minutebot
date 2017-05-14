import json, urllib.error, urllib.parse, urllib.request, socket
SENT = False
class TelegramBot():
    class attribute_dict():
        def __init__(self, data):
            self.__data__ = data
        def __getattr__(self, index):
            if index == "__data__": return object.__getattr__(self, "__data__")
            try:
                return self.__getitem__(index)
            except KeyError:
                raise AttributeError
        def __getitem__(self, index):
            return self.__data__[index]
        def __setattr__(self, index, value):
            if index == "__data__": return object.__setattr__(self, "__data__", value)
            self.__setitem__(index)
        def __setitem__(self, index, value):
            self.__data__[index] = value
        def __delattr__(self, index, value):
            if index == "__data__": return object.__delattr__(self, "__data__", value)
            self.__delitem__(index)
        def __delitem__(self, index, value):
            del self.__data__[index]
        def __repr__(self):
            return repr(self.__data__)
        def __iter__(self):
            return iter(self.__data__)
        def __len__(self):
            return len(self.__data__)
        def keys(self):
            return self.__data__.keys()
        def has(self, key):
            return key in self.__data__.keys() and self.__data__[key] != None
    def __init__(self, token):
        self.token = token
        self.retry = 0
    def __getattr__(self, attr):
        return self.func_wrapper(attr)
    def func_wrapper(self, fname):
        def func(self, unsafe, **kw):
            url_par={}
            for key in kw.keys():
                if kw[key] != None:
                    url_par[key] = urllib.parse.quote_plus(TelegramBot.escape(kw[key]))
            url = ("https://api.telegram.org/bot" + self.token + "/" + (fname.replace("__UNSAFE","") if fname.endswith("__UNSAFE") else fname) + "?" +
                    "&".join(map(lambda x:x+"="+url_par[x],url_par.keys())))
            RETRY = True
            while RETRY:
                try:
                    with urllib.request.urlopen(url, timeout=10) as f:
                        raw = f.read().decode('utf-8')
                    RETRY = False
                except socket.timeout:
                    raise ValueError("timeout")
                except BaseException as e:
                    print(str(e))
                    time.sleep(0.5)
                    if "too many requests" in str(e).lower():
                        self.retry += 1
                        time.sleep(self.retry * 5)
                    elif "unreachable" in str(e).lower() or "bad gateway" in str(e).lower() or "name or service not known" in str(e).lower() or  "network" in str(e).lower() or "handshake operation timed out" in str(e).lower():
                        time.sleep(3)
                    elif "bad request" in str(e).lower() and not unsafe:
                        print(fname)
                        print(json.dumps(url_par))
                        traceback.print_exc()
                        return
                    else:
                        raise e
            self.retry = 0
            return TelegramBot.attributify(json.loads(raw))
        return lambda **kw:func(self,fname.endswith("__UNSAFE"),**kw)
    @staticmethod
    def escape(obj):
        if type(obj) == str:
            return obj
        else:
            return json.dumps(obj).encode('utf-8')
    @staticmethod
    def attributify(obj):
        if type(obj)==list:
            return list(map(TelegramBot.attributify,obj))
        elif type(obj)==dict:
            d = obj
            for k in d.keys():
                d[k] = TelegramBot.attributify(d[k])
            return TelegramBot.attribute_dict(d)
        else:
            return obj

bot = TelegramBot("BOT_TOKEN_GOES_HERE")
TARGET_CHANNEL = CHANNEL_ID_GOES_HERE

import time, pickle, os.path, traceback, threading
ME = bot.getMe().result
ID = ME.id
UN = ME.username

lastpost = 0

def dictify(d):
    if type(d) == TelegramBot.attribute_dict:
        return d.__data__
    return d

def superdictify(obj):
    if type(obj)==list:
        return list(map(superdictify,obj))
    elif type(obj)==TelegramBot.attribute_dict:
        d = obj
        for k in d.keys():
            d[k] = superdictify(d[k])
        return dictify(d)            
    elif type(obj)==dict:
        d = obj
        for k in d.keys():
            d[k] = superdictify(d[k])
        return d 
    else:
        return obj

def load():
    global lastpost
    if os.path.isfile("minutebot.dat"):
        try:
            with open("minutebot.dat", "rb") as f:
                lastpost, = pickle.load(f)            
        except:
            pass

import copy
def save(reason):
    print("saving <" + reason + ">")
    with open("minutebot.dat", "wb") as f:
        pickle.dump((lastpost,), f)
    print("saved")
        
from socket import AF_INET, SOCK_DGRAM
import sys
import socket
import struct, time

# NTP time code, author unknown
def getNTPTime(host = "pool.ntp.org"):
    port = 123
    buf = 1024
    address = (host,port)
    msg = b'\x1b' + (47 * b'\0')

    # reference time (in seconds since 1900-01-01 00:00:00)
    TIME1970 = 2208988800 # 1970-01-01 00:00:00

    # connect to server
    client = socket.socket( AF_INET, SOCK_DGRAM)
    client.settimeout(5)
    client.sendto(bytes(msg), address)
    msg, address = client.recvfrom( buf )

    t = struct.unpack( "!12I", msg )[10]
    t -= TIME1970
    return t

def getFixedTime():
    return int(time.time()) - NTPOFF

# synchronize to NTP
def resync():
    global ntp, NTPOFF
    ntp = -1
    while ntp < 0:
        try:
            ntp = getNTPTime()
        except:
            time.sleep(2)
            pass
    print(ntp)
    NTPOFF = int(time.time()) - ntp 
    print(getFixedTime())

resync()

load()

UPD_COUNTER = 0
SAVE_EVERY_N_UPDATES = 16

import os, sys, datetime, calendar
tried_to = 0
saferes = True
lastsec = -1
try:
    # auto restart system
    def autoreset():
        time.sleep(600)
        while not saferes:
            time.sleep(0.5)
            tried_to = 10000
        time.sleep(30)
        save("quitting - backup thread")
        os.execl(sys.executable, sys.executable, *sys.argv)      
    threading.Thread(target=autoreset, daemon=True).start()
    while True:
        tried_to += 1
        if (tried_to % 2500) == 0:
            save("temp")
            resync()
        if tried_to >= 25000:
            save("quitting")
            os.execl(sys.executable, sys.executable, *sys.argv)
        saferes = False         
        now = time.time()
        if lastsec >= 0:
            if abs(lastsec - now) > 2:
                resync()
        lastsec = now
        dtnow = datetime.datetime.utcfromtimestamp(getFixedTime())
        if (dtnow.second<1 and (now-lastpost)>4) or (now-lastpost)>63:
            iso = dtnow.isoformat().split(".")[0][:-2]+"00Z"
            try:
                bot.sendMessage__UNSAFE(chat_id=TARGET_CHANNEL,
                            text=iso + "\n" + str(int(calendar.timegm(datetime.datetime.strptime(iso,"%Y-%m-%dT%H:%M:%SZ").timetuple()))))
                print("poll " + str(time.time()))
                lastpost = now
            except: 
                pass
        time.sleep(0.2)
except KeyboardInterrupt as e:
    save("Quit")
except BaseException as e:
    save("Exception")
    traceback.print_exc()
