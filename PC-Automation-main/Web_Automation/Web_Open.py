import webbrowser
import json
from googlesearch import search  # For Google search

# Load the websites data from the JSON file
try:
    with open("Web_Automation\\websites.json", "r") as file:
        websites = json.load(file)
except FileNotFoundError:
    websites = {}

# Function to search for a website using Google and return the first result
def google_search_website(name):
    try:
        # Perform a Google search and get the first result
        for url in search(name, num_results=1):
            return url
    except Exception as e:
        print(f"Error during Google search: {e}")
    return None

# Function to add a new website to the JSON file
def add_website_to_json(name, url):
    websites[name] = url
    with open("Web_Automation\\websites.json", "w") as file:
        json.dump(websites, file, indent=4)

# Main function to open websites
def openweb(webname):
    website_name = webname.lower().split()
    counts = {}
    
    # Count occurrences of each website name
    for name in website_name:
        counts[name] = counts.get(name, 0) + 1
    
    urls_to_open = []
    for name, count in counts.items():
        # Check if the website is in the existing dictionary
        if name in websites:
            urls_to_open.extend([websites[name]] * count)
        else:
            # Try to find the website using Google search
            url = google_search_website(name)
            if url:
                print(f"Found and saving new site: {url}")
                add_website_to_json(name, url)  # Add to JSON if found
                urls_to_open.extend([url] * count)
            else:
                print(f"No website found for '{name}' on Google.")
    
    # Open each URL in the list
    for url in urls_to_open:
        webbrowser.open(url)
    
    if urls_to_open:
        print("Opening...")
    else:
        print("No recognized websites to open.")

# Example interactive usage
def open_web():
    user_input = input("Enter a website name :")
    openweb(user_input)
