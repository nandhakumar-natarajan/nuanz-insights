"""
download_hdfc_monthly_wire.py

Selenium-wire based downloader for HDFC Monthly Portfolio excel files.

Usage:
    python download_hdfc_monthly_wire.py
"""
import os
import time
import json
import re
import requests
from urllib.parse import urljoin, urlparse
from seleniumwire import webdriver  # pip install selenium-wire
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

PAGE_URL = "https://www.hdfcfund.com/statutory-disclosure/portfolio/monthly-portfolio"
TARGET_FOLDER = r"F:\MF Holdings"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def ensure_folder(path):
    os.makedirs(path, exist_ok=True)

def prompt_year_month():
    year = input("Enter year (e.g. 2024): ").strip()
    month_in = input("Enter month (name or number, e.g. Jan or 1 or January): ").strip()
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
    month = month_map.get(key, month_in)
    return year, month

def download_file(url, dest_folder, session=None, headers=None):
    session = session or requests
    headers = headers or HEADERS
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "download.xlsx"
    out_path = os.path.join(dest_folder, filename)
    base, ext = os.path.splitext(out_path)
    counter = 1
    while os.path.exists(out_path):
        out_path = f"{base}({counter}){ext}"
        counter += 1
    print(f"Downloading {url} -> {out_path}")
    with session.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return out_path

def attempt_close_cookie_banner(driver):
    # common cookie banner texts/selectors
    candidates = [
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'close')]",
        "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
        "//button[contains(@id,'cookie') or contains(@class,'cookie') or contains(@class,'consent')]",
    ]
    for xp in candidates:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    if el.is_displayed():
                        el.click()
                        print("Closed cookie/consent overlay using xpath:", xp)
                        time.sleep(0.5)
                        return True
                except Exception:
                    pass
        except Exception:
            continue
    return False


def click_monthly_tab(driver):
    """Try to click a tab or link that opens the Monthly portfolio view."""
    texts = ["monthly", "monthly portfolio", "monthly-portfolio", "monthly_portfolio"]
    # common xpath patterns for links/buttons/tabs
    xpaths = [
        "//a", "//button", "//li", "//span", "//div"
    ]
    for xp_root in xpaths:
        try:
            els = driver.find_elements(By.XPATH, xp_root)
        except Exception:
            continue
        for el in els:
            try:
                txt = (el.text or "").strip().lower()
                if not txt:
                    # check aria-label or title
                    txt = ((el.get_attribute("aria-label") or "") + " " + (el.get_attribute("title") or "")).strip().lower()
                for t in texts:
                    if t in txt:
                        try:
                            if el.is_displayed():
                                el.click()
                                print("Clicked element with text/title containing:", t)
                                time.sleep(1)
                                return True
                        except Exception:
                            pass
            except Exception:
                continue

    # also try specific xpath that matches nav links with 'monthly'
    try:
        el = driver.find_element(By.XPATH, "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'monthly')]")
        if el and el.is_displayed():
            el.click()
            print("Clicked monthly anchor via xpath")
            time.sleep(1)
            return True
    except Exception:
        pass

    return False


def set_year_month_controls(driver, year, month):
    """Try to set year and month controls by label text, placeholder, name, or aria-label.
    Returns True if any control was set."""
    lowered_year = str(year).lower()
    lowered_month = str(month).lower()
    set_any = False

    # 1) look for labels containing the texts and find associated control
    label_texts = ["search by year", "search by year:", "select month", "select month:", "year", "month"]
    for lbl_text in label_texts:
        try:
            labels = driver.find_elements(By.XPATH, f"//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{lbl_text}')]")
            for lab in labels:
                try:
                    # associated control may be for attribute
                    fid = lab.get_attribute('for')
                    if fid:
                        ctrl = None
                        try:
                            ctrl = driver.find_element(By.ID, fid)
                        except Exception:
                            ctrl = None
                        if ctrl:
                            tag = ctrl.tag_name.lower()
                            if tag == 'select':
                                try:
                                    Select(ctrl).select_by_visible_text(str(year) if 'year' in lbl_text else str(month))
                                    set_any = True
                                except Exception:
                                    pass
                            else:
                                try:
                                    # set value via JS
                                    val = str(year) if 'year' in lbl_text else str(month)
                                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", ctrl, val)
                                    set_any = True
                                except Exception:
                                    pass
                except Exception:
                    continue
        except Exception:
            pass

    # 2) inputs/selects with placeholder or aria-label matching
    try:
        candidates = driver.find_elements(By.XPATH, "//input|//select|//div|//span")
        for c in candidates:
            try:
                pl = (c.get_attribute('placeholder') or '').strip().lower()
                al = (c.get_attribute('aria-label') or '').strip().lower()
                name = (c.get_attribute('name') or '').strip().lower()
                if 'year' in pl or 'year' in al or 'year' in name:
                    # set year
                    try:
                        if c.tag_name.lower() == 'select':
                            Select(c).select_by_visible_text(str(year))
                        else:
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", c, str(year))
                        set_any = True
                    except Exception:
                        pass
                if 'month' in pl or 'month' in al or 'month' in name:
                    try:
                        if c.tag_name.lower() == 'select':
                            Select(c).select_by_visible_text(str(month))
                        else:
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", c, str(month))
                        set_any = True
                    except Exception:
                        pass
            except Exception:
                continue
    except Exception:
        pass

    return set_any

def find_selects_in_current_context(driver):
    selects = driver.find_elements(By.TAG_NAME, "select")
    return selects

def switch_to_frame_if_needed(driver):
    # if no selects found in main context, inspect iframes and switch into one that contains selects
    selects = find_selects_in_current_context(driver)
    if selects:
        return True  # already good
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for f in frames:
        try:
            driver.switch_to.frame(f)
            selects = find_selects_in_current_context(driver)
            if selects:
                print("Switched into iframe for selects.")
                return True
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
    return False

def extract_urls_from_requests(driver):
    urls = []
    for req in driver.requests:
        try:
            # we only consider requests with response
            if not hasattr(req, "response") or req.response is None:
                continue
            u = req.url
            # direct excel links
            if u.lower().endswith(".xls") or u.lower().endswith(".xlsx"):
                urls.append(u)
                continue
            # sometimes the response is a JSON with URLs
            ct = req.response.headers.get("Content-Type", "")
            if "application/json" in ct or "text/json" in ct or req.response.body:
                try:
                    text = req.response.body.decode('utf-8', errors='ignore')
                    # find urls ending with xls/xlsx inside the body
                    for m in re.findall(r"https?://[^'\"\\s>]+\\.(?:xlsx|xls)", text, flags=re.IGNORECASE):
                        urls.append(m)
                    # also try basic JSON parse
                    try:
                        data = json.loads(text)
                        # recursive find strings in JSON
                        def walk(obj):
                            if isinstance(obj, str):
                                if obj.lower().endswith(('.xls', '.xlsx')):
                                    urls.append(obj)
                            elif isinstance(obj, dict):
                                for v in obj.values():
                                    walk(v)
                            elif isinstance(obj, list):
                                for v in obj:
                                    walk(v)
                        walk(data)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            continue
    # dedupe while preserving order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

def scrape_and_download(year, month, dest_folder, headful=True, wait_timeout=40):
    ensure_folder(dest_folder)

    options = webdriver.ChromeOptions()
    if not headful:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # selenium-wire options (optional)
    seleniumwire_options = {
        # 'request_storage_base_dir': '/tmp/seleniumwire',  # adjust if needed
    }

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                              options=options,
                              seleniumwire_options=seleniumwire_options)

    try:
        driver.get(PAGE_URL)
        wait = WebDriverWait(driver, wait_timeout)

        # try close cookie banner if present
        attempt_close_cookie_banner(driver)

        # try clicking the Monthly tab/link so the Monthly view is rendered
        clicked_month = False
        try:
            clicked_month = click_monthly_tab(driver)
        except Exception:
            clicked_month = False

        # if monthly tab wasn't found, try clicking a 'Portfolio' link first then retry
        if not clicked_month:
            try:
                portfolio_el = None
                candidates = driver.find_elements(By.XPATH, "//a|//button|//li|//span")
                for el in candidates:
                    txt = (el.text or "").strip().lower()
                    if 'portfolio' in txt:
                        portfolio_el = el
                        break
                if portfolio_el and portfolio_el.is_displayed():
                    try:
                        portfolio_el.click()
                        print("Clicked 'Portfolio' element to reveal submenu/tabs")
                        time.sleep(1)
                        # retry monthly
                        clicked_month = click_monthly_tab(driver)
                    except Exception:
                        pass
            except Exception:
                pass

        # switch into iframe if selects are inside one
        switched = switch_to_frame_if_needed(driver)

        # try to find selects
        selects = find_selects_in_current_context(driver)
        if not selects:
            # attempt to set year/month via alternative controls (labels/placeholders/custom widgets)
            tried = False
            try:
                tried = set_year_month_controls(driver, year, month)
                if tried:
                    print("Tried setting year/month via heuristic controls; re-checking for selects.")
                    time.sleep(1)
                    selects = find_selects_in_current_context(driver)
            except Exception:
                tried = False

            if not selects:
                print("No <select> elements found after switching frames/cookie handling. Saving debug and aborting.")
                ts = int(time.time())
                debug_html = os.path.join(dest_folder, f"debug_noselects_{ts}.html")
                debug_png = os.path.join(dest_folder, f"debug_noselects_{ts}.png")
                with open(debug_html, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                try:
                    driver.save_screenshot(debug_png)
                except Exception:
                    pass
                print("Saved debug files:", debug_html, debug_png)
                return []

        # find Year and Month selects and set values
        found_year = False
        found_month = False
        for s in selects:
            try:
                sel = Select(s)
            except Exception:
                continue
            option_texts = [o.text.strip() for o in sel.options if o.text.strip()]
            # match year
            if not found_year and any(str(year) == opt or str(year) in opt for opt in option_texts):
                try:
                    sel.select_by_visible_text(str(year))
                except Exception:
                    for o in sel.options:
                        if str(year) in o.text:
                            sel.select_by_visible_text(o.text)
                            break
                found_year = True
                time.sleep(0.5)
                continue
            # match month
            if not found_month and any(month.lower() == opt.lower() or month.lower() in opt.lower() for opt in option_texts):
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
                    found_month = True
                    time.sleep(0.5)
                    continue

        if not (found_year and found_month):
            print("Couldn't find both Year and Month select choices automatically. Found selects (showing options):")
            for idx, s in enumerate(selects, start=1):
                try:
                    sel = Select(s)
                    print(f"Select #{idx} options:", [o.text for o in sel.options][:20])
                except Exception:
                    pass
            # continue anyway to capture network activity

        # Clear previously recorded requests
        driver.requests.clear()

        # Try to find and click a search/filter button
        clicked = False
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                txt = (b.text or "").strip().lower()
                if "search" in txt or "submit" in txt or "filter" in txt:
                    try:
                        b.click()
                        clicked = True
                        break
                    except Exception:
                        pass
        except Exception:
            pass
        if not clicked:
            try:
                inputs = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit']")
                for inp in inputs:
                    val = (inp.get_attribute("value") or "").strip().lower()
                    if "search" in val or "submit" in val:
                        try:
                            inp.click()
                            clicked = True
                            break
                        except Exception:
                            pass
            except Exception:
                pass

        # wait a short while for XHRs to fire
        time.sleep(6)

        # Inspect captured requests for direct excel links or JSON containing links
        found_urls = extract_urls_from_requests(driver)
        if found_urls:
            print(f"Found {len(found_urls)} file URL(s) from network requests.")
        else:
            print("No direct file URLs found in captured requests. Dumping recent requests for inspection:")
            for req in driver.requests[-40:]:
                # print a compact summary
                try:
                    url = req.url
                    status = req.response.status_code if req.response else None
                    ctype = req.response.headers.get('Content-Type') if (req.response and req.response.headers) else None
                    print(url, status, ctype)
                except Exception:
                    pass

        # Build a requests.Session with cookies from the browser so downloads that require cookies work
        session = requests.Session()
        session.headers.update(HEADERS)
        for ck in driver.get_cookies():
            session.cookies.set(ck['name'], ck['value'], domain=ck.get('domain'))

        downloaded = []
        for u in found_urls:
            try:
                full = urljoin(PAGE_URL, u)
                p = download_file(full, dest_folder, session=session, headers=HEADERS)
                downloaded.append(p)
            except Exception as e:
                print("Download failed for", u, ":", e)

        if not downloaded:
            # final attempt: find any anchors on page with .xls/.xlsx href attributes (in-case dynamic loaded)
            anchors = driver.find_elements(By.XPATH, "//a[contains(@href,'.xls') or contains(@href,'.xlsx')]")
            hrefs = []
            for a in anchors:
                href = a.get_attribute("href")
                if href:
                    hrefs.append(href)
            if hrefs:
                print("Found direct anchors on page:", hrefs)
                for h in hrefs:
                    try:
                        fname = download_file(h, dest_folder, session=session, headers=HEADERS)
                        downloaded.append(fname)
                    except Exception as e:
                        print("Failed download:", e)

        if not downloaded:
            ts = int(time.time())
            debug_html = os.path.join(dest_folder, f"debug_afterrequests_{ts}.html")
            debug_png = os.path.join(dest_folder, f"debug_afterrequests_{ts}.png")
            with open(debug_html, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            try:
                driver.save_screenshot(debug_png)
            except Exception:
                pass
            print("No files downloaded. Saved debug files:", debug_html, debug_png)

        return downloaded

    finally:
        driver.quit()

if __name__ == "__main__":
    print("HDFC Monthly downloader (network-capture mode)")
    y, m = prompt_year_month()
    print("Requested:", y, m)
    ensure_folder(TARGET_FOLDER)
    files = scrape_and_download(y, m, TARGET_FOLDER, headful=True)
    if files:
        print("Downloaded files:")
        for f in files:
            print(" ", f)
    else:
        print("No files downloaded. Check debug files in", TARGET_FOLDER)