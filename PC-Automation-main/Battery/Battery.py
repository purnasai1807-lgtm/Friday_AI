# pip install psutil
# CTRL + J Terminal 

import psutil
import time
import time

battery = psutil.sensors_battery()


def battery_Alert():
    print("Battery Alert Function Started")
    plugged_in = psutil.sensors_battery().power_plugged
    fully_charged_notified = False
    low_battery_notified = False

    while True:
        battery = psutil.sensors_battery()
        percentage = int(battery.percent)
        is_plugged = battery.power_plugged

        # Check if fully charged and unplugged
        if percentage == 100 and not is_plugged:
            if not fully_charged_notified:
                print("100% charged. Please unplug it.")
                fully_charged_notified = True
        else:
            fully_charged_notified = False  # Reset notification when unplugged or charging

        # Check for low battery when unplugged
        if not is_plugged:
            if percentage <= 20 and not low_battery_notified:
                if percentage <= 5:
                    print("Sir, Sorry to disturb you but this is your last chance, charge your system now")
                elif percentage <= 10:
                    print("Sir, Sorry to disturb you but we are running on very low battery power")
                elif percentage <= 20:
                    print("Sir, Sorry to disturb you but battery is low now")
                low_battery_notified = True
            elif percentage > 20:
                low_battery_notified = False  # Reset when battery goes above 20%
        else:
            low_battery_notified = False  # Reset if plugged in

        time.sleep(10)


def check_plug1():
    print("Checking Charging Status...")
    previous_state = None  # Initialize previous state as None

    while True:
        battery = psutil.sensors_battery()
        current_state = battery.power_plugged

        # Check if the state has changed
        if current_state != previous_state:
            if current_state:
                print("Charging status : Started")
            else:
                print("charging status : Stopped")
            
            previous_state = current_state  # Update the previous state

        time.sleep(1) 

def check_plug():
    battery = psutil.sensors_battery()
    if battery.power_plugged:
        print("Charging Started")
    else:
        print("Charging Stopped")



def check_percentage():
    battery = psutil.sensors_battery()
    percent = int(battery.percent)
    print(f"The device is running on {percent}% power")

