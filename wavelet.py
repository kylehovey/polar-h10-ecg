import pywt
import numpy as np
import matplotlib.pyplot as plt

data = np.load("./H10_ecg_data.npy")
scales = np.logspace(1.2, 3.1, num=200, dtype=np.int32)

coef, freqs = pywt.cwt(data, np.arange(1, 129), 'morl')

plt.matshow(coef)
plt.show()
