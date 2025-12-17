import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_timesjobs(designation, location):
    """Scrapes TimesJobs (Static Content)"""
    jobs = []
    base_url = "https://www.timesjobs.com/candidate/job-search.html"
    params = {
        'searchType': 'personalizedSearch',
        'from': 'submit',
        'txtKeywords': designation,
        'txtLocation': location,
    }
    
    try:
        response = requests.get(base_url, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')
        
        for card in cards:
            try:
                jobs.append({
                    'title': card.find('h2').text.strip(),
                    'company': card.find('h3', class_='joblist-comp-name').text.strip(),
                    'location': location,
                    'link': card.find('a')['href'],
                    'source': 'TimesJobs'
                })
            except: continue
    except Exception as e:
        print(f"TimesJobs Error: {e}")
        
    return jobs

def scrape_careerindia(designation, location):
    """Scrapes CareerIndia (Dynamic Content via Selenium)"""
    jobs = []
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Uncomment to run invisible
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get("https://www.careerindiajobs.com")
        time.sleep(2)

        try:
            # Try finding input by placeholder or name
            kw_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Key') or @name='keywords']")
            kw_input.clear()
            kw_input.send_keys(designation)
            kw_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'job') or contains(@class, 'listing')]")
            for card in cards[:10]:
                text = card.text.split('\n')
                if len(text) > 1:
                    try:
                        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: link = "#"
                    
                    jobs.append({
                        'title': text[0],
                        'company': text[1] if len(text) > 1 else "N/A",
                        'location': location,
                        'link': link,
                        'source': 'CareerIndia'
                    })
        except Exception as e:
            print(f"Interaction Error: {e}")

    except Exception as e:
        print(f"Selenium Error: {e}")
    finally:
        driver.quit()
        
    return jobs