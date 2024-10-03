import numpy as np
import matplotlib.pyplot as plt


def decaying_sine_wave():
    # Constants
    print("setting parameters")
    frequency = 2  # Hz
    decay_rate = 0.2  # 20% decay rate
    time = np.linspace(0, 10, 1000)  # Time range from 0 to 10 seconds
    amplitude = np.sin(2 * np.pi * frequency * time) * np.exp(-decay_rate * time)

    np.notacommand()

    plt.show()

    print("done")


# Call the function to display the plot and print amplitudes
decaying_sine_wave()
