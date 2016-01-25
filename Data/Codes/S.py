import numpy as np
from matplotlib import pyplot as plt
__author__ = 'William'

o=0
# for o in np.linspace(0,.1,1000):
t = np.linspace(o, o+2., 1000)
d = np.sin(5*(2*np.pi*t)) + np.random.uniform(-1, 1, 1000)
# plt.plot(t,d)
# plt.show()
df = (2./d.size)*np.fft.rfft(d)
dfa = abs(df)
print(o, max(dfa))
f = np.fft.rfftfreq(d.size, (t[1]-t[0]))
plt.plot(f, dfa)
plt.show()


