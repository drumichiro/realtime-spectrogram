#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 2015/04/23

@author: drumichiro
'''

import numpy as np
import warnings
import enum  # enum34


##############################
Phase = enum.Enum('Phase', 'ZERO RANDOM SCHROEDER')

##############################


class Synthesizer:
    # Synthesizes a simple sine wave.
    def __init__(self, samplingRate, bufferLength, frameLength,
                 initialPhase=Phase.RANDOM):
        if bufferLength < frameLength:
            raise Exception("Buffer length must be more than frame length.")
        if 0 < (bufferLength % frameLength):
            warnings.warn("Buffer length is not multiple of frame length.")

        # Initialize parameters
        self.SAMPLING_RATE = samplingRate
        self.BUFFER_LENGTH = bufferLength
        self.DEFAULT_BASE_AMP = 0.1
        self.DEFAULT_F0_FREQUENCY = samplingRate/8
        self.DEFAULT_SINES = 2
        self.frameLength = frameLength
        self.position = 0

        # Preset default parameters.
        baseValue = np.ones((self.BUFFER_LENGTH,
                             self.DEFAULT_SINES), np.float)
        self.amplitude = baseValue*self.DEFAULT_BASE_AMP/self.DEFAULT_SINES
        # Peak trajectories to generate phase.
        peakFreq = np.arange(1, self.DEFAULT_SINES+1)*self.DEFAULT_F0_FREQUENCY
        self.frequency = peakFreq*baseValue
        # freqAmp = (1.0 + 0.2*np.sin(np.arange(0, self.BUFFER_LENGTH)/4000.0))
        # frequency[:, 0] = frequency[:, 0]*freqAmp
        # frequency[:, 1] = frequency[:, 1]*freqAmp
        self.setInitialPhase(initialPhase)

    def calculateInstantPhase(self, frequency, initialPhase):
        phaseBase = np.zeros(frequency.shape)
        sumFreq = initialPhase[:]
        for freq, phs in zip(frequency, phaseBase):
            sumFreq += freq
            phs[:] = sumFreq
        coef = 2*np.pi/self.SAMPLING_RATE
        return phaseBase*coef

    def getSineNum(self):
        return self.amplitude.shape[1]

    def generateRandomPhase(self):
        np.random.seed(0xabe)
        return np.random.random(self.getSineNum())*self.SAMPLING_RATE

    def generateSchroederPhase(self):
        # TODO Implement!
        return self.generateRandomPhase()

    def generateZeroPhase(self):
        return np.zeros(self.getSineNum())

    def setInitialPhase(self, phaseType):
        initialPhase = []
        if phaseType == Phase.ZERO:
            initialPhase = self.generateZeroPhase()
        elif phaseType == Phase.RANDOM:
            initialPhase = self.generateRandomPhase()
        elif phaseType == Phase.SCHROEDER:
            initialPhase = self.generateSchroederPhase()
        else:
            raise Exception("Invalid phase type is input.")
        self.phase = self.calculateInstantPhase(self.frequency, initialPhase)

    def setParameter(self, amplitude=[], phase=[]):
        if len(amplitude):
            self.amplitude = amplitude
        if len(phase):
            self.phase = phase
        if self.amplitude.shape != self.phase.shape:
            raise Exception("Lengths are not different.")

    def getStream(self):
        # Generate sine wave.
        begin = self.position
        end = self.position + self.frameLength
        sines = np.cos(self.phase[begin:end])*self.amplitude[begin:end]

        # Update position
        rest = self.BUFFER_LENGTH - end
        self.position = end if rest >= self.frameLength else 0

        return np.sum(sines, axis=1)

    def getSamplingRate(self):
        return self.SAMPLING_RATE
