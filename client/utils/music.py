import numpy as np

import matplotlib.pyplot as plt

import threading

import librosa
import librosa.display

class BeatDetection():

    def __init__(self, multiplier, arr, block_size, samplerate):
        self.multiplier = multiplier
        self.block_size = block_size
        sr = samplerate

        self.peaks = []
        print("\rArr shape: {}".format(arr.shape))
        x = arr
        print("\rself.arr shape:\t{}".format(x.shape))
        print("\rx[,0] shape:\t{}".format(x[:,0].shape))
        print("\rsr:\t{}".format(sr))
        print("\rframes len:\t{}".format(len(x)/sr))

        # interval for stft
        hop_length = 512
        # frequency edges to detect
        bot_edge = 6
        top_edge = 16
        # edges for peak picking
        max_edge  = 40
        avg_edge  = 100
        avg_delta = 100

        # maybe pass hop_length, frame_length
        S = librosa.stft(x[:,0], hop_length=hop_length)
        # human senses are logariphmic
        # leave window for n_fft to default (2048)
        logS = librosa.amplitude_to_db(abs(S))
        # sum up energy in all of frequences
        low_freq_arr = logS[bot_edge:top_edge,:].sum(axis=0).flatten()
        # compute first-order difference
        low_freq_diff = np.zeros_like(low_freq_arr)
        low_freq_diff[1:] = np.diff(low_freq_arr)
        # half-wave rectification
        low_freq_novelty = np.max([np.zeros_like(low_freq_diff), low_freq_diff], axis=0)
        # find peaks
        peak_frames = librosa.util.peak_pick(low_freq_novelty, max_edge, max_edge, avg_edge, avg_edge, avg_delta, 1)

        # # plot result
        # frames = np.arange(len(low_freq_novelty))
        # t = librosa.frames_to_time(frames, sr=sr)
        # plt.figure(figsize=(15, 6))
        # plt.plot(t, low_freq_novelty, "k-")
        # plt.vlines(t[peak_frames], 0, low_freq_novelty.max(), color='r', alpha=0.7)
        # plt.show()

        # copy
        self.onset_frames = peak_frames[:]
        print("\rself.onset_frames is: {}".format(self.onset_frames))


        self.idx       = 0  # index in queue of music pieces
        self.last_beat = 0  # index in onset_frames

    def __call__(self):
        beat = 0
        if self.onset_frames[self.last_beat] in range(self.idx * 4, 4 * (self.idx + 1)):
            print("\rb\t{}:{}".format(self.idx,self.onset_frames[self.last_beat]))
            self.last_beat += 1
            beat = 1

        self.idx += 1
        return beat


def time_to_idx(sec, sr):
    return int(sec * sr)

def idx_to_time(idx, sr):
    return int(idx / sr)

def get_file_bpm(path):
    # TODO: implement this
    return 220


def bpm_get_color(bpm):
    # TODO: replace constants with variables
    r = int()
    g = int()
    b = int()

    bottom_side = 100
    top_side    = 150
    bucket_qty  = 27    # 3x3x3 - low - medium - high

    print("\rbpm on input - {}".format(bpm))
    # get coef - [0;1]
    rl_bpm = (bpm - bottom_side) / (top_side - bottom_side)
    tmp = 1 / bucket_qty
    print("\rtmp - {}".format(tmp))
    rl_bpm = int(rl_bpm / tmp)
    print("\rrl bpm - {}".format(rl_bpm))

    # rl bpm 5 --
    #   012

    # 0-26
    # [0-2][0-2][0-2]
    # parse r
    r = int(rl_bpm / 9) * 64
    g = int((rl_bpm % 9) / 3) * 64
    b = int(rl_bpm % 3) * 64

    return (r,g,b)

def output_to_device(string,fl):
    # import os
    # if os.path.exists(device_file_name):
    # print("file exists => outputting")
    # with open(device_file_name, "w") as f:
    fl.write(string)
    # else: print("no file to output color")

def output_beat(beat, fl):
    if not beat: return
    # print("\rbeat occure")
    string = b"9\0"
    threading.Thread(target=output_to_device, args=(string,fl)).start()
    pass

def send_on_device(device_file_name, bpm, fl):
    r, g, b = bpm_get_color(bpm)
    string = "{} {} {} 0 4 0\n".format(r, g, b)
    threading.Thread(target=output_to_device,args=(string,fl)).start()

    print("\rcalculated: r - {}\tg - {}\tb - {}".format(r,g,b))

# def beat_occure(device_file_name):
#     # TODO: send type of message as 1 --
#     # X X X <len beat increase> <len beat fade> 1
#     try:
#         with open(device_file_name, "w") as f:
#             f.write("0 0 0 2 4 1")
#     pass

