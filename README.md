# Blink-Detection-OpenBCI
This project takes EEG signals from the OpenBCI kit (Ultracortex + Daisy + Cyton) in real time, filters them and detect when there is a blink.
When a blink is detected, we send a signal serially to my arduino to light up an LED.
When another blink is detected, we send another signal to turn off the LED.

It also contains a file that detects blinks from a recording that is done by the OpenBCI GUI.

!Note that you only need 2 electrodes for this to work, located on Fp1 and Fp2 (using 10-20 system)
## How to run
1. Hook up your OpenBCI through the serial dongle provided with the kit (and change COM port in main.py)
2. Hook up the arduino to your pc with a simple LED and change LEDBlink.ino to follow your connections (also change COM port in main.py)
3. Run main.py and LEDBlink.ino and Enjoy!
