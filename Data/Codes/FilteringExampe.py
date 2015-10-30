# -*- coding: utf-8 -*-

"""

Python code for basis FIR filter design

@author: Matti Pastell <matti.pastell@helsinki.fi>

http://mpastell.com

"""



from pylab import *

import scipy.signal as signal



#Plot frequency and phase response

def mfreqz(b,a=1):

    w,h = signal.freqz(b,a)

    h_dB = 20 * log10 (abs(h))

    subplot(211)

    plot(w/max(w),h_dB)

    ylim(-150, 5)

    ylabel('Magnitude (db)')

    xlabel(r'Normalized Frequency (x$\pi$rad/sample)')

    title(r'Frequency response')

    subplot(212)

    h_Phase = unwrap(arctan2(imag(h),real(h)))

    plot(w/max(w),h_Phase)

    ylabel('Phase (radians)')

    xlabel(r'Normalized Frequency (x$\pi$rad/sample)')

    title(r'Phase response')

    subplots_adjust(hspace=0.5)



#Plot step and impulse response

def impz(b,a=1):

    l = len(b)

    impulse = repeat(0.,l); impulse[0] =1.

    x = arange(0,l)

    response = signal.lfilter(b,a,impulse)

    subplot(211)

    stem(x, response)

    ylabel('Amplitude')

    xlabel(r'n (samples)')

    title(r'Impulse response')

    subplot(212)

    step = cumsum(response)

    stem(x, step)

    ylabel('Amplitude')

    xlabel(r'n (samples)')

    title(r'Step response')

    subplots_adjust(hspace=0.5)





#Lowpass FIR filter 

figure(1)

n = 61

a = signal.firwin(n, cutoff = 0.3, window = "hamming")

mfreqz(a)

show()

figure(4)

impz(a)

show()





#Highpass FIR filter

figure(2)

n = 101

a = signal.firwin(n, cutoff = 0.3, window = "hanning")

a = -a

a[n/2] = a[n/2] + 1

mfreqz(a)

show()



#Bandpass FIR 0.3 - 0,5

figure(3)

n = 1001

a = signal.firwin(n, cutoff = 0.3, window = 'blackmanharris')

b = - signal.firwin(n, cutoff = 0.5, window = 'blackmanharris'); b[n/2] = b[n/2] + 1

d = - (a+b); d[n/2] = d[n/2] + 1

#Frequency response

mfreqz(d)

show()