# X32-Recorder
Raspberry PI Behringer X32 Multitrack Recorder and MP3 player. 
Records up to 32 tracks and plays MP3. Uses the X32 DAW Remote scribble strip to interact with user.
You can select files to play, folders, options, play, stop, record, etc with the DAW remote buttons, and see the files' names, formats, recording time, etc in the X32 scribble.
You can multitrack record an play with no time or memory size limits. So virtual sound test on the run is possible, and multitrack recording of the whole gig.
Plays MP3, perfect for music between gig's parts.
You can navigate the User Interface with Rew and FF buttons, select with Play button and go back in folders' tree selecting (..).
Attention, to prevent accidental recordings stop, to stop recording you have to push the record button and keeping it pushed, push the stop button.

Pure Pyhton and Raspberry Pi. Tested with a Raspberry Pi 4 and records up to 32 tracks with no underuns. With a Raspberry Pi 2 there were underruns.
Completely autonomous (hopefully) and operable with the X32 through the DAW Remote transport Scribble Strip (DAW Remote/Matrix Main C).
Records and plays multitrack in .w64 or .caf format.
Random and playlist play MP3 options.
The script mounts every memory stick that is plugged to the Raspberry at start, and will choose as mediafolder (to record audio) the first USB stick with XFS format.
The MP3 are in a folder in the memory card (/share/MP3) or in a memory stick, and the multitrack recordings are done in an external USB Memory stick, that has to be XFS formatted, otherwise there will be overruns.
It uses SOX for multitrack recording, mpg123 for MP3 playing, and RTMIDI to MIDI comunicate with the X32.
It uses a SAMBA Server in order to have an easy and fast transfer of the files to the computer, because the XFS format of the memory stick is not very compatible.

It comes with a installation script that (I hope) will install dependencies, SAMBA server, configure the XUSB (X32 USB card) as default ALSA card, and sets a systemctl service so the script executes when the Raspberry starts.

Video of the creature
https://www.youtube.com/watch?v=mOaofRDe_WI

Thanks for Peter Dikant for his wisdom and generosity.
This is only a continuation of his work.
https://dikant.de/2018/02/28/raspberry-xr18-recorder/

I'm not a programmer, so excuse my rough coding and my poor english.
If you find it useful or you are making money with it, consider buying me a coffee. 
https://www.buymeacoffee.com/jajito

Have fun!
