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
from matplotlib import gridspec
from matplotlib.mlab import specgram
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
import time

###########################################
BUFFER_LENGTH = 64*1024
BUFFER_MARGIN = 1024

###########################################
PushedPosition = 0
PopedPosition = 0
SignalBuffer = np.zeros(BUFFER_LENGTH)
BufferSemaphore = threading.Semaphore()
BufferPushEvent = threading.Event()
BufferPopEvent = threading.Event()

###########################################


class AudioListener(threading.Thread):
    def __init__(self, samplingRate, frameLength):
        super(AudioListener, self).__init__()
        self.SAMPLING_RATE = 44100
        self.FRAME_LENGTH = 1024
        self.running = True
        self.audio = rec.Recoder(self.SAMPLING_RATE, self.FRAME_LENGTH)
        # self.audio = syn.Synthesizer(self.SAMPLING_RATE,
        #                              np.ones((self.FRAME_LENGTH, 1)))

    def run(self):
        while self.running:
            signal = self.audio.getStream()
            length = len(signal)
            if 0 == length:
                # Wait for Microphone to be ready
                time.sleep(0.1)
                continue
            elif self.isNotSignalBufferReleased(length):
                # Wait for accumulating.
                BufferPopEvent.clear()
                BufferPopEvent.wait()
                # Retry to check.
                continue

            BufferSemaphore.acquire()   # Lock.
            self.accumulateSignalBuffer(signal)
            BufferSemaphore.release()   # Unlock.
            if not BufferPushEvent.is_set():
                # Suppose accumulating enough buffer in the above.
                BufferPushEvent.set()

    def stop(self):
        self.running = False
        self.join()
        del self.audio

    def isNotSignalBufferReleased(self, length):
        rest = PopedPosition - PushedPosition
        if rest <= 0:
            rest += BUFFER_LENGTH
        return length > (rest - BUFFER_MARGIN)

    # releaseSignalBuffer() is a brother.
    def accumulateSignalBuffer(self, signal):
        global PushedPosition
        global SignalBuffer
        begin = PushedPosition
        end = (PushedPosition + len(signal)) % BUFFER_LENGTH
        assert BufferPopEvent.is_set()
        PushedPosition = end
        if begin < end:
            SignalBuffer[begin:end] = signal
        else:
            rest = BUFFER_LENGTH - begin
            SignalBuffer[begin:] = signal[:rest]
            SignalBuffer[:end] = signal[rest:]


class SpecgramListener(threading.Thread):
    def __init__(self, length, frames):
        super(SpecgramListener, self).__init__()
        self.FRAME_LENGTH = length
        self.running = True
        bins = self.FRAME_LENGTH/2 + 1
        self.spectrogram = np.zeros((bins, frames), np.float)
        self.spectrum = np.zeros(bins, np.float)
        self.envelope = np.zeros(frames, np.float)
        self.window = np.hamming(self.FRAME_LENGTH)
        self.frames = frames

    def run(self):
        pos = 0
        while self.running:
            if self.isNotSignalBufferAccumulated():
                # Wait for accumulating.
                BufferPushEvent.clear()
                BufferPushEvent.wait()
                # Retry to check.
                continue

            BufferSemaphore.acquire()   # Lock.
            signal = self.releaseSignalBuffer()
            self.spectrum = self.transformToSpectrum(signal)
            self.spectrogram[:, pos:pos+1] = self.spectrum.reshape((-1, 1))
            self.envelope = np.sum(self.spectrogram, axis=0)
            BufferSemaphore.release()   # Unlock.
            pos = (pos + 1) % self.frames
            if not BufferPopEvent.is_set():
                # Suppose releasing enough buffer in the above.
                BufferPopEvent.set()

    def stop(self):
        self.running = False
        self.join()

    def isNotSignalBufferAccumulated(self):
        rest = PushedPosition - PopedPosition
        if rest < 0:
            rest += BUFFER_LENGTH
        return self.FRAME_LENGTH > (rest - BUFFER_MARGIN)

    # accumulateSignalBuffer() is a brother.
    def releaseSignalBuffer(self):
        global PopedPosition
        begin = PopedPosition
        end = (PopedPosition + self.FRAME_LENGTH) % BUFFER_LENGTH
        # PopedPosition is changed only here, so is_set() is always true.
        assert BufferPushEvent.is_set()
        PopedPosition = end
        if begin < end:
            return SignalBuffer[begin:end]
        else:
            return np.append(SignalBuffer[begin:], SignalBuffer[:end])

    def transformToSpectrum(self, signal):
        return specgram(signal, NFFT=self.FRAME_LENGTH,
                        noverlap=0, window=self.window)[0]

    def getSpecgramReference(self):
        return self.spectrogram

    def getSpectrumReference(self):
        return self.spectrum

    def getEnvelopeReference(self):
        return self.envelope


def updatePlot(i1, spec, axes, img, line):
    axl = axes[1]
    axb = axes[2]
    # Ignore drawing first frame.
    if 0 == i1:
        return []

    img.set_data(spec.getSpecgramReference())
    if 1 < i1:
        axl.lines.pop(0)
        axb.lines.pop(0)
    BufferSemaphore.acquire()
    left, = axl.plot(spec.getSpectrumReference(), line, "b")
    bottom, = axb.plot(spec.getEnvelopeReference(), "b")
    BufferSemaphore.release()
    return [left, bottom, img]


if __name__ == '__main__':
    samplingRate = 44100
    frameLength = 1024
    bins = frameLength/2 + 1
    frames = 150

    fig = plt.figure(figsize=(20, 10))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 5], height_ratios=[5, 1])
    axs = plt.subplot(gs[0, 1])
    axl = plt.subplot(gs[0, 0], sharey=axs)
    axb = plt.subplot(gs[1, 1], sharex=axs)
    axs.set_xlim([0, frames])
    axs.set_ylim([0, bins])
    axl.set_xlim([0, 0.3])
    axb.set_ylim([0, 3.0])
    axes = [axs, axl, axb]
    line = np.linspace(0.0, bins - 1, bins)

    audio = AudioListener(samplingRate, 1024)
    spec = SpecgramListener(frameLength, frames)
    img = axs.matshow(spec.getSpecgramReference(), aspect="auto",
                      origin='lower', norm=LogNorm(vmin=1e-10, vmax=1))
    BufferPushEvent.set()
    BufferPopEvent.set()

    # Start plot.
    anime = animation.FuncAnimation(fig, updatePlot, interval=50, blit=True,
                                    fargs=(spec, axes, img, line))
    audio.start()
    spec.start()
    print "Drawing."
    plt.show()
    audio.stop()
    spec.stop()
    print "Done."
