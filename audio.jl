using WAV, NPZ

sample_rate = 130

data = npzread("./H10_ecg_data.npy")[5000:end]
wavwrite(data / (maximum(abs.(data))), "./ecg.wav", Fs=sample_rate)
