from scipy.signal import butter, filtfilt, iirnotch, decimate, find_peaks
import numpy as np
from pyOpenBCI import OpenBCICyton
import time
import serial

arduinoPort = "COM5"  # Change this to your Arduino port
openBCIPort = "COM4"  # Change this to your OpenBCI port
ser = serial.Serial(arduinoPort, 9600)

def sendBlink():
    ser.write(b'1')  # Send blink command

# --- Filter Functions ---
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



def handle_sample(sample):
    global ch0, ch1, timestamps, last_processed_index, globalStartTime
    if globalStartTime is None:
        globalStartTime = time.time()

    ch0.append(sample.channels_data[0])
    ch1.append(sample.channels_data[1])
    timestamps.append(time.time())

    stopTime = 25

    if time.time() - globalStartTime > stopTime:  # Stop after 10 seconds
        board.stop_stream()
        print(f"Stream stopped after {stopTime} seconds.")

    while last_processed_index + chunk_size <= len(ch0):
        # Process the next chunk of data
        chunk_ch0 = ch0[last_processed_index:last_processed_index + chunk_size]
        chunk_ch1 = ch1[last_processed_index:last_processed_index + chunk_size]
        chunk_timestamps = timestamps[last_processed_index:last_processed_index + chunk_size]

        # Process the data
        process_data(chunk_ch0, chunk_ch1, chunk_timestamps)

        # Update the last processed index
        last_processed_index += step_size

        

def process_data(ch0, ch1, timestamps):
    global globalStartTime, global_last_blink_time, printed_blinks, printed_double, printed_triple
    fs = 125  # Sampling frequency
    t = np.array(timestamps) - globalStartTime  # Relative time in seconds
    #print(f"Processing chunk from {t[0]: .2f} to {t[-1]: .2f} seconds")
    # Apply filters
    ch0_filtered = highpass_filter(np.array(ch0), cutoff=1.0, fs=fs)
    ch0_filtered = bandstop_notch(ch0_filtered, fs, freq=50)
    ch0_filtered = bandpass(ch0_filtered, fs, low=1, high=50)

    ch1_filtered = highpass_filter(np.array(ch1), cutoff=1.0, fs=fs)
    ch1_filtered = bandstop_notch(ch1_filtered, fs, freq=50)
    ch1_filtered = bandpass(ch1_filtered, fs, low=1, high=50)

    ch0_filtered *= 0.02235  # Scale to microvolts
    ch1_filtered *= 0.02235  # Scale to microvolts

    # Downsample for analysis/display
    downsample_factor = int(fs / 20)
    ch0_filtered = decimate(ch0_filtered, downsample_factor)
    ch1_filtered = decimate(ch1_filtered, downsample_factor)
    x = t[::downsample_factor]


    # Blink detection parameters
    threshold = 135  # µV  (This is tunable based on the person)
    min_distance = int(0.3 * len(x) / (x[-1] - x[0]))  # in samples
    

    # Find negative peaks in channel
    peaks_ch0, _ = find_peaks(-ch0_filtered, height=threshold, distance=min_distance)
    peaks_ch1, _ = find_peaks(-ch1_filtered, height=threshold, distance=min_distance)

    # Match peaks in channel
    times_ch0 = x[peaks_ch0]
    times_ch1 = x[peaks_ch1]

    matched_peaks = []
    tolerance = 0.2  # seconds between peaks in both channels
    for t0 in times_ch0:
        if np.any(np.abs(times_ch1 - t0) <= tolerance):
            matched_peaks.append(t0)
            global_last_blink_time = t0
    
    matched_peaks = [t for t in matched_peaks if t > 2.0] # ignore first 2 seconds of data

    printed_blinks, new_singles = merge_new_events(printed_blinks, matched_peaks)

    if new_singles:
        for t in sorted(new_singles):
            sendBlink()
            print(f"Blink: Time = {t:.3f} s")
    

def merge_new_events(already, new, tol=0.1):
    """
    already: sorted list of times you’ve already printed
    new:     list of newly detected times in this chunk
    tol:     merge tolerance in seconds
    Returns (updated_already, genuinely_new)
    """
    genuinely_new = []
    for t in sorted(new):
        # if it’s not within tol of any time in already, it’s new
        if all(abs(t - t0) > tol for t0 in already):
            genuinely_new.append(t)
            already.append(t)
    already.sort()
    return already, genuinely_new



if __name__ == "__main__":
    chunk_size = 125 * 2  # 2 seconds buffer
    step_size = 62  # 0.5 seconds step
    
    globalStartTime = None
    last_processed_index = 0
    global_last_blink_time = -np.inf
    ch0 = []
    ch1 = []
    timestamps = []
    printed_blinks = []

    
    board = OpenBCICyton(port=openBCIPort, daisy=True)
    time.sleep(2)
    board.start_stream(handle_sample)

    time.sleep(0.1)  # Wait a bit before closing
    ser.close()
