#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 2015/04/29

@author: drumichiro
'''

import numpy as np
import unittest
# from matplotlib.mlab import specgram
# import scikits.audiolab as wio
# import pylab as plt
import synthesizer as syn

###########################################
# TEST_WAVE_NAME = "test123.wav"
SAMPLING_RATE = 44100
FRAME_LENGTH = 4410  # 1024
# SPECGRAM_WINDOW = np.hamming(FRAME_LENGTH)

###########################################


class SynthesizerTest(unittest.TestCase):
    def setUp(self):
        self.amplitude, self.frequency = self.generateAmpAndFreq(FRAME_LENGTH,
                                                                 2, 440.0)

    # def tearDown(self):

    def generateAmpAndFreq(self, length, sineNum, fundFreq):
        baseValue = np.ones((length, sineNum), np.float)
        amplitude = baseValue/sineNum
        peakFreq = np.arange(1, sineNum+1)*fundFreq
        frequency = peakFreq*baseValue
        return amplitude, frequency

    def testConstructor(self):
        for synth in [syn.Synthesizer(SAMPLING_RATE, amplitude=self.amplitude),
                      syn.Synthesizer(SAMPLING_RATE, frequency=self.frequency),
                      syn.Synthesizer(SAMPLING_RATE, amplitude=self.amplitude,
                                      initialPhaseType=syn.Phase.RANDOM),
                      syn.Synthesizer(SAMPLING_RATE, frequency=self.frequency,
                                      initialPhaseType=syn.Phase.RANDOM)]:
            length = len(synth.getStream())  # Check only lengths
            self.assertEqual(length, FRAME_LENGTH)

    def testInitialPhase(self):
        length = FRAME_LENGTH
        sineNum = length/2 + 1
        fundFreq = 0.5
        amplitude, frequency = self.generateAmpAndFreq(length, sineNum,
                                                       fundFreq)

        ampMin = ampMax = []
        for phase in syn.Phase:
            synth = syn.Synthesizer(length, initialPhaseType=phase,
                                    amplitude=amplitude,
                                    frequency=frequency)
            signal = synth.getStream()
            ampMin = np.append(ampMin, np.min(signal))
            ampMax = np.append(ampMax, np.max(signal))
            # Plot for debug
#             plt.subplot(len(syn.Phase), 1, phase.value)
#             plt.plot(signal)
#         plt.show()
        # Schroeder phase is the most effective.
        bestPhase = syn.Phase.SCHROEDER
        worstPhase = syn.Phase.ZERO
        # Plus one is to adapt Enum index.
        self.assertEqual(np.argmin(ampMax) + 1, bestPhase.value)
        self.assertEqual(np.argmax(ampMin) + 1, bestPhase.value)
        self.assertEqual(np.argmin(ampMin) + 1, worstPhase.value)
        self.assertEqual(np.argmax(ampMax) + 1, worstPhase.value)

    def testAmplitudeLength(self):
        sineNum = self.frequency.shape[1]
        shortLen = [np.ones((FRAME_LENGTH - 1, sineNum), np.float),
                    np.ones((FRAME_LENGTH + 0, sineNum), np.float),
                    np.ones((FRAME_LENGTH + 1, sineNum), np.float)]
        longLen = [np.ones((FRAME_LENGTH*2 - 1, sineNum), np.float),
                   np.ones((FRAME_LENGTH*2 + 0, sineNum), np.float),
                   np.ones((FRAME_LENGTH*2 + 1, sineNum), np.float)]
        for lhs, rhs in zip(shortLen, longLen):
            # Check checksums of only rear signal.
            begin = - (FRAME_LENGTH - 1)
            synth = syn.Synthesizer(FRAME_LENGTH, frequency=self.frequency)
            synth.setAmplitude(lhs)
            lhSum = np.sum(synth.getStream()[begin:])
            synth = syn.Synthesizer(FRAME_LENGTH, frequency=self.frequency)
            synth.setAmplitude(rhs)
            rhSum = np.sum(synth.getStream()[begin:])
            self.assertEqual(lhSum, rhSum)

    def testFrequencyLength(self):
        sineNum = self.frequency.shape[1]
        bitLongFreq = np.r_[self.frequency, np.ones((2, sineNum), np.float)]
        synth = syn.Synthesizer(FRAME_LENGTH, amplitude=self.amplitude)
        synth.setFrequency(bitLongFreq)
        lSgn = synth.getStream()[:-1]  # Move stream position.
        synth.setAmplitude(self.amplitude[:-1])  # Set short amplitude.
        synth.setFrequency(self.frequency)  # Should reset position here.
        rSgn = synth.getStream()
        self.assertEqual(lSgn.shape, rSgn.shape)
        self.assertEqual(np.sum(lSgn), np.sum(rSgn))
