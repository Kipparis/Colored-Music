# Music specifications

General command: `sox -r 22050 -e float -b 32 input.mp3 output.wav`  

+ `-r 22050` - resample to 22050 Hz  
+ `-e float -b 32` - convert to 32-bit floating point format  

Downmix to mono: `sox in.wav out.wav remix -`  

# About implementation

If I load sound with soundfile, it won't be correctly recognized by
librosa utils. If I load it with librosa, it would sound weirdly. So I
have to load it twice.  
