using PyPlot, NPZ

#time = npzread("H10_ecg_time.npy")
data = npzread("H10_ecg_data.npy")

plot(data)
