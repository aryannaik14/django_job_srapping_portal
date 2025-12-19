import requests
from bs4 import BeautifulSoup
import time
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Disable SSL warnings for the verify=False calls
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_guru(designation, location=None):
    """
    Unified Guru Scraper
    1. Tries to find JOBS first.
    2. If no jobs are found, it searches for FREELANCERS (matching your screenshot).
    """
    jobs = []
    
    # 1. Try Scraping Jobs First
    print(f"Debug: Searching Jobs for '{designation}'...")
    jobs = scrape_guru_jobs(designation, location)
    
    # 2. If no jobs found, try Scraping Freelancers
    if not jobs:
        print(f"Debug: No jobs found. Switching to Freelancer search for '{designation}'...")
        jobs = scrape_guru_freelancers(designation, location)
        
    return jobs

def scrape_guru_jobs(designation, location=None):
    """Scrapes the /d/jobs/ endpoint"""
    jobs = []
    # Use the standard query parameter ?q= which is safer
    base_url = f"https://www.guru.com/d/jobs/?q={designation.replace(' ', '+')}"
    
    chrome_options = _get_chrome_options()
    driver = None
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(base_url)
        print(f"Debug: Loaded URL {base_url}")
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Try primary selector 'jobRecord'
        cards = soup.find_all('div', class_='jobRecord')
        
        # Fallback to 'record' if jobRecord is empty (sometimes layout changes)
        if not cards:
            print("Debug: No 'jobRecord' found, trying generic 'record' class...")
            cards = soup.find_all('div', class_='record')
            
        print(f"Debug: Found {len(cards)} cards on page.")

        for card in cards:
            try:
                # Title Extraction
                title_elem = card.find('h2', class_='jobRecord__title') or \
                             card.find('h2', class_='record__title') or \
                             card.find('h3') 
                             
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Link Extraction
                link_tag = title_elem.find('a') or card.find('a')
                link = "https://www.guru.com" + link_tag['href'] if link_tag else "#"
                
                # Client/Company Extraction
                client_elem = card.find('a', class_='jobRecord__clientName') or \
                              card.find('div', class_='identityName')
                client = client_elem.text.strip() if client_elem else "Client"
                
                # Location Extraction
                # Guru location is often in a span with class 'jobRecord__meta--location' or just 'location'
                loc_elem = card.find('span', class_='jobRecord__meta--location') or \
                           card.find('span', class_='location')
                job_location = loc_elem.text.strip() if loc_elem else "Remote"
                
                print(f"Debug: Scraped '{title}' at '{job_location}'")

                # Location Filtering Logic
                if location and location.lower() != "remote":
                    # Check if user's location matches the job location OR if job is "Remote"
                    # We often want to see Remote jobs even if we searched for a specific city
                    is_match = location.lower() in job_location.lower()
                    is_remote_job = "remote" in job_location.lower()
                    
                    if not is_match and not is_remote_job:
                        print(f"Debug: Skipping '{title}' (Location mismatch: {job_location} vs {location})")
                        continue

                jobs.append({
                    'title': title,
                    'company': client, 
                    'location': job_location,
                    'link': link,
                    'source': 'Guru Jobs'
                })
            except Exception as e:
                 print(f"Debug: Error parsing card: {e}")
                 continue
            
    except Exception as e:
        print(f"Job Scraper Error: {e}")
    finally:
        if driver: driver.quit()
        
    return jobs

def scrape_guru_freelancers(designation, location=None):
    """
    Scrapes the /d/freelancers/ endpoint.
    Matches the HTML structure from your screenshot (div.record, freelancerAvatar).
    """
    freelancers = []
    # Use the freelancers search URL
    base_url = f"https://www.guru.com/d/freelancers/?q={designation.replace(' ', '+')}"
    
    chrome_options = _get_chrome_options()
    driver = None
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(base_url)
        time.sleep(5)
        
        # Scroll to load more
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # TARGETING THE CLASS FROM YOUR SCREENSHOT: 'record__details' inside 'div.record'
        # Or simply 'div.record' which is the main container for freelancers
        cards = soup.find_all('div', class_='record')
        
        if not cards:
            print("Debug: No freelancer records found.")
            
        for card in cards:
            try:
                # 1. Extract Name (from freelancerAvatar__screenName)
                name_tag = card.find('p', class_='freelancerAvatar__screenName')
                name = name_tag.text.strip() if name_tag else "Freelancer"
                
                # 2. Extract Title (The main service title, usually in an h3 or similar)
                # In freelancer view, the title is often the first service listed or the profile title
                title_tag = card.find('h3', class_='record__serviceTitle') or \
                            card.find('a', class_='serviceTitle')
                title = title_tag.text.strip() if title_tag else f"{designation} Specialist"
                
                # 3. Extract Link
                link_tag = card.find('a', href=True)
                link = "https://www.guru.com" + link_tag['href'] if link_tag else "#"
                
                # 4. Extract Location from attributes (as seen in your screenshot)
                # Your screenshot showed <div class="module_avatar" city="Bengaluru" ...>
                avatar_div = card.find('div', class_='module_avatar')
                city = avatar_div.get('city', '') if avatar_div else ""
                country = avatar_div.get('country', '') if avatar_div else ""
                
                full_location = f"{city}, {country}".strip(', ')
                if not full_location:
                    full_location = "Remote"

                # Filter by location if user specified one
                if location and location.lower() != "remote":
                    if location.lower() not in full_location.lower():
                        continue

                freelancers.append({
                    'title': title,           # e.g., "Python Developer"
                    'company': name,          # Freelancer Name
                    'location': full_location, # e.g., "Bangalore, India"
                    'link': link,
                    'source': 'Guru Freelancers'
                })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Freelancer Scraper Error: {e}")
    finally:
        if driver: driver.quit()
        
    return freelancers

def _get_chrome_options():
    options = Options()
    # options.add_argument("--headless") # Keep visible for debugging
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return options

# Keep the featured fallback just in case
def scrape_guru_featured(designation, location=None):
    return scrape_guru(designation, location)