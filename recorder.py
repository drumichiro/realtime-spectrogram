#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 2015/04/23

@author: drumichiro
'''

import pyaudio
import numpy as np


class Recoder:
    # Records wave data from a microphone.
    def __init__(self, samplingRate, frameLength):
        # Parameters for recording
        self.CHANNELS = 1
        self.SAMPLING_RATE = samplingRate
        self.SHORT_MAX = float(2**15)

        # Prepare audio microphone
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=self.CHANNELS,
                                      rate=self.SAMPLING_RATE,
                                      input=True,
                                      frames_per_buffer=frameLength)

    def __del__(self):
        self.stream.stop_stream()
        self.audio.close(self.stream)

    def getStream(self):
        # The number of frames that can be read without waiting.
        num_frame = self.stream.get_read_available()
        if num_frame == 0:
            return []

        # Read binary data by streaming
        data = self.stream.read(num_frame)

        # Interpret a buffer as a 1-dimensional array.
        return np.frombuffer(data, dtype="int16")/self.SHORT_MAX

    def getSamplingRate(self):
        return self.SAMPLING_RATE
