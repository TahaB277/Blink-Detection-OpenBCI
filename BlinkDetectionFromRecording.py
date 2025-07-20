import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, iirnotch, decimate, find_peaks
import numpy as np

def highpass_filter(data, cutoff=1.0, fs=250, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    y = filtfilt(b, a, data)
    return y
    
def bandstop_notch(x, fs, freq=50, Q=30):
    b, a = iirnotch(freq, Q, fs)
    return filtfilt(b, a, x)

def bandpass(x, fs, low=1, high=50, order=4):
    nyq = fs/2
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, x)


# File path
filename = r'C:\Users\USP\Documents\OpenBCI_GUI\Recordings\OpenBCISession_2025-05-18_19-45-01\OpenBCI-RAW-2025-05-18_19-50-14.txt'

# Read file, skipping comment lines starting with '%'
df = pd.read_csv(filename, comment='%', header=0)

fs = 125  # Sample rate from your file header

# Convert Timestamp column to float (if not already)
df[' Timestamp'] = df[' Timestamp'].astype(float)

# Calculate elapsed time relative to the first timestamp (start time)
t = df[' Timestamp'] - df[' Timestamp'].iloc[0]


# apply high‑pass, notch, then low‑pass:
ch0_filtered = highpass_filter(df[' EXG Channel 0'], cutoff=1, fs=fs)
ch0_filtered = bandstop_notch(ch0_filtered, fs, freq=50)
ch0_filtered = bandpass(ch0_filtered, fs, low=1, high=50)

ch1_filtered = highpass_filter(df[' EXG Channel 1'], cutoff=1, fs=fs)
ch1_filtered = bandstop_notch(ch1_filtered, fs, freq=50)
ch1_filtered = bandpass(ch1_filtered, fs, low=1, high=50)

#y = y - y.rolling(window=fs*2, center=True).mean()

ch0_filtered *= 0.02235
ch1_filtered *= 0.02235

ch0_filtered = decimate(ch0_filtered, int(fs/20))  # e.g. to 20 Hz display rate
ch1_filtered = decimate(ch1_filtered, int(fs/20))  # e.g. to 20 Hz display rate
x = t[::int(fs/20)]


# Parameters
threshold = 100  # µV, adjust based on your signal
min_distance = int(0.3 * (fs / 20))  # Minimum distance between blinks (~300ms in samples)

# Detect positive peaks above the threshold
peaks, _ = find_peaks(-ch0_filtered, height=threshold, distance=min_distance)

# Enforce minimum blink interval in seconds
min_interval_sec = 0.7
filtered_peaks = []
last_time = -np.inf

# Convert x to NumPy array if needed
x_np = np.array(x)

for p in peaks:
    t_peak = x_np[p]
    if t_peak - last_time >= min_interval_sec:
        filtered_peaks.append(p)
        last_time = t_peak



# Extract blink times and durations (blink duration ~300ms, roughly estimate)
blink_events = []
for peak in filtered_peaks:
    time = x_np[peak]
    blink_events.append(time)

# Print the blink timestamps
for i, t_blink in enumerate(blink_events):
    print(f"Blink {i+1}: Time = {t_blink:.3f} s")


# Plotting
plt.figure(figsize=(12, 6))
plt.plot(x, ch0_filtered, label='EXG Channel 0 (filtered)')
#plt.plot(x, ch1_filtered, label='EXG Channel 1 (filtered)')
plt.title('High-pass Filtered EEG Channels 0 and 1')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (µV)')
plt.ylim(-1000, 1000)
#plt.xlim(0, 15)
plt.legend()
plt.show()
