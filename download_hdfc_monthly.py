import os
import time
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

# ----- Config -----
TARGET_FOLDER = r"F:\MF Holdings"   # destination folder
PAGE_URL = "https://www.hdfcfund.com/statutory-disclosure/portfolio/monthly-portfolio"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# ----- Helpers -----
def ensure_folder(path):
    os.makedirs(path, exist_ok=True)

def prompt_year_month():
    year = input("Enter year (e.g. 2024): ").strip()
    month_in = input("Enter month (name or number, e.g. Jan or 1 or January): ").strip()
    # normalize month to full name (e.g., 'January')
    month_map = {
        '1': 'January', '01': 'January', 'jan': 'January', 'january': 'January',
        '2': 'February', '02': 'February', 'feb': 'February', 'february': 'February',
        '3': 'March', '03': 'March', 'mar': 'March', 'march': 'March',
        '4': 'April', '04': 'April', 'apr': 'April', 'april': 'April',
        '5': 'May', '05': 'May',
        '6': 'June', '06': 'June', 'jun': 'June', 'june': 'June',
        '7': 'July', '07': 'July', 'jul': 'July', 'july': 'July',
        '8': 'August', '08': 'August', 'aug': 'August', 'august': 'August',
        '9': 'September', '09': 'September', 'sep': 'September', 'september': 'September',
        '10': 'October', 'oct': 'October', 'october': 'October',
        '11': 'November', 'nov': 'November', 'november': 'November',
        '12': 'December', 'dec': 'December', 'december': 'December'
    }
    key = month_in.strip().lower()
    month = month_map.get(key, month_in)  # fallback to raw input if not mapped
    return year, month

def download_file(url, dest_folder, session=None):
    session = session or requests
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename:
        filename = "downloaded.xlsx"
    out_path = os.path.join(dest_folder, filename)
    # avoid overwriting: add suffix if exists
    base, ext = os.path.splitext(out_path)
    counter = 1
    while os.path.exists(out_path):
        out_path = f"{base}({counter}){ext}"
        counter += 1
    print(f"Downloading: {url} -> {out_path}")
    with session.get(url, headers=HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return out_path

# ----- Main scraping function -----
def scrape_and_download(year, month, dest_folder, headless=False, wait_timeout=60):
    ensure_folder(dest_folder)

    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(PAGE_URL)
        wait = WebDriverWait(driver, wait_timeout)

        # Wait for at least one select element to appear on the page
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        except Exception as e:
            # Save debug artifacts: screenshot + page source
            ts = int(time.time())
            debug_png = os.path.join(dest_folder, f"debug_page_{ts}.png")
            debug_html = os.path.join(dest_folder, f"debug_page_{ts}.html")
            try:
                driver.save_screenshot(debug_png)
            except Exception:
                pass
            try:
                with open(debug_html, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except Exception:
                pass
            print(f"Timeout waiting for selects. Saved screenshot: {debug_png} and HTML: {debug_html}")
            raise

        selects = driver.find_elements(By.TAG_NAME, "select")
        found_year = False
        found_month = False

        for s in selects:
            try:
                sel = Select(s)
            except Exception:
                continue
            option_texts = [o.text.strip() for o in sel.options if o.text.strip()]
            # try match year
            if not found_year and any(str(year) == opt or str(year) in opt for opt in option_texts):
                # try exact match first, else choose the option that contains the year string
                try:
                    sel.select_by_visible_text(str(year))
                except Exception:
                    # fallback: find partial match
                    for o in sel.options:
                        if str(year) in o.text:
                            sel.select_by_visible_text(o.text)
                            break
                print(f"Selected year {year} in a select.")
                found_year = True
                time.sleep(0.5)
                continue

            # try match month (visible text likely full month name)
            if not found_month and any(month.lower() == opt.lower() or month.lower() in opt.lower() for opt in option_texts):
                # prefer exact case-insensitive match
                matched = None
                for o in sel.options:
                    if o.text.strip().lower() == month.strip().lower():
                        matched = o.text
                        break
                if not matched:
                    for o in sel.options:
                        if month.strip().lower() in o.text.strip().lower():
                            matched = o.text
                            break
                if matched:
                    sel.select_by_visible_text(matched)
                    print(f"Selected month {matched} in a select.")
                    found_month = True
                    time.sleep(0.5)
                    continue

        if not (found_year and found_month):
            print("Warning: couldn't automatically find both Year and Month selects. Listing selects & options for debugging:")
            for idx, s in enumerate(selects, start=1):
                try:
                    sel = Select(s)
                    print(f"Select #{idx} options: {[o.text for o in sel.options]}")
                except Exception:
                    pass
            print("You may need to adjust the script selectors manually.")
            # continue anyway

        # Find and click a search button (try common patterns)
        # Look for button elements with text 'Search' (case-insensitive)
        clicked = False
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                txt = b.text.strip().lower()
                if "search" in txt or "submit" in txt or "filter" in txt:
                    try:
                        b.click()
                        clicked = True
                        print("Clicked a button with text:", b.text)
                        break
                    except Exception:
                        pass
        except Exception:
            pass

        # If not clicked, try input[type=button] or anchors
        if not clicked:
            try:
                inputs = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit']")
                for inp in inputs:
                    val = inp.get_attribute("value") or ""
                    if "search" in val.lower() or "submit" in val.lower():
                        try:
                            inp.click()
                            clicked = True
                            print("Clicked input button:", val)
                            break
                        except Exception:
                            pass
            except Exception:
                pass

        # wait for results area: detect links to .xls/.xlsx
        # give page JS some time to load results
        time.sleep(2)
        # Wait until at least one link with xls/xlsx is present or timeout
        def links_present(driver):
            elems = driver.find_elements(By.XPATH, "//a[contains(@href,'.xls') or contains(@href,'.xlsx')]")
            return len(elems) > 0

        try:
            wait.until(lambda d: links_present(d))
        except Exception as e:
            # Save debug artifacts for investigation
            ts = int(time.time())
            debug_png = os.path.join(dest_folder, f"debug_links_{ts}.png")
            debug_html = os.path.join(dest_folder, f"debug_links_{ts}.html")
            try:
                driver.save_screenshot(debug_png)
            except Exception:
                pass
            try:
                with open(debug_html, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except Exception:
                pass
            print(f"Timeout waiting for download links. Saved screenshot: {debug_png} and HTML: {debug_html}")
            # continue to try to find any links that may already be present

        links = driver.find_elements(By.XPATH, "//a[contains(@href,'.xls') or contains(@href,'.xlsx')]")
        hrefs = []
        for a in links:
            href = a.get_attribute("href")
            if href and (href.lower().endswith(".xls") or href.lower().endswith(".xlsx")):
                hrefs.append(href)

        # deduplicate preserving order
        seen = set()
        hrefs = [h for h in hrefs if not (h in seen or seen.add(h))]

        if not hrefs:
            # sometimes the table contains buttons that trigger downloads via javascript; try scanning onclick attributes
            onclick_links = []
            anchors = driver.find_elements(By.XPATH, "//*[contains(@onclick,'xls') or contains(@onclick,'xlsx')]")
            for el in anchors:
                onclick = el.get_attribute("onclick") or ""
                # try to extract URL in quotes
                import re
                m = re.search(r"(https?://[^\s'\"\\)]+\.xls[x]?)", onclick)
                if m:
                    url = m.group(1)
                    onclick_links.append(url)
            hrefs = onclick_links

        if not hrefs:
            print("No direct .xls/.xlsx links found after selecting year/month. The page may use dynamic JS or a different flow.")
            # we can optionally print the page html for debugging:
            # print(driver.page_source[:2000])
            return []

        print(f"Found {len(hrefs)} excel file link(s).")

        # Use requests to download each file
        session = requests.Session()
        session.headers.update(HEADERS)

        downloaded_files = []
        for href in hrefs:
            # some links are relative
            full_url = urljoin(PAGE_URL, href)
            try:
                path = download_file(full_url, dest_folder, session=session)
                downloaded_files.append(path)
            except Exception as e:
                print(f"Failed to download {full_url}: {e}")

        return downloaded_files

    finally:
        driver.quit()


if __name__ == "__main__":
    print("HDFC Monthly portfolio Excel downloader")
    y, m = prompt_year_month()
    print(f"Requested year={y}, month={m}")
    dest = TARGET_FOLDER
    downloaded = scrape_and_download(y, m, dest, headless=True)
    if downloaded:
        print("Downloaded files:")
        for p in downloaded:
            print(" ", p)
    else:
        print("No files downloaded. See messages above for debugging tips.")