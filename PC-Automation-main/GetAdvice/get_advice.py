import requests

def get_random_advice():
    res = requests.get("https://api.adviceslip.com/advice").json()
    print(res['slip']['advice'])
