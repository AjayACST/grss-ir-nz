import numpy as np
from readGPS import readGPS
import matplotlib.pyplot as plt

def find_indices(el, az, emin, emax, azim1, azim2):
    condition = (el > emin) & (el < emax) & \
                (az > azim1) & (az < azim2) & \
                (~np.isnan(az)) & (~np.isnan(el))

    indices = np.where(condition)[0]
    if indices.size > 0 and np.max(i) >= el.size:
        az_trnaspose = az.T.flatten()
        condition_transposed = (el > emin) & (el < emax) & \
                               (az_trnaspose > azim1) & (az_trnaspose < azim2)
        indices = np.where(condition_transposed)[0]

    return indices

def smooth(data):
    kernel = np.ones(5) / 5
    return np.convolve(data, kernel, mode='same')
# satlist = np.array(range(32)) #use all GPS satellites
# print(satlist)
pvf = 2 # polynomial order used to remove the direct signal.
# this can be smaller, especially for short eleveation angle ranges.

# this will store a crude median reflector height for a single da/site
avg_mxRH = []
freqtype = 1

min_rh = 0.4 # meters
max_arc_time = 4 # one hour

# Minimum number of points, completely arbitrary for now.
min_points = 100

emin = 5
emax = 30

ediff = 10

cf = 0.1902936
w=4*np.pi/cf

az_range = 45
naz = round(360/az_range)

# TODO: implement for loop, testing is fine to just do this once

azim1 = 225
azim2 = 360-45

gnss_data = readGPS("../data/240606.LOG")

for prn in gnss_data:
    el = np.zeros(len(prn))
    az = np.zeros(len(prn))
    snr = np.zeros(len(prn))
    if len(prn) == 0:
        continue
    for i in range(len(prn)):
        prn_data = prn[i]
        el[i] = prn_data[2]
        az[i] = prn_data[3]
        snr[i] = prn_data[4]
    i = find_indices(el, az, emin, emax, azim1, azim2)

    if i.size == 0:
        continue
    elev_angles = el[i]
    if np.max(elev_angles) - np.min(elev_angles)>ediff:
        snr_db = np.power(10, el[i])

        az_mean = np.mean(az[i])

        # Detrend the data
        p = np.polyfit(elev_angles, snr_db, pvf)
        pv = np.polyval(p, elev_angles)
        save_snr = smooth(snr_db-pv).conj().T

        elev_angles_rad = np.radians(elev_angles) # convert to radians as np does not have sind function
        sine_e = np.sin(elev_angles_rad)

        sorted_x, j = np.unique(sine_e.conj().T, return_index=True)
        es = np.sin(np.radians(0.01))
        Fs = 1/es
        sorted_y = save_snr[j]
        sorted_x_int = np.arange(np.min(sorted_x), np.max(sorted_x) + es, es)
        sorted_y_int = np.interp(sorted_x_int, sorted_x, sorted_y)

        L = np.max(sorted_x_int)-np.min(sorted_x_int)

        freq = np.fft.fft(sorted_y_int)
        hsolve = np.abs(np.fft.fftshift(freq))

        x_values = np.arange(-L/2, L/2, es)
        scaled_x = (Fs / L) * x_values * (cf / 2)
        normalized_hsolve = hsolve/np.max(hsolve)
        plt.plot(scaled_x, normalized_hsolve)
        plt.xlim(-10, 10)
        plt.show()