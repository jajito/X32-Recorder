# X32-Recorder.
Raspberry PI Behringer X32 Recorder and MP3 player. Records up to 32 tracks and plays MP3. Uses the X32 DAW Remote scribble strip to interact with user.
You can select files to play, folders, options, play, stop, record, etc with the DAW remote buttons, and see the files, formats, recording time, etc in the scribble.
You can multitrack record an play with no time or memory size limits. Virtual sond test is possible.
Plays MP3, perfect for music between gis's parts.

Pure Pyhton and Raspberry Pi. Tested with a Raspberry Pi 4 and records up to 32 tracks with no underuns.
Completely autonomous (hopefully) and operable fromn the X32 through the DAW Remote transport Scribble Strip (DAW Remote/Matrix Main C).
Records and plays multitrack in .w64 or .caf format.
Random and playlist play MP3 options.
The script mounts every memory stick that is plugged to the Raspberry at start, and will choose as madiafolder (to record audio) the first with XFS format.
The MP3 are in a folder in the memory card (/share/MP3) and the recordings in an external USB Memory stick, that has to be XFS formatted, otherwise there will be overruns.
It uses SOX for multitrack recording, mpg123 for MP3 playing, and RTMIDI to MIDI comunicate with the X32.
It uses a SAMBA Server in order to have an easy and fast transfer of the files to the computer, because the XFS format of the memory stick is not very compatible.

It comes with a installation script that (I hope) will install dependencies, SAMBA server, configure the XUSB (X32 USB card) as default ALSA card, and sets a systemctl servicer so the script executes when the Raspberry starts.

Thanks for Peter Dikant for his wisdom and generosity.
This is only a continuation of his marvelous work.
https://dikant.de/2018/02/28/raspberry-xr18-recorder/

I'm not a programmer, so excuse my rough coding
