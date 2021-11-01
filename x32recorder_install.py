
# X32RECORDER INSTALLATION
import os
import sys
import fileinput



#to make xfs disk
#get name with
#   blkid
# example : /dev/sda
# unmount if mounted
#   sudo umount /dev/sda
# make xfs disk
#   mkfs.xfs /dev/sda -f


def comando(cmd):
    result = os.system(cmd)
    print "result = ", result

def replace(file, searchExp, replaceExp):
    for line in fileinput.input(file, inplace=1):
        line = line.replace(searchExp, replaceExp)
        sys.stdout.write(line)

print "Installation of files for X32RECORDER."

answer = raw_input("Do you want to install X32RECORDER? (y/n)")
if answer == "y":
   print("Proceeding...")
   exit
elif answer == "n":
   print "Bye..."
   sys.exit()
else:
   print("Sorry your answer is not recognised. Restart the program and make sure you answer with the word Yes or the word No.")

print "Updating ..."
comando ("sudo apt update")
comando ("sudo apt dist-upgrade")
#comando ("sudo apt clean")

print "Installing SOX"
comando ("sudo apt-get install sox libsox-fmt-mp3")

print "Installing mpg123"
comando ("sudo apt-get install mpg123")

print "Installing xfs utilities"
comando ("sudo apt-get install xfsprogs")

print "Installing RTMIDI"
comando ("sudo apt-get install libasound2-dev")
comando ("sudo apt-get install libjack-dev")
comando ("sudo apt update")
comando ("sudo apt install python-pip")
comando ("pip install python-rtmidi")


print "Installing samba server"
comando ("sudo apt-get install samba samba-common-bin")
comando ("sudo mkdir -m 1777 /share/MP3")

#comando ("sudo nano /etc/samba/smb.conf")

print "Configuring SAMBA server"

import configparser
config = configparser.ConfigParser()
config.sections()
config.read('/etc/samba/smb.conf')
result = config.sections()
print "res ", result

config["share"]={"Comment" : "Pi shared card MP3",
                 "Path" : "/share",
                 "Browseable" : "yes",
                 "Writeable" : "Yes",
                 "only guest" : "no",
                 "create mask" : "0777",
                 "directory mask" : "0777", 
                 "Public" : "yes",
                 "Guest ok" : "yes"}
config["media"]={"Comment" : "Pi shared USB XFS",
                 "Path" : "/media",
                 "Browseable" : "yes",
                 "Writeable" : "Yes",
                 "only guest" : "no",
                 "create mask" : "0777",
                 "directory mask" : "0777",
                 "Public" : "yes",
                 "Guest ok" : "yes"}

with open('/etc/samba/smb.conf', 'w') as configfile:
   config.write(configfile)

print "Configuring X32 as default sound card"
file = "/usr/share/alsa/alsa.conf"
replace(file, "defaults.ctl.card 0", "defaults.ctl.card \"XUSB\"")
replace(file, "defaults.pcm.card 0", "defaults.pcm.card \"XUSB\"")


print "Configure to Run at start"
config = configparser.ConfigParser()
config.optionxform = str
config.sections()
config.read('/lib/systemd/system/X32sample.service')
#config.read("x32sampledemo.service")
result = config.sections()
print "res ", result

config["Unit"]={"Description" : "My X32Sample Service",
                "After" : "multi-user.target"}

config["Service"]={"Type" : "idle",
                   "ExecStart" : "/usr/bin/python /home/pi/x32recorder.py",
                   "StandardOutput" : "append:/home/pi/log.txt",
                   "StandardError" : "append:/home/pi/logerror.txt",
                   "Environment" : "PYTHONUNBUFFERED = 1"}

config["Install"]={"WantedBy" : "multi-user.target"}

with open('/lib/systemd/system/X32sample.service', 'w') as configfile:
#with open('x32sampledemo.service', 'w') as configfile:
   config.write(configfile)

comando ("sudo chmod 644 /lib/systemd/system/X32sample.service")
comando ("sudo systemctl daemon-reload")
comando ("sudo systemctl enable X32sample.service")
print "configuration terminated, reboot now"
