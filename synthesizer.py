#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 2015/04/23

@author: drumichiro
'''

import numpy as np
import enum  # enum34


##############################
Phase = enum.Enum('Phase', 'ZERO RANDOM SCHROEDER')

##############################


class Synthesizer:
    # Synthesizes a simple sine wave.
    def __init__(self, samplingRate, amplitude=None, frequency=None,
                 initialPhaseType=Phase.RANDOM):

        # Initialize parameters
        self.SAMPLING_RATE = samplingRate
        self.initialPhaseType = initialPhaseType
        self.position = 0

        # Preset default parameters.
        amplitude, frequency = self.presetDefaultParameter(amplitude,
                                                           frequency)

        self.amplitude = np.array(amplitude)
        self.frequency = np.array(frequency)
        self.sines = None
        if None is not frequency:
            self.calculateSines()

    def presetDefaultParameter(self, amplitude, frequency):
        if None is amplitude and None is not frequency:
            length = frequency.shape[0]
            sinNum = frequency.shape[1]
            amplitude = np.ones((length, sinNum), np.float)/sinNum
        elif None is not amplitude and None is frequency:
            length = amplitude.shape[0]
            sinNum = amplitude.shape[1]
            fundFreq = self.SAMPLING_RATE/2.0/length
            peakFreq = np.arange(1, sinNum+1)*fundFreq
            frequency = peakFreq*np.ones((length, sinNum), np.float)
        return amplitude, frequency

    def calculateInstantPhase(self, frequency, initialPhase):
        phaseBase = np.zeros(frequency.shape)
        sumFreq = initialPhase[:]
        for freq, phs in zip(frequency, phaseBase):
            sumFreq += freq
            phs[:] = sumFreq
        coef = 2*np.pi/self.SAMPLING_RATE
        return phaseBase*coef

    def calculateSines(self):
        initialPhase = []
        if self.initialPhaseType == Phase.ZERO:
            initialPhase = self.generateZeroPhase()
        elif self.initialPhaseType == Phase.RANDOM:
            initialPhase = self.generateRandomPhase()
        elif self.initialPhaseType == Phase.SCHROEDER:
            initialPhase = self.generateSchroederPhase()
        else:
            raise Exception("Invalid phase type is input.")
        self.phase = self.calculateInstantPhase(self.frequency, initialPhase)
        self.sines = np.cos(self.phase)  # Use cosine function.

    def getAmpLength(self):
        if 0 >= len(self.amplitude.shape):
            return 1
        return self.amplitude.shape[0]

    def getFreqLength(self):
        if 0 >= len(self.frequency.shape):
            return 1
        return self.frequency.shape[0]

    def getSineNum(self):
        if 1 >= len(self.frequency.shape):
            return 1
        return self.frequency.shape[1]

    def generateRandomPhase(self):
        np.random.seed(0xabe)
        return np.random.random(self.getSineNum())*self.SAMPLING_RATE

    def generateSchroederPhase(self):
        roughAmp = np.sum(self.amplitude, axis=0)
        ampSquare = roughAmp*roughAmp
        ampNorm = ampSquare/np.sum(ampSquare)
        phase = np.zeros(self.getSineNum(), np.float)
        coef = np.arange(self.getSineNum(), 0, -1)
        for i1 in np.arange(1, self.getSineNum()):
            phase[i1] = np.sum(coef[-i1:]*ampNorm[:i1])
        return - phase*self.SAMPLING_RATE

    def generateZeroPhase(self):
        return np.zeros(self.getSineNum())

    def setAmplitude(self, amplitude):
        self.amplitude = amplitude

    def setFrequency(self, frequency):
        self.frequency = frequency
        self.calculateSines()
        # Reset position
        self.position = 0

    def popCurrentSines(self):
        begin = self.position
        end = self.position + self.getAmpLength()
        assert begin < self.getAmpLength()
        assert end <= self.getAmpLength()
        # Update position
        self.position = end % self.getFreqLength()
        if end <= self.getFreqLength():
            # Return sines directly.
            return self.sines[begin:end]
        # Cross the boundary of sines.
        sines = self.sines[begin:]
        while True:
            end -= self.getFreqLength()
            if end <= self.getFreqLength():
                break
            sines = np.r_[sines, self.sines]
        return np.r_[sines, self.sines[:end]]

    def getStream(self):
        # Generate sine wave.
        # print "self.position:%d" % self.position
        sines = self.popCurrentSines()*self.amplitude
        return np.sum(sines, axis=1)

    def getSamplingRate(self):
        return self.SAMPLING_RATE
