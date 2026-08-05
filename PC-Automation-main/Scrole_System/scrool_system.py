import pyautogui

def scroll_up():
    # Scroll up by pressing the Up arrow key five times
    pyautogui.press('up', presses=5)

def scroll_down():
    # Scroll down by pressing the Down arrow key five times
    pyautogui.press('down', presses=5)

def scroll_to_top():
    # Scroll to the top of the page
    pyautogui.hotkey('home')

def scroll_to_bottom():
    # Scroll to the bottom of the page
    pyautogui.hotkey('end')


