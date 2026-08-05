# Import the necessary modules
from Battery.Battery import *
from fuzzywuzzy import fuzz  # Optional, use if you install fuzzywuzzy
from Data.data import command_phrases
import threading
import time

def Auto_Brain(cmd):
    for phrase, func in command_phrases.items():
        similarity = fuzz.ratio(cmd.lower(), phrase.lower())
        if similarity >= 85:  # Match threshold
            func()  # Call the associated function
            return  # Exit the function once a match is found
    print("Command not recognized")

# Main loop to accept user input
def main():
    time.sleep(2)
    while True:
        cmd = input("Enter your command: ")
        Auto_Brain(cmd)


t1 = threading.Thread(target=main)
t2 = threading.Thread(target=check_plug1)
t3 = threading.Thread(target=battery_Alert)
t1.start()
t2.start()
t3.start()
t1.join()
t2.join()
t3.join()