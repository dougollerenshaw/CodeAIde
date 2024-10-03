import numpy as np
import time

# Generate a random number
random_number = np.random.rand()

# Print the random number with a message
print(f"The random number generated is: {random_number}")

# Simulate a slow-running process
for i in range(5):
    time.sleep(2)  # Wait for 2 seconds
    print(f"Slow process output {i + 1}")
