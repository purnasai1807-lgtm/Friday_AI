import os
import datetime
import pywhatkit as kit
from TextToSpeech.Fast_DF_TTS import speak
from os import getcwd

now = datetime.datetime.now()
hour = now.hour
minute = now.minute


def clear_file():
    with open(f"{getcwd()}\\input.txt", "w") as file:
        file.truncate(0)


def send_msg_wa():
    target_number = os.getenv("WHATSAPP_TARGET_NUMBER", "").strip()
    speak("who do you want to send sir ?")
    output_text = ""
    while True:
        with open("input.txt", "r") as file:
            input_text = file.read().lower()
        if input_text != output_text:
            output_text = input_text
            if output_text.startswith("send to") or output_text.startswith("send tu"):
                output_text = output_text.replace("send to", "").replace("send tu", "")
                if target_number:
                    speak("By the way what is the message , sir ?")
                    while True:
                        with open("input.txt", "r") as file:
                            input_text = file.read().lower()
                        if input_text != output_text:
                            output_text = input_text
                            if output_text.startswith("message is"):
                                message = output_text.replace("message is", "")
                                kit.sendwhatmsg(target_number, message, hour, minute + 1)
                                speak("message send successfully")
                                break
                else:
                    speak("No WhatsApp target configured. Set WHATSAPP_TARGET_NUMBER in your environment.")
                    break

