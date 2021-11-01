#!/usr/bin/env python
# By jajito
# https://github.com/jajito


import sys
import time
import datetime
import subprocess
import os
import os.path
import signal
import random
from subprocess import PIPE, Popen
import rtmidi
from rtmidi.midiutil import open_midiinput,  open_midioutput
from subprocess import Popen
from subprocess import PIPE

MIDI_NOTE_REC = 95
MIDI_NOTE_PLAY = 94
MIDI_NOTE_STOP = 93
MIDI_NOTE_REW = 91
MIDI_NOTE_FF = 92

port = 1

lcd_header = [0xF0,0x00,0x00,0x66,0x14,0x12,0x00]
lcd_sysex_end = 0xF7
timetowait = 0.05 #time to wait after sending midi messages

#mediafolder = "/media/USBXFS/" # recording folder
MP3_folder = "/share/MP3"
channels_to_record = 16
test_mode = False

midiout = rtmidi.MidiOut()
midiout.open_port(port)

record_start = datetime.datetime.now()

rec_stop_alert = False
change_mode_alert = False
recording = False
playing_record = False
playing_mp3 = False
play_mode_mp3 = False
#actual_option = 0
playlist_mode = False
random_mode = False

modes = [(0 , "Player"),
        (1 , "Setup")]
modes_lenght = len(modes)
mode = modes [0]
print "Mode ", mode

formats =[".w64", ".caf"]
play_formats=(".mp3",".w64",".caf",".wav")
format_num = 0
print "format ", formats[format_num]

play_modes = [( False, False),
              ( True, False),
              ( True, True)] # playlist_mode , random_mode
play_mode_number = 1
print play_modes[play_mode_number]

actual_mp3_folder = 0

#channel = channels_to_record
modenew = mode[0]

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):# for readable results of diskspace
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def minutestorecord(chann = channels_to_record):
    statvfs = os.statvfs(mediafolder)
    #print statvfs
    diskabailable = statvfs.f_frsize * statvfs.f_bavail
    bitesporsegundo = 146227 * chann
    segundosavailable = diskabailable / bitesporsegundo
    segundoshumansize = str(datetime.timedelta(seconds=segundosavailable))
    return segundoshumansize
def diskavailable():
    statvfs = os.statvfs(mediafolder)
    diskabailable = statvfs.f_frsize * statvfs.f_bavail
    return humansize(diskabailable)

def check_X32_ALSA_CARD():
    p = subprocess.Popen("cat /proc/asound/cards", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.readlines()
    for i in range(len(result)):
        result[i] = result[i].strip() # strip out white space
        print result[i]
        if "XUSB" in result[i]:
            print "XUSB is ALSA CARD number :", result[i][0]
            X32in = result[i][0]
            return X32in

        else:
            print "X32 not found"
            X32in = 0
    return X32in

def getCol(col, line):
    p1 = line.find(col)
    if p1<0 : return ""
    p2 = p1 + len(col) + 1
    p3 = line.find('"',p2+1)
    return line[p2+1:p3]

def mount_not_mounted():
    # mount all partition by neoedmund
    print "Mounting USBs"
    data_stream = Popen(["/bin/lsblk", "-P", "-o", "FSTYPE,UUID,MOUNTPOINT,KNAME"], stdout=PIPE)
    data=[]
    for line in data_stream.stdout:
        #print  "line ", line
        fstype = getCol("FSTYPE", line)
        if fstype=="": continue # no fs
        mountpoint = getCol("MOUNTPOINT", line)
        if mountpoint!="":continue  # already mounted
        uuid = getCol("UUID", line)
        kname = getCol("KNAME", line)
        data.append((kname))
    for (kname) in data:
        print("mkdir /media/%s" % (kname))
        print("mount /dev/%s /media/%s" % (kname, kname))
        os.system("sudo mkdir /media/%s" % (kname))
        os.system("sudo mount /dev/%s /media/%s" % (kname, kname))
        print("sudo chmod 777 /media/%s" % (kname))
        os.system("sudo chmod 777 /media/%s" % (kname))

def unmount_mounted():
    print "Unmounting USBs"
    data_stream = Popen(["/bin/lsblk", "-P", "-o", "FSTYPE,UUID,MOUNTPOINT,KNAME,SIZE"], stdout=PIPE)
    data=[]
    for line in data_stream.stdout:
        #print "line ", line
        fstype = getCol("FSTYPE", line)
        if fstype=="": continue # no fs
        mountpoint = getCol("MOUNTPOINT", line)
        if mountpoint!="" and "sd" in mountpoint:#continue  # already mounted
            #uuid = getCol("UUID", line)
            kname = getCol("KNAME", line)
            #size = getCol("SIZE", line)
            data.append((kname))
    for (kname) in data:
        print("umount /dev/%s" %(kname))
        os.system("umount /dev/%s" %(kname))

def check_mounted():
    data_stream = Popen(["/bin/lsblk", "-P", "-o", "FSTYPE,UUID,MOUNTPOINT,KNAME,SIZE"], stdout=PIPE)
    data=[]
    for line in data_stream.stdout:
        #print "line ", line
        fstype = getCol("FSTYPE", line)
        if fstype=="": continue # no fs
        mountpoint = getCol("MOUNTPOINT", line)
        if mountpoint!="" and "sd" in mountpoint:#continue  # already mounted
            uuid = getCol("UUID", line)
            kname = getCol("KNAME", line)
            size = getCol("SIZE", line)
            data.append((kname, fstype, mountpoint, uuid, size))
    return data


def strip_clean():
    sysex = list(lcd_header)
    for i in range(112):
        sysex.append((0x00))
    sysex.append(lcd_sysex_end)
    assert sysex[0] == 0xF0 and sysex[-1] == 0xF7
    midiout.send_message(sysex)
    time.sleep(timetowait)

def update_dir_old(folder):
    print "update dir "
    files = os.listdir(folder)
    paths = [os.path.join(folder, basename) for basename in files]
    paths.sort()
    dirs_number = len (paths)
    print "Updated dir. Number of files =", dirs_number
    print "paths ", paths
    return dirs_number, paths

def update_dir(folder):
    print "update dir "
    result = os.listdir(folder)
    paths = [os.path.join(folder, basename) for basename in result]
    dirs = []
    files = []
    for file in paths:
        if os.path.isdir(file): dirs.append(file)
        if os.path.isfile(file):
            if file.endswith(play_formats):
                files.append(file)
    dirs.sort()
    files.sort()
    fildir = dirs + files
    if folder == mediafolder[:-1]:
        print "uptdating mediafolder, invert order"
        fildir.sort(reverse=True)
    dirs_number = len (fildir)
    #print "Updated dir. Number of files =", dirs_number
    #print "paths ", fildir
    return dirs_number, fildir

def info_file_old(file):
    print "info file"
    print "File to check ", file
    if file[-5] == "." and file[-4] != ".":# is file
        length = str(os.popen("soxi -d " + file).readlines())[3:10]
        print "is file, file length ", length
        return length
    else:
        print "is folder ", file
        print os.listdir(file[1:-1])
        files_number = str(len((os.listdir(file[1:-1]))))
        print "number of files ", files_number
        txt = files_number[0:2] + (3 - len(files_number)) * " " + "File"
        print "number of files ", txt
        return txt

def info_file(folder):
    #print "File to check ", folder
    #if file[-5] == "." and file[-4] != ".":# is file
    if os.path.isfile(folder): #is file
        length = str(os.popen("soxi -d " + "'" +folder+"'").readlines())[3:10]
        #print "is file, file length ", length
        return length
    else:
        #print "is folder ", folder
        result = os.listdir(folder)
        paths = [os.path.join(folder, basename) for basename in result]
        dirs = []
        files = []
        for file in paths:
            if os.path.isdir(file): dirs.append(file)
            if os.path.isfile(file):
                if file.endswith(play_formats):
                    files.append(file)
        fildir = dirs + files
        files_number = str(len((fildir)))
        #print "number of files ", files_number
        txt = files_number[0:2] + (3 - len(files_number)) * " " + "File"
        #print "number of files ", txt
        return txt

def buttons_out(button, onoff):
    #midiout = rtmidi.MidiOut()
    #midiout.open_port(port)
    midiout.send_message([144, button, onoff])
    time.sleep(timetowait)
    #midiout.close_port()
    #del midiout


def send_lcd_2( actiontxt , trktxt ="", trknmbr="", folder_txt="", filetxt="",trklength="       "): # first line, mode an so
    #offset = 56
    line_1 = "PLAYER "+ "       "+ "Folder:"+ (folder_txt[0:35] + (35 - len(folder_txt))*" ")
    line_2 = (actiontxt[0:7] + (7 - len(actiontxt)) * " " + (6-len(trktxt+trknmbr))*" "+ (trktxt+"/"+trknmbr)  +
                    trklength + filetxt[0:35] + (35 - len(filetxt)) * " ")

    # ("Selected Channels   "[:-len(str(channels_to_record))] + str(channels_to_record)))
    text_to_send = line_1+line_2
    sysex = list(lcd_header)
    for character in text_to_send:
        sysex.append(ord(character))
    sysex.append(lcd_sysex_end)
    #sysex[6]= offset
    assert sysex[0] == 0xF0 and sysex[-1] == 0xF7
    midiout.send_message(sysex)
    time.sleep(timetowait)

def send_lcd_record(rec_time):
    global channels_to_record
    #text_to_send = "Rec" + str(channels_to_record) + (2 - len(str(channels_to_record))) * " " + "ch" + str(rec_time)
    text_to_send = "Rec" + (2 - len(str(channels_to_record))) * " " + str(channels_to_record)  + "ch" + str(rec_time)
    sysex = list(lcd_header)
    for character in text_to_send:
        sysex.append(ord(character))
    sysex.append(lcd_sysex_end)
    # sysex[6]= offset
    assert sysex[0] == 0xF0 and sysex[-1] == 0xF7
    midiout.send_message(sysex)
    time.sleep(timetowait)

def update_records_list(folder):
    files = os.listdir(folder)
    paths = [os.path.join(folder, basename) for basename in files]
    records_number = len (paths)
    #print "Updated records list . Number of records =", records_number
    return records_number, paths

def txt_to_sysex(text):
    sysex = lcd_header
    sysex.append(lcd_offset)
    for character in text:
        sysex.append(ord(character))
    sysex.append(lcd_sysex_end)
    return sysex

def grabar():
    if test_mode == True:
        print ("demo mode Recording")
        return
    #grabadora_status["rec"] = True
    global record_start
    record_start = datetime.datetime.now()
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")+formats[format_num]
    print ("Recording ", record_start)
    grabando = "rec -q --buffer 1048576 -c " + str(channels_to_record) + " -b 24 " + mediafolder + filename
    #grabando = "AUDIODEV=hw:XUSB rec -q --buffer 1048576 -c " + str(channels_to_record) + " -b 24 " + mediafolder + filename

    print (grabando)
    send_lcd_record("0:00:00")
    global rec_process
    rec_process = subprocess.Popen(grabando, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

def fingrabar():
    if test_mode == True:
        print ("demo mode End Recording")
        return
    #grabadora_status["rec"] = False
    print ('Recording Stopped :', (datetime.datetime.now()))
    global rec_process
    #esto mata el proceso de grabacion
    os.killpg(os.getpgid(rec_process.pid), signal.SIGTERM)
    print ("REC PROCESS TERMINATE")
    grabaend = datetime.datetime.now()
    global record_start
    send_lcd_record("Stopped")
    if record_start == 0:
        #print 'no hay nada en record_start'
        pass

    else:
        recordtime = grabaend - record_start
        print ('Total Recording time = ', str(recordtime)[:-7])
        #lcdimprime('Recorded Time:',str(recordtime)[:-7])
    #ready_to_rumble()

def playrecording(file, mp3_to_play):
    if mp3_to_play == False:
        print "Playing from mediafolder"
        reproduciendo = "play -q " + file
    elif mp3_to_play == True:
        print "Playing MP3"
        reproduciendo = "mpg123 -C --no-control " + file
    print(reproduciendo)
    #print("Playing : ", file)
    if test_mode == True:
        print ("demo mode Playing")
        return

    global play_recorded_process
    play_recorded_process = subprocess.Popen(reproduciendo, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

def playing_stop():
    if test_mode == True:
        print ("demo mode Stop Playing")
        return
    print ("Playing stopped")
    global play_recorded_process
    os.killpg(os.getpgid(play_recorded_process.pid), signal.SIGTERM)
    print ("Play process terminated")


class MidiInputHandler(object):
    def __init__(self, port):
        self.port = port
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        note = message[1]


        global rec_stop_alert
        global change_mode_alert
        global recording
        global playing_record
        global playing_mp3
        global play_mode_mp3
        global actual_record
        global mediafolder
        global records_number
        global records_list
        global channels_to_record
        global channel
        global actual_mp3_folder
        global mp3_folders_list
        global mp3_folders_number
        global mode
        global modes_lenght
        global modenew
        global actual_dir
        global dir_to_explore
        global dir_number
        global channel_temp
        global formats
        global format_num
        global playlist_mode
        global random_mode
        global play_modes
        global play_mode_number
        global initial_dirs
        global dir_act
        global mp3_to_play


        if mode[0] == 0: #FILES

            if message == [144, MIDI_NOTE_STOP, 127]: # STOP
                buttons_out(MIDI_NOTE_STOP, 127)
                if rec_stop_alert == True:
                    print ("Stop Recording")
                    buttons_out(MIDI_NOTE_REC, 0)
                    fingrabar()
                    records_number, records_list = update_records_list(mediafolder)
                    actual_record = records_number
                    rec_stop_alert = False
                    recording = False
                else:
                    print("Stop multitrak")
                    playing_record = False
                    buttons_out(MIDI_NOTE_PLAY, 0)
                    playing_stop()
            if message == [144, MIDI_NOTE_STOP, 0]: # STOP
                buttons_out(MIDI_NOTE_STOP, 0)

            if message == [144, MIDI_NOTE_PLAY, 0]: # PLAY

                    #print "selected folder ", actual_dir, dir_to_explore[actual_dir]
                    if dir_to_explore[actual_dir] == "Setup":
                        print   " Setup selected"
                        init_setup()
                        mode = modes[1]

                    if dir_to_explore[actual_dir] == "(..)": # back to previous folder

                        #print "dir to explore no ni na ", dir_to_explore
                        #print "initial dirs ", initial_dirs
                        if len(dir_to_explore) == 1:
                            path_act = dir_act
                        else:
                            path_act = os.path.dirname(dir_to_explore[actual_dir+1])
                        #print "actuallll dir" , path_act

                        if (str(path_act)) in initial_dirs: # initial dir
                            print "initial dir"
                            dir_to_explore = initial_dirs
                            dir_number = len(dir_to_explore)
                            actual_dir = 0
                            #print "previous dir number initial dirs ", dir_number, " dir to explore ", dir_to_explore
                            file_length = info_file((dir_to_explore[actual_dir]))
                            #send_lcd_2("Selectd", str(actual_dir), str(dir_number-1),
                            #           (dir_to_explore[actual_dir]), "  rr  ", trklength= file_length)
                            txt_file = str(os.path.basename(dir_to_explore[actual_dir]))
                            txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))
                            send_lcd_2("Selectd", str(actual_dir), str(dir_number-1), txt_folder,
                                       txt_file, trklength= file_length)

                            return

                        else: # no initial dir
                            print "no initial dir"
                            path_prev = "/".join(path_act.split("/")[:-1])+"/"
                            print "previous dir", path_prev
                            dir_number, dir_to_explore = update_dir(path_prev)
                            dir_to_explore.insert(0, "(..)")
                            dir_number = dir_number + 1
                            txt_file = str(os.path.basename(dir_to_explore[actual_dir]))
                            if txt_file == "(..)":
                                txt_folder = str(os.path.dirname(dir_to_explore[actual_dir + 1]))
                                file_length = "Prev.  "
                            else:
                                txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))

                                file_length = info_file(txt_folder + "/" + txt_file)
                            send_lcd_2("Selectd", str(actual_dir), str(dir_number - 1), txt_folder,
                                       txt_file, trklength= file_length)

                    if os.path.isdir (dir_to_explore[actual_dir]) == True: # is folder
                        dir_act = dir_to_explore[actual_dir]
                        dir_number , dir_to_explore = update_dir(dir_to_explore[actual_dir])
                        print "dir act ", dir_act
                        dir_to_explore.insert(0, "(..)")
                        dir_number = dir_number + 1
                        actual_dir = 0
                        txt_file = str(os.path.basename(dir_to_explore[actual_dir]))
                        if txt_file == "(..)":
                            #print "actua dir ", actual_dir
                            #print "dir to explore ", dir_to_explore
                            #txt_folder = "holasss"
                            if len(dir_to_explore)==1:
                                txt_folder= dir_act
                            else:
                                txt_folder = str(os.path.dirname(dir_to_explore[actual_dir + 1]))
                            file_length = "Prev.  "
                        else:
                            print "dir to explore no p", dir_to_explore[actual_dir]
                            txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))
                            file_length = info_file(txt_folder + "/" + txt_file)
                        send_lcd_2("Selectd", str(actual_dir), str(dir_number - 1), txt_folder,
                                   txt_file, trklength= file_length)
                        playing_record = False

                    if os.path.isfile (dir_to_explore[actual_dir]) == True: #is file, play file
                        if playing_record == False:
                            playing_record = True
                            buttons_out(MIDI_NOTE_PLAY, 127)
                            txt_file = str(os.path.basename(dir_to_explore[actual_dir]))
                            print "txt file", txt_file
                            if txt_file == "(..)":
                                txt_folder = str(os.path.dirname(dir_to_explore[actual_dir + 1]))
                                file_length = "Prev.  "

                            else:
                                txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))
                                file_length = info_file(txt_folder + "/" + txt_file)
                            send_lcd_2("Playing", str(actual_dir), str(dir_number-1),
                                   txt_folder, txt_file, trklength= file_length)
                            #print "Playing ", dir_to_explore[actual_dir]
                            print "playing txt_folder ", txt_folder
                            #print "madiafolder ", mediafolder[:-1]
                            mp3_to_play = True
                            if txt_folder == mediafolder[:-1]:
                                print "playing recording from mediafolder"
                                #playlist_mode = False
                                mp3_to_play = False
                            if not playlist_mode:
                                #print "dir to explore ", dir_to_explore
                                #print "actual dir ", actual_dir
                                #print "dir to explore len ", len(dir_to_explore)
                                onlyfiles = dir_to_explore[actual_dir:]
                                #print "onlyfiles ", onlyfiles
                                #onlyfiles = dir_to_explore[actual_dir]
                                # files_to_play = "\"" + onlyfiles +"\""
                                paths_quotes = ["\"" + p + "\"" for p in onlyfiles]
                                files_to_play = " ".join([str(i) for i in paths_quotes])

                                print "files to play ", files_to_play

                            if playlist_mode:
                                onlyfiles = [f for f in os.listdir(txt_folder) if os.path.isfile(os.path.join(txt_folder, f))]

                                #print "onlyfiles ", onlyfiles
                                paths = [os.path.join(txt_folder, basename) for basename in onlyfiles]
                                #print paths
                                paths_quotes = ["\"" + p + "\"" for p in paths]
                                #paths_quotes = paths
                                #print "paths_quotes ", paths_quotes
                                if random_mode:
                                    random.shuffle(paths_quotes)
                                if not random_mode:
                                    #print "not random mode"
                                    paths_quotes.sort()
                                #print "paths_quotes ", paths_quotes
                                #files_to_play = paths_quotes
                                files_to_play = " ".join([str(i) for i in paths_quotes])
                                #print "actual dir ",
                            #print "files to play ", files_to_play
                            playrecording(files_to_play, mp3_to_play)
                        else:
                            print ("Already playing multitrak")

            if message == [144, MIDI_NOTE_REW, 127]: # REW
                buttons_out(MIDI_NOTE_REW, 127)
                print("Previous")
                actual_dir = min(max((actual_dir - 1), 0), dir_number)
                txt_file = str(os.path.basename(dir_to_explore[actual_dir]))

                if txt_file == "(..)":
                    if len(dir_to_explore) == 1:
                        txt_folder = dir_act
                    else:
                        txt_folder = str(os.path.dirname(dir_to_explore[actual_dir+1]))
                    file_length = "Prev.  "

                elif txt_file == "":
                    txt_file = str(os.path.dirname(dir_to_explore[actual_dir]))
                    txt_folder = "       "
                    file_length = info_file(txt_file)
                    #file_length = info_file("'" + txt_folder + "/" + txt_file + "'")
                else:
                    txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))

                    file_length= info_file(txt_folder + "/" + txt_file)

                send_lcd_2("Select", str(actual_dir), str(dir_number - 1),
                           txt_folder, txt_file,trklength = file_length)

            if message == [144, MIDI_NOTE_REW, 0]:
                buttons_out(MIDI_NOTE_REW, 0)
                #print "rew release"

            if message == [144, MIDI_NOTE_FF, 127]: # FF
                buttons_out(MIDI_NOTE_FF, 127)
                print("Next")
                #print "dir_number", dir_number
                actual_dir = min(max((actual_dir + 1), 0), dir_number-1)
                txt_file = str(os.path.basename(dir_to_explore[actual_dir]))
                if txt_file == "(..)":
                    #print "dir acrt ", dir_act
                    if len(dir_to_explore) == 1:
                        txt_folder = dir_act
                    else:
                        txt_folder = str(os.path.dirname(dir_to_explore[actual_dir+1]))
                    file_length = "Prev.  "

                elif txt_file == "":
                    txt_file = str(os.path.dirname(dir_to_explore[actual_dir]))
                    txt_folder = "       "
                    file_length = info_file(txt_file)
                    #file_length = info_file("'" + txt_folder + "/" + txt_file + "'")

                elif txt_file == "Setup":
                    #txt_file = "Setupa" #str(os.path.dirname(dir_to_explore[actual_dir]))
                    txt_folder = "Setup  "
                    file_length = "       " #info_file("'" + txt_file + "'")
                else:
                    txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))
                    file_length = info_file(txt_folder + "/" + txt_file)
                send_lcd_2("Select", str(actual_dir), str(dir_number - 1),
                            txt_folder, txt_file,trklength= file_length)

            if message == [144, MIDI_NOTE_FF, 0]:  # FF
                buttons_out(MIDI_NOTE_FF,00)

            if message == [144, MIDI_NOTE_REC, 127]: # REC
                if rec_stop_alert == False:
                    if recording == False:
                        recording = True
                        buttons_out(MIDI_NOTE_REC, 127)
                        print("Recording")
                        grabar()
                        rec_stop_alert = True
                    else:
                        print ("Already Recording")
                        rec_stop_alert = True
                else:
                    print("Rec stop alert ", rec_stop_alert)

            if message == [144, MIDI_NOTE_REC, 0]:
                rec_stop_alert = False
                print("Nada")


        if mode[0] == 1: #Setup

            if message == [144, MIDI_NOTE_REW, 127]: # REW
                print ("Channels -")
                channel_temp =min(max((channel_temp - 2) , 2), (32))
                print "Channels to record ", channel_temp
                send_lcd_setup(playlist_mode, random_mode, channel_temp, formats[format_num], minutestorecord(channel_temp))
                #send_lcd_2("Select Channel", str(channel)+"  ")

            if message == [144, MIDI_NOTE_FF, 127]: # FF
                print ("Channels +")
                channel_temp = min(max((channel_temp + 2), 2), (32))
                print "channel to record", channel_temp
                #print "Channels to record ", channels_to_record
                send_lcd_setup(playlist_mode, random_mode, channel_temp, formats[format_num], minutestorecord(channel_temp))
                #send_lcd_2("Select Channel", (str(channel)+"  "))

            if message == [144, MIDI_NOTE_PLAY, 127]: # PLAY
                # do whatever
                print "Cambiar modo"
                play_mode_number = play_mode_number + 1
                if play_mode_number >= len(play_modes):
                    play_mode_number = 0
                print play_mode_number, "play mode ", play_modes[play_mode_number]
                playlist_mode, random_mode = play_modes[play_mode_number]
                print playlist_mode, random_mode

                send_lcd_setup(playlist_mode, random_mode, channel_temp, formats[format_num], minutestorecord(channel_temp))

                #send_lcd_2("Select Channel", (str(channel)+"  "))

            if message == [144, MIDI_NOTE_REC, 127]: # REC
                # do whatever
                print "Cambiar FORMAT"
                #print "actual " , formats[format_num]
                format_num = format_num +1
                if format_num >= len(formats):
                    format_num = 0
                send_lcd_setup(playlist_mode, random_mode, channel_temp, formats[format_num], minutestorecord(channel_temp))
                #print "nuevo ", formats[format_num]
                #format = format

            if message == [144, MIDI_NOTE_STOP, 127]: # exit
                # do whatever
                channels_to_record = channel_temp

                print "channels to record out setup ", channels_to_record
                print "format ", formats[format_num]
                print "play modes ", playlist_mode, random_mode
                print "exit setup"
                mode = modes[0]
                init_player()
                #send_lcd_2("Select Channel", (str(channel)+"  "))

def send_lcd_setup( playlist_bol , random_bol, chann, format_txt, time_available):

    line_1 = "SETUP  " + "Plylist"+ "Random " + "Record " + "Channls" + "Time   " + "Availab" + "Format "
    line_2 = "Exit   " + str(playlist_bol) + (7-len(str(playlist_bol)))*" " + str(random_bol) + (7-len(str(random_bol)))*" " + "       " + "  " + str(chann) +(5-len(str(chann)))*" " + \
             time_available + "         " +  format_txt
    text_to_send = line_1+line_2
    #print text_to_send
    sysex = list(lcd_header)
    for character in text_to_send:
        sysex.append(ord(character))
    sysex.append(lcd_sysex_end)
    #sysex[6]= offset
    assert sysex[0] == 0xF0 and sysex[-1] == 0xF7
    midiout.send_message(sysex)
    time.sleep(timetowait)


def init_player():
    strip_clean()
    all_led_off()
    txt_file = str(os.path.basename(dir_to_explore[actual_dir]))
    if txt_file == "(..)":
        txt_folder = str(os.path.dirname(dir_to_explore[actual_dir + 1]))
    else:
        txt_folder = str(os.path.dirname(dir_to_explore[actual_dir]))
    strip_clean()
    send_lcd_2("Select", str(actual_dir), str(dir_number - 1), "       ",
                        txt_folder, txt_file)

def init_setup():
    print "init setup from ini setup"
    strip_clean()
    all_led_on()
    global channel_temp
    global channels_to_record
    global formats
    global format_num
    channel_temp = channels_to_record
    send_lcd_setup(playlist_mode, random_mode, channels_to_record, formats[format_num], minutestorecord())

def all_led_off():
    buttons_out(MIDI_NOTE_STOP, 0)
    buttons_out(MIDI_NOTE_PLAY, 0)
    buttons_out(MIDI_NOTE_REW, 0)
    buttons_out(MIDI_NOTE_FF, 0)
    buttons_out(MIDI_NOTE_REC, 0)

def all_led_on():
    buttons_out(MIDI_NOTE_STOP, 127)
    buttons_out(MIDI_NOTE_PLAY, 127)
    buttons_out(MIDI_NOTE_REW, 127)
    buttons_out(MIDI_NOTE_FF, 127)
    buttons_out(MIDI_NOTE_REC, 127)

try:
    midiin, port_name = open_midiinput(port)
    #midiout, port_name = open_midioutput(port)
except (EOFError, KeyboardInterrupt):
    sys.exit()

print("Attaching MIDI input callback handler.")
midiin.set_callback(MidiInputHandler(port_name))

print("Entering main loop. Press Control-C to exit.")
try:
    print "init player"
    check_X32_ALSA_CARD()

    mount_not_mounted()
    mounted = check_mounted()
    print "mounted ", mounted
    mounted_usbs = [x[2] for x in check_mounted()]
    print "mounted usbs ", mounted_usbs
    if len(mounted_usbs) == 0:
        print "No USB found"
        send_lcd_2("NO USB ", "detectd", " ", " " , " ", "   ")
        time.sleep(15)
    #comprobar que sea xfs!!!!!
    for i in mounted:
        print i
        if "xfs" in i:
            strip_clean()
            print "Found XFS disc " , i
            mediafolder = str(i[2]) + "/"
            mediafolder_size = i[4]
            print "Mediafolder ", mediafolder
            print "Mediafolder size ", mediafolder_size
            send_lcd_2("XFS    ", "detectd", "Mediaf", i[0], mediafolder_size, "Size   ")
            time.sleep(3)
            strip_clean()
        else:
            print "No XFS disk found"
            print "Risk of ALSA underuns, please use a SFX formatted USB memory for recording"
            send_lcd_2("Alert  ", "no XFS ", "detectd", "Risk of", "underrun", " ")
            time.sleep(15)





    initial_dirs = [ MP3_folder ]
    #print "initial_dirs", initial_dirs
    initial_dirs = initial_dirs + mounted_usbs + ["Setup"]
    print "initial_dirs", initial_dirs
    #usbs = check_mounted()
    #print  "usbs ", usbs
    dir_to_explore = initial_dirs
    dir_number = len(dir_to_explore)
    print "dir number ", dir_number, " dir to explore ", dir_to_explore
    actual_dir = 0
    print "Time to record available ", minutestorecord()
    init_player()
    while True:
        if recording:
            actual_time = datetime.datetime.now()
            #print "actual ", actual_time, "record start ", record_start
            #print record_start
            rec_time = str( actual_time - record_start)[:7]
            send_lcd_record(rec_time)
            time.sleep(1)
except KeyboardInterrupt:
    print('Saliendo')
    time.sleep(1)
    strip_clean()
    all_led_off()

finally:
    print("Exit.")
    unmount_mounted()
    midiin.close_port()
    midiout.close_port()
    del midiin

