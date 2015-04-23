#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 2015/04/23

@author: drumichiro
'''

import numpy as np
import pylab as plt
import threading
import recorder as rec
import synthesizer as syn
import waveio as wav
import time
import matplotlib.animation as animation
from matplotlib import gridspec
from matplotlib.mlab import specgram
from matplotlib.colors import LogNorm

###########################################
SAMPLING_RATE = 44100
FRAME_LENGTH = 1024
BINS = FRAME_LENGTH/2 + 1
BUFFER_LENGTH = FRAME_LENGTH*32*2
SHOWED_SAMPLES = SAMPLING_RATE*3   # 3sec
SHOWED_FRAMES = SHOWED_SAMPLES/FRAME_LENGTH
PLOT_SIGNAL_FRAMES = SHOWED_FRAMES/2
UPDATE_MSEC = 50
SPECGRAM_WINDOW = np.hamming(FRAME_LENGTH)

###########################################
FramePosition = 0   # Position of updated frame index.
BufferPosition = 0
SignalBufferFore = np.zeros(BUFFER_LENGTH)
SignalBufferBack = np.zeros(BUFFER_LENGTH)
BufferSemaphore = threading.Semaphore()

###########################################


class AudioListener(threading.Thread):
    def __init__(self):
        super(AudioListener, self).__init__()
        self.running = True
        self.audio = rec.Recoder(SAMPLING_RATE, FRAME_LENGTH)
        # syn.Synthesizer(SAMPLING_RATE, SAMPLING_RATE, FRAME_LENGTH)

    # releaseSignalBuffer() is a brother.
    def accumulateSignalBuffer(self):
        global BufferPosition
        global SignalBufferFore
        stream = self.audio.getStream()
        time.sleep(0.023)   # for synthesis
        length = len(stream)
        if 0 == length:
            return False
        BufferSemaphore.acquire()   # Lock.
        end = BufferPosition + length
        if end <= BUFFER_LENGTH:
            SignalBufferFore[BufferPosition:end] = stream
            BufferPosition = end
        else:
            print "Buffer is full."
            time.sleep(2)
        BufferSemaphore.release()   # Unlock.
        return True

    def run(self):
        while self.running:
            self.accumulateSignalBuffer()

    def stop(self):
        self.running = False


# accumulateSignalBuffer() is a brother.
def releaseSignalBuffer():
    global BufferPosition
    global SignalBufferFore
    global SignalBufferBack
    if 0 == BufferPosition:
        return []
    BufferSemaphore.acquire()   # Lock.
    signal = SignalBufferFore[0:BufferPosition]
    SignalBufferBack, SignalBufferFore = SignalBufferFore, SignalBufferBack
    BufferPosition = 0
    BufferSemaphore.release()   # Unlock.
    return signal


def updateSpectrogram(signal, spectrogram):
    global FramePosition
    if 0 == len(signal):
        return False
    spec = specgram(signal, NFFT=FRAME_LENGTH, noverlap=0,
                    window=SPECGRAM_WINDOW)[0]
    end = FramePosition + spec.shape[1]
    if SHOWED_FRAMES < end:
        FramePosition = 0
        end = spec.shape[1]
        assert end <= SHOWED_FRAMES
    spectrogram[:, FramePosition:end] = spec
    FramePosition = end
    return True


def updatePlot(axes, img):
    img.set_data(spectrogram)


def updateAnalysis(i1, spectrogram, axes, img):
    signal = releaseSignalBuffer()
    updateSpectrogram(signal, spectrogram)
    updatePlot(axes, img)


if __name__ == '__main__':

    fig = plt.figure(figsize=(20, 10))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 5], height_ratios=[5, 1])
    axs = plt.subplot(gs[0, 1])
    axl = plt.subplot(gs[0, 0], sharey=axs)
    axb = plt.subplot(gs[1, 1], sharex=axs)
    axes = [axs, axl, axb]

    spectrogram = np.zeros((BINS, SHOWED_FRAMES), np.float)
    # img = axs.imshow(spectrogram, vmin=0, vmax=1, aspect="auto")#animated
    img = axs.matshow(spectrogram, aspect="auto", origin='lower',
                      norm=LogNorm(vmin=1e-10, vmax=1))

    # Start plot and analysis
    ani = animation.FuncAnimation(fig, updateAnalysis, interval=UPDATE_MSEC,
                                  fargs=(spectrogram, axes, img))

    # Start collecting audio data
    trans = AudioListener()
    trans.start()

    plt.show()
