import wmi

def get_brightness_windows():
    try:
        w = wmi.WMI(namespace='wmi')
        brightness_methods = w.WmiMonitorBrightness()
        brightness_percentage = brightness_methods[0].CurrentBrightness
        return brightness_percentage
    except Exception as e:
        return f"Error: {e}"

def set_brightness_level():
    try:
        level = input("Enter brightness level (0-100): ")
        if 0 <= level <= 100:
            w = wmi.WMI(namespace='wmi')
            brightness_methods = w.WmiMonitorBrightnessMethods()[0]
            brightness_methods.WmiSetBrightness(level, 0)  # 0 is the timeout in seconds
            return f"Brightness set to {level}%"
        else:
            return "Error: Brightness level must be between 0 and 100"
    except Exception as e:
        return f"Error: {e}"

def check_brightness_percentage():
    brightness = get_brightness_windows()
    print(f"Current Brightness: {brightness}%")

