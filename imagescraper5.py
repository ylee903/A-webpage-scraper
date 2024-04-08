import requests
from bs4 import BeautifulSoup
import os
import time
import urllib.parse
import re  # For sanitizing filenames

def save_state(page_number):
    with open('last_page.txt', 'w') as f:
        f.write(str(page_number))

def load_state():
    try:
        with open('last_page.txt', 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 1  # Start from the beginning if no saved state

def sanitize_filename(text, max_length=255):
    sanitized = re.sub(r'[<>:"/\\|?*]', '', text)
    sanitized = sanitized.rstrip('.')
    reserved_length = 10 + 4  # 10 for page number and space, 4 for extension
    return sanitized[:max_length - reserved_length]

def download_image(image_url, folder_name, page_number, tooltip_text):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    image_extension = image_url.split('.')[-1]
    sanitized_tooltip = sanitize_filename(tooltip_text, max_length=255)
    image_name = f"{page_number:04d} {sanitized_tooltip}.{image_extension}"

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        with open(os.path.join(folder_name, image_name), 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {image_name}")
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for {image_url}")
    except Exception as err:
        print(f"An error occurred: {err} for {image_url}")

def get_next_page(soup, base_url):
    next_link = soup.find('a', rel='next', class_='comicnavlink')
    if next_link and 'href' in next_link.attrs:
        return urllib.parse.urljoin(base_url, next_link['href'])

def scrape_page(url, folder_name, page_number, base_url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    comic_image = soup.find('img', id='comicimage')
    if comic_image and comic_image.get('src'):
        img_url = comic_image['src']
        tooltip_text = comic_image.get('title', '')
        download_image(img_url, folder_name, page_number, tooltip_text)
    
    return get_next_page(soup, base_url)

def main():
    page_number = load_state()  # Load the last saved state
    folder_name = 'comics_images'
    base_url = 'url_here'

    current_url = f"{base_url}{page_number}"  # Adjust the URL based on the saved page number

    while current_url:
        print(f"Scraping page: {current_url}")
        next_page_partial_url = scrape_page(current_url, folder_name, page_number, base_url)
        if next_page_partial_url:
            current_url = next_page_partial_url
            time.sleep(0.1)  # Polite delay
            page_number += 1
            save_state(page_number)  # Save after each successful page scrape
        else:
            print("No more pages to scrape.")
            break

if __name__ == '__main__':
    main()
