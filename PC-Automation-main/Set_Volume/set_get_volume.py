from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Function to get current volume
def get_volume_windows():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_volume = volume.GetMasterVolumeLevelScalar() * 100
    print(f"the device is running on {int(round(current_volume, 2))}  % volume level")

# Function to set the system volume
def set_volume_windows():
    percentage = int(input("Enter the volume percentage (0-100): "))
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    # Convert percentage to scalar value (0.0 to 1.0)
    volume.SetMasterVolumeLevelScalar(percentage / 100, None)
    print(f"Volume set to {percentage}%")
