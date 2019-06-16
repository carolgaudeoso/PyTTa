# -*- coding: utf-8 -*-

from pytta import default
from .filter import OctFilter
import numpy as np
import scipy .signal as ss
import scipy.integrate as si


def __filter(signal,
             order: int = 4,
             nthOct: int = 3,
             samplingRate: int = 44100,
             minFreq: float = 20,
             maxFreq: float = 16000,
             refFreq: float = 1000,
             base: int = 10):
    with OctFilter(order=order,
                   nthOct=nthOct,
                   samplingRate=signal.samplingRate,
                   minFreq=minFreq,
                   maxFreq=maxFreq,
                   refFreq=refFreq,
                   base=base) as of:
        return of.filter(signal)


def __remove_init_silence(timeSignal):
    RMS = (np.mean(timeSignal**2))**0.5
    idx = np.where(np.abs(timeSignal) >= RMS)[0]
    return timeSignal[idx[0]:], idx[0]


def __remove_nonlinear(timeSignal, samplingRate):
    RMS = (np.mean(timeSignal**2))**0.5
    idx = np.where(np.abs(timeSignal[samplingRate//2:]) <= RMS)[0]
    return timeSignal[:samplingRate//2+idx[0]], samplingRate//2+idx[0]


def __cumulative_integration(timeSignal, timeVector, samplingRate):
    signal, ini = __remove_init_silence(timeSignal[:])
    signal, fin = __remove_nonlinear(signal[:], samplingRate)
    signal = signal[::-1]**2
    signal = np.array(si.cumtrapz(signal, timeVector[ini:ini+fin],
                      axis=0, initial=0)[::-1], ndmin=2).T
    return 20*np.log10(signal/np.max(np.abs(signal)))


def filtered_decays(signalObj, nthOct, **kwargs):
    filteredObj = __filter(signalObj, nthOct, **kwargs)
    integList = [__cumulative_integration(filteredObj.timeSignal[:, ch],
                                          filteredObj.timeVector[:],
                                          filteredObj.samplingRate)
                 for ch in range(filteredObj.num_channels())]
    return integList


def RT(decay, signalObj, nthOct, **kwargs):
    try:
        decay = int(decay)
        y1 = -5
        y2 = y1 - decay
    except ValueError:
        if decay in ['EDT', 'edt']:
            y1 = 0
            y2 = -10
        else:
            raise ValueError("Decay must be either 'EDT' or an integer \
                             corresponding to the amount of energy decayed to \
                             evaluate.")
    output = []
    for ch in range(signalObj.num_channels()):
        filtDecay = filtered_decays(signalObj[ch], nthOct, **kwargs)
        RT = []
        for bd in range(len(filtDecay)):
            x1 = np.where(filtDecay[bd] >= y1)[0][-1]
            x2 = np.where(filtDecay[bd] >= y2)[0][-1]
            print(y2, y1, x2, x1)
            RT.append(3*(x2/signalObj.samplingRate
                         - x1/signalObj.samplingRate))
        output.append(RT)
    return output


def C(temp, signalObj, nthOct, **kwargs):
    pass


def D(temp, signalObj, nthOct, **kwargs):
    pass

# %% LEGACY CODE
#import numpy as np  
#from pyfilterbank import FractionalOctaveFilterbank 
##from scipy.io import wavfile
#from scipy import stats
#from matplotlib import pyplot as plt
#
#
#
## C50
#fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#h = filtered_signal**2
#fff = hfilt[1]
#
#f_filtro = np.fromiter(fff.keys(), dtype=float)
#f_filtro = np.transpose(f_filtro)
#
#c_50 = np.zeros(f_filtro.size)
#
#for band in range(33):
#       
#        h = filtered_signal**2
#        t = int((50/1000.0)*fs + 1)
#        c_50[band] = 10.0*np.log10((np.sum(h[:t])/np.sum(h[t:])))
#
## C80
#        fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#h = filtered_signal**2
#fff = hfilt[1]
#
#f_filtro = np.fromiter(fff.keys(), dtype=float)
#f_filtro = np.transpose(f_filtro)
#
#c_80 = np.zeros(f_filtro.size)
#
#for band in range(33):
#       
#        h = filtered_signal**2
#        t = int((80/1000.0)*fs + 1)
#        c_80[band] = 10.0*np.log10((np.sum(h[:t])/np.sum(h[t:])))
#
#
## D50
#fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#h = filtered_signal**2
#fff = hfilt[1]
#
#f_filtro = np.fromiter(fff.keys(), dtype=float)
#f_filtro = np.transpose(f_filtro)
#
#d_50 = np.zeros(f_filtro.size)
#
#for band in range(33):
#       
#        h = filtered_signal**2
#        t = int((50/1000.0)*fs + 1)
#        d_50[band] = 10.0*np.log10((np.sum(h[:t])/np.sum(h[:])))
#
## D80
#fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#h = filtered_signal**2
#fff = hfilt[1]
#
#f_filtro = np.fromiter(fff.keys(), dtype=float)
#f_filtro = np.transpose(f_filtro)
#
#d_80 = np.zeros(f_filtro.size)
#
#for band in range(33):
#       
#        h = filtered_signal**2
#        t = int((80/1000.0)*fs + 1)
#        d_80[band] = 10.0*np.log10((np.sum(h[:t])/np.sum(h[:])))
#
#
## EDT
#
#fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#init = 0
#end = -10
#factor = 6
#EDT = np.zeros(32)
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#
#
#for band in range(32):
#        # Filtering signal
#    abs_signal = np.abs(filtered_signal) / np.max(np.abs(filtered_signal))
#
#        # Schroeder integration
#    sch = np.cumsum(abs_signal[::-1, band]**2)[::-1]
#    sch_db = 10.0 * np.log10(sch / np.max(sch))
#
#        # Linear regression
#    sch_init = sch_db[np.abs(sch_db - init).argmin()]
#    sch_end = sch_db[np.abs(sch_db - end).argmin()]
#    init_sample = np.where(sch_db == sch_init)[0][0]
#    end_sample = np.where(sch_db == sch_end)[0][0]
#    x = np.arange(init_sample, end_sample + 1) / fs
#    y = sch_db[init_sample: end_sample + 1]
#    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
#
#        # Reverberation time (T30, T20, T10 or EDT)
#    db_regress_init = (init - intercept) / slope
#    db_regress_end = (end - intercept) / slope
#    EDT[band] = factor*((end_sample/44100))
#    
#    
#
#
#fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#init = -5
#end = -25
#factor = 3
#t60 = np.zeros(33)
#t20 = np.zeros(33)
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#fff = hfilt[1]
#f_filtro = np.fromiter(fff.keys(), dtype=float)
#f_filtro = np.transpose(f_filtro)
#for band in range(33):
#        # Filtering signal
#    abs_signal = np.abs(filtered_signal) / np.max(np.abs(filtered_signal))
#
#        # Schroeder integration
#    sch = np.cumsum(abs_signal[::-1, band]**2)[::-1]
#    sch_db = 10.0 * np.log10(sch / np.max(sch))
#
#        # Linear regression
#    sch_init = sch_db[np.abs(sch_db - init).argmin()]
#    sch_end = sch_db[np.abs(sch_db - end).argmin()]
#    init_sample = np.where(sch_db == sch_init)[0][0]
#    end_sample = np.where(sch_db == sch_end)[0][0]
#    x = np.arange(init_sample, end_sample + 1) / fs
#    y = sch_db[init_sample: end_sample + 1]
#    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
#
#        # Reverberation time (T30, T20, T10 or EDT)
#    db_regress_init = (init - intercept) / slope
#    db_regress_end = (end - intercept) / slope
#    t20[band] = 3*((end_sample/44100)-(init_sample/44100))
#    t60[band] = factor * (db_regress_end - db_regress_init)
#
#f2 = (  100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000)
##t20_p = t20[9:30]
#plt.figure(figsize=(10, 5))
#p1 = plt.semilogx(f_filtro, t20, 'k--')
##p2 = plt.semilogx(f2,t20_m, 'b--')
##plt.legend((p1[0], p2[0]),('Python','Matlab'))
#plt.xscale('log')
#plt.axis([100, 5000, 0, 3])
#plt.xlabel(r'$F$ in Hz')
#plt.ylabel(r'$T20$')
#plt.xticks(f2, ('100', '125', '160', '200', '250', '314', '400', '500', '630', '800', '1000', '1250', '1600', '2000', '2500', '3150', '4000', '5000', '6300', '8000', '10000'))
#plt.title('Comparação entre valores de T20 calculados em Python e em Matlab')
##plt.savefig('T20_PxM.pdf')
#plt.show()
#
#
#fs = 44100
#medp= np.load('C:/Users/Marvos/Desktop/Sala_TCC/Pos1/Spyder/medisom.npz')
#hpy = medp['h']
#Hpy = medp['H']
#raw_signal = hpy
#init = -5
#end = -35
#factor = 2
#t60 = np.zeros(32)
#t30 = np.zeros(32)
#
#octfilter = FractionalOctaveFilterbank(sample_rate=44100, order=4, nth_oct=3.0, norm_freq=1000, start_band=-19, end_band=13, edge_correction_percent=0.01, filterfun='py')
#
#hfilt = octfilter.filter(raw_signal)
#filtered_signal = hfilt[0]
#
#
#for band in range(32):
#        # Filtering signal
#    abs_signal = np.abs(filtered_signal) / np.max(np.abs(filtered_signal))
#
#        # Schroeder integration
#    sch = np.cumsum(abs_signal[::-1, band]**2)[::-1]
#    sch_db = 10.0 * np.log10(sch / np.max(sch))
#
#        # Linear regression
#    sch_init = sch_db[np.abs(sch_db - init).argmin()]
#    sch_end = sch_db[np.abs(sch_db - end).argmin()]
#    init_sample = np.where(sch_db == sch_init)[0][0]
#    end_sample = np.where(sch_db == sch_end)[0][0]
#    x = np.arange(init_sample, end_sample + 1) / fs
#    y = sch_db[init_sample: end_sample + 1]
#    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
#
#        # Reverberation time (T30, T20, T10 or EDT)
#    db_regress_init = (init - intercept) / slope
#    db_regress_end = (end - intercept) / slope
#    t30[band] = 3*((end_sample/44100)-(init_sample/44100))
#    t60[band] = factor * (db_regress_end - db_regress_init)