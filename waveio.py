#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 2015/04/26

@author: drumichiro
'''

import wave
import struct
# TODO Implement WaveIn


class WaveOut:
    # Records wave data from a microphone.
    def __init__(self, name, samplingRate, length=None):
        # Setup parameters
        self.name = name
        self.samplingRate = samplingRate
        self.bits = 16
        self.channels = 1
        self.length = length
        self.dones = 0
        self.SHORT_MAX = int(2**15)

        # Initialize by preset parameters
        self.wavo = wave.open(name, "w")
        self.wavo.setnchannels(self.channels)
        self.wavo.setsampwidth(self.bits/8)
        self.wavo.setframerate(self.samplingRate)
        self.wavo.setnframes(self.samplingRate*self.channels)

    def isOpened(self):
        return None == self.length or self.dones < self.length

    def __del__(self):
        if self.isOpened():
            self.wavo.close()

    def write(self, signal):
        if not self.isOpened():
            # Full. The handle has been already closed.
            return False

        # Written length of data.
        samples = min([len(signal), self.length - self.dones])
        shortSignal = signal[0:samples]*self.SHORT_MAX
        data = struct.pack("h"*len(shortSignal), *shortSignal)
        self.wavo.writeframes(data)

        # If written data is full, the handle is closed.
        self.dones += samples
        if None != self.length and self.dones >= self.length:
            self.wavo.close()
        return True
