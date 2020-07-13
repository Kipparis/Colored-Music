# import lines
import os, sys
import random
from   enum import Enum

import sounddevice as sd
import soundfile as sf

# from   scipy.io.wavfile import read
import numpy as np

import threading
import queue

# bpm calc
from .music import *
import time

from multiprocessing import Process
import threading

# for communication with arduino
import serial

class PleerMode(Enum):
    """
    order in which songs are played
    """
    SERIAL = 1
    RANDOM = 2
    CIRCLE = 3

class PleerState(Enum):
    PLAYING   = 1
    CHILLING  = 2
    PAUSED    = 3

class PleerAction(Enum):
    SET_SONG      = 1
    PLAY_STOP     = 2
    PAUSE_UNPAUSE = 3
    NEXT_SONG     = 4
    PREV_SONG     = 5
    SONG_FINISHED = 6
    EXIT          = 0


class Pleer(Process):
    playing_ext = ".wav"

    def __init__(self, device, color_ctl, play_mode, block_size, loudness):
        self.device = device                # playback device
        self.playing_mode = play_mode       # order in which music is chosen
        self.state = PleerState.CHILLING    # Pleer state (used for asynchronous)
        self.block_size = block_size        # block for transmitting bits of music
        volume_parts = 5
        self.volume_part_size = 1.0 / volume_parts
        self.loudness = loudness            # how loud music is

        self.q = queue.Queue()
        self.song_list = []
        self.current_song_ind = -1

        self.event_occure = threading.Event()
        self.event_occure.clear()

        self.song_ind_stack = []
        self.connection_opened = True
        try:
            self.color_controller = serial.Serial(color_ctl)    # serial port to arduino
        except PermissionError:
            self.connection_opened = False
        pass

    def __del__(self):
        if self.connection_opened:
            self.color_controller.close()

    # add folder to current playlist
    def add_folder(self, path_to_folder):
        # get all files with .wav in specified dir
        for fl in os.listdir(path_to_folder):
            if fl.endswith(Pleer.playing_ext):
                # append full path
                self.song_list.append(os.path.join(path_to_folder,fl))
        pass

    # [] access
    def __getitem__(self, ind):
        ind_ = int(ind)
        assert (ind_ > -1 and ind_ < len(self.song_list)),\
            "specify ind in range of song list"
        return(self.song_list[ind_])

    @property
    def songs(self):
        return(self.song_list)

    def set_mode(self, mode):
        assert(isinstance(mode, PleerMode)), \
                "pass PleerMode enum inst"
        self.playing_mode = mode


    # get current playing song
    @property
    def song_name(self):
        return(
            self[self.current_song_ind].split('/')[-1]
        )

    # get full name of current playing song
    @property
    def song_name_full(self):
        return(
            self[self.current_song_ind]
        )

    # choose next ind according to playing mode
    def next_song_ind(self):
        """
        return index of next playing song
        """
        song_ind = -1
        if self.current_song_ind == -1:
            if self.playing_mode == PleerMode.SERIAL:
                song_ind = 0
            elif self.playing_mode == PleerMode.CIRCLE:
                song_ind = 0
            elif self.playing_mode == PleerMode.RANDOM:
                song_ind =\
                random.randrange(0,len(self.song_list),1)
        else:
            # pick next according to mode
            if self.playing_mode == PleerMode.SERIAL:
                song_ind = (self.current_song_ind + 1) % len(self.songs)
            elif self.playing_mode == PleerMode.CIRCLE:
                song_ind = self.current_song_ind
            elif self.playing_mode == PleerMode.RANDOM:
                song_ind =\
                random.randrange(0,len(self.song_list),1)
        return(song_ind)

    # all music processing
    def __call__(self, outdata, frames, time, status):
        """
        assign to `outdata` music array for playing (need to be same shape)
        """
        # print("outputting")
        if status.output_underflow:
            print('Output underflow: increase blocksize?',
                    file=sys.stderr)
            raise sd.CallbackAbort
        # assert not status
        try:
            data = self.q.get_nowait()
            # print("Data shape is: {}".format(data.shape))
        except queue.Empty:
            print('Buffer is empty: increase buffersize?',
                    file=sys.stderr)
        if len(data) != len(outdata):
            # возможно запрещает пользоваться второй раз
            raise sd.CallbackStop
        else:
            beat = self.beat_detect()
            output_beat(beat, self.color_controller)
            outdata[:] = data

    # call this when music finishes (music queue is empty)
    def finished(self):
        self.action = PleerAction.SONG_FINISHED
        self.event_occure.set()

    def pause_unpause(self):
        self.action = PleerAction.PAUSE_UNPAUSE
        self.event_occure.set()

    def stop_play(self):
        self.action = PleerAction.PLAY_STOP
        self.event_occure.set()

    def set_ind(self, song_ind=-1):
        # play specified song
        # self.play_ind(song_ind)
        if (song_ind == -1): self.current_song_ind = self.next_song_ind()
        else:                self.current_song_ind = song_ind
        self.action           = PleerAction.SET_SONG
        self.event_occure.set()
        pass

    def stop(self):
        # clear all (to be sure)
        self.stream.__exit__()
        self.q.queue.clear()
        self.state = PleerState.CHILLING


    def next_mode(self):
        """
        apply next pleer mode
        """
        # increment without overflowing
        self.playing_mode = PleerMode((self.playing_mode.value + 1) %
                len(list(PleerMode)) + 1)
        print("\rcurrent mode: {}".format(self.playing_mode))

    def exit(self):
        self.action = PleerAction.EXIT
        self.event_occure.set()


    def _set_song_impl(self):
        """
        load song into buffer
        """
        # calculate np array no play
        fl = self.song_name_full

        # x, sr = librosa.load(fl)
        # float32 - so librosa can understand
        # always_2d - so sounddevice can play it
        x, sr = sf.read(fl, dtype="float32", always_2d=True)
        music_arr = x
        print("\r(_set_song_impl) music_arr shape: {}".format(music_arr.shape))

        # bpm = get_file_bpm(fl)
        # if self.connection_opened:
        #     send_on_device(device_file_name, bpm, self.color_controller)
        # print("\rbpm is {}".format(bpm))

        start = 0;
        end = start + self.block_size;

        # create queue so we can fetch music data from it later
        while True:
            buf = music_arr[start:end]
            self.q.put_nowait(buf)
            start = end
            end += self.block_size
            if (start > len(music_arr)): break

        # self.beat_detect = BeatDetection(3, self.q, self.block_size, inf[0])
        self.beat_detect = BeatDetection(3, music_arr, self.block_size, sr)

        # if not hasattr(self, "stream"):
        self.play(music_arr, sr)
        # add songs id so you can return to previously played
        self.song_ind_stack.append(self.current_song_ind)


    # play song
    def play(self, music_arr, sr):
        self.stream = sd.OutputStream(
            samplerate=sr,
            blocksize=self.block_size,
            device=self.device,
            channels=1,
            callback=self,
            finished_callback=self.finished,
            dtype='{}'.format(music_arr.dtype))    # replace with "{}".format(music_arr.dtype)
        self.state = PleerState.PLAYING
        self.stream.__enter__()
        pass

    def next_song(self):
        # set action so another thread can understand what to do
        self.action = PleerAction.NEXT_SONG
        # unlock the mutex to let another thread run
        self.event_occure.set()
        pass

    def previous_song(self):
        # set action so another thread can understand what to do
        self.action = PleerAction.PREV_SONG
        # unlock the mutex to let another thread run
        self.event_occure.set()
        pass

    # make louder
    def make_louder(self):
        # you have to round because you're working with floating points
        # when it's small, it never will be 0, but really close to it (12e-12)
        if round(self.loudness,1) != 2.0:
            self.loudness += self.volume_part_size
        print("\rloudness: {}".format(self.loudness))

    # make more quite
    def make_more_quite(self):
        # you have to round because you're working with floating points
        if round(self.loudness,1) != 0.0:
            self.loudness -= self.volume_part_size
        print("\rloudness: {}".format(self.loudness))


    # pause song
    def pause(self):
        self.stream.__exit__()
        # XXX: после точки не автодополняет
        self.state = PleerState.PAUSED
        pass

    def _control_impl(self):
        """
        handle events: block until event occure than check self.action
        for what he needs to do
        """
        while True:
            # wait until there is state to procede
            self.event_occure.wait()    # blocking until event

            if self.action == PleerAction.SET_SONG:
                if self.state == PleerState.PLAYING:
                    self.stop()
                self._set_song_impl()
            elif self.action == PleerAction.SONG_FINISHED:
                self.current_song_ind = self.next_song_ind()
                self.stop()
                self._set_song_impl()
            elif self.action == PleerAction.PAUSE_UNPAUSE:
                if self.state == PleerState.PLAYING:
                    self.pause()
                elif self.state == PleerState.PAUSED:
                    self.play()
            elif self.action == PleerAction.PLAY_STOP:
                if self.state == PleerState.PLAYING:
                    self.stop()
                elif self.state == PleerState.CHILLING:
                    self._set_song_impl()
            elif self.action == PleerAction.NEXT_SONG:
                if self.state == PleerState.PLAYING or \
                    self.state == PleerState.PAUSED:
                    self.stop()
                self.current_song_ind = self.next_song_ind()
                self._set_song_impl()
            elif self.action == PleerAction.PREV_SONG:
                if self.state == PleerState.PLAYING or \
                    self.state == PleerState.PAUSED:
                    self.stop()
                self.song_ind_stack.pop()   # remove last song
                self.current_song_ind = self.song_ind_stack.pop()
                self._set_song_impl()
            elif self.action == PleerAction.EXIT:
                if self.state == PleerState.PLAYING or \
                    self.state == PleerState.PAUSED:
                    self.stop()
                break



            self.event_occure.clear()   # set flag to false
        pass

    def control(self):
        """
        call this to start endless loop
        """
        self.controller = threading.Thread(target=self._control_impl)
        self.controller.start()

    # return bpm of current song
    @property
    def bpm(self):
        return(get_file_bpm(self.song_name_full))

if __name__ == "__main__":
    print("script for manipulating and playing songs")
    exit(0)

