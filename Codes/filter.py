import scipy as sp
import scipy.signal as sig
import scipy.optimize as opt
from matplotlib import pyplot as plt

time_len = 10  # length of sample data in seconds
sample_fz = 150  # data frequency in Hz
npts = time_len*sample_fz
drift_sample = 50  # how many points to average over during drift calculation

ntaps = 15  # size of filter
filter_delay_time = (ntaps - 1)/(2.0*sample_fz)  # delay induced by filter in seconds

t = sp.linspace(0, time_len, npts)
t_clean = t - filter_delay_time
Bg = 16*2*sp.pi  # set frequency to be 16 Hz
xe_ideal = sp.sin(Bg * t)
sp.random.seed(1000)
rand_arr = sp.randn(len(t))*1e-7

rand_drift = [rand_arr[0]]
for i in range(len(t)):
    rand_drift.append(rand_drift[i]+rand_arr[i])

rand_drift.pop(0)
rand_drift = sp.array(rand_drift)
Bdrift = Bg*(1+rand_drift)

#Bdrift = [Bg*(1 + sum(rand_drift[:50*to])) for to in range(len(rand_drift))]


# plt.plot(Bdrift)

xe_noise = xe_ideal + sp.random.randn(len(t)) * 0.08
xe_drift = sp.sin(Bdrift * t)

plt.plot(t, xe_ideal)
plt.plot(t, xe_noise - 2)
plt.plot(t, xe_drift + 2)


xe_low = 16
xe_width = 1e-3
bf = sig.firwin(ntaps, [xe_low, xe_low+xe_width], pass_zero=False, nyq=sample_fz/2)
bf1 = sig.firwin(ntaps*10+5, [xe_low, xe_low+xe_width], pass_zero=False, nyq=sample_fz/2)
sig.freqz(bf, plot=lambda w, h: plt.plot(w*sample_fz/(2*sp.pi), abs(h)))
sig.freqz(bf1, plot=lambda w, h: plt.plot(w*sample_fz/(2*sp.pi), abs(h)+2))


# denominator for FIR filter is 1.0
xe_noise_clean = sig.lfilter(bf, [1.0], xe_noise)
xe_drift_clean = sig.lfilter(bf, [1.0], xe_drift)
xe_ideal_clean = sig.lfilter(bf, [1.0], xe_ideal)

plt.plot(t_clean, xe_ideal_clean)
plt.plot(t_clean, xe_drift_clean + 2)
plt.plot(t_clean, xe_noise_clean - 2)

plt.show()


def sin_cos_fit(tarr, w, A, B):
    return A*sp.sin(2*sp.pi*w*tarr) + B*sp.cos(2*sp.pi*w*tarr)

xe_fit_ideal = opt.curve_fit(sin_cos_fit, t_clean, xe_ideal_clean, p0=(16, 1, 1))
xe_fit_noise = opt.curve_fit(sin_cos_fit, t_clean, xe_noise_clean, p0=(16, 1, 1))
xe_fit_drift = opt.curve_fit(sin_cos_fit, t_clean, xe_drift_clean, p0=(16, 1, 1))
xe_fit_drift_end = opt.curve_fit(sin_cos_fit, t_clean[-150:], xe_drift_clean[-150:], p0=(16, 1, 1))
xe_fit_ideal_end = opt.curve_fit(sin_cos_fit, t_clean[-150:], xe_ideal_clean[-150:], p0=(16, 1, 1))
