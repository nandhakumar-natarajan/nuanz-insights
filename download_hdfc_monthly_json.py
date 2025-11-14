#!/usr/bin/env python3
"""
Download HDFC Monthly Portfolio Excel files by parsing embedded JSON from the monthly-portfolio page.

Usage:
  python download_hdfc_monthly_json.py --year 2025-2026 --month September --out "F:\\MF Holdings" --dry-run

This script tries a simple requests GET on the page and extracts the JS that contains
"monthPortfolioContent". It parses that object, filters the file list by month+year,
and downloads files to the output directory. Use --dry-run to only list matches.

This is usually more reliable than driving the selectors because the page embeds
the file URLs in a JSON object (seen in the debug HTML you produced).
"""
import argparse
import json
import os
import re
import requests
import sys
from bs4 import BeautifulSoup


def extract_json_object(text, start_at):
    """Return substring of balanced JSON object starting at first '{' at/after start_at."""
    i = text.find('{', start_at)
    if i == -1:
        raise ValueError('No opening brace found')
    depth = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[i:j+1]
    raise ValueError('No matching closing brace found')


def find_month_portfolio_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Find script tags that contain the marker
    scripts = soup.find_all('script')
    marker = 'monthPortfolioContent'
    for s in scripts:
        if not s.string:
            continue
        if marker in s.string:
            try:
                idx = s.string.find(marker)
                # back up a bit to capture the enclosing object (start at marker-50 safely)
                start_search = max(0, idx - 100)
                obj_text = extract_json_object(s.string, start_search)
                # obj_text may be a large JS object containing many keys. We want to locate
                # the monthPortfolioContent value inside it. We'll parse the obj and extract key.
                data = json.loads(obj_text)
                # Try to get monthPortfolioContent directly
                # This will work if the script contains a plain JSON object.
                if 'monthPortfolioContent' in data:
                    return data['monthPortfolioContent']
                # Otherwise, try nested lookup for StatutoryDisclosures -> monthPortfolioContent
                if 'StatutoryDisclosures' in data and 'monthPortfolioContent' in data['StatutoryDisclosures']:
                    return data['StatutoryDisclosures']['monthPortfolioContent']
            except Exception:
                # fallback: try to extract only the monthPortfolioContent object by searching for its key
                txt = s.string
                key_idx = txt.find('"monthPortfolioContent"')
                if key_idx != -1:
                    try:
                        # find the ':' after the key
                        colon_idx = txt.find(':', key_idx)
                        if colon_idx != -1:
                            obj = extract_json_object(txt, colon_idx)
                            return json.loads(obj)
                    except Exception:
                        pass
    raise RuntimeError('monthPortfolioContent not found in any <script> tag')


def download_file(url, dest, session=None):
    s = session or requests.session()
    # stream download
    with s.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        total = r.headers.get('content-length')
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def normalize_month_input(month):
    m = month.strip().lower()
    months = {
        'january':'January','february':'February','march':'March','april':'April','may':'May','june':'June',
        'july':'July','august':'August','september':'September','october':'October','november':'November','december':'December'
    }
    if m in months:
        return months[m]
    # accept short forms
    short_map = {k[:3]:v for k,v in months.items()}
    if m[:3] in short_map:
        return short_map[m[:3]]
    raise ValueError('Unknown month: %s' % month)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--year', '-y', help="Fiscal year string like '2025-2026' or '2025'", required=False)
    p.add_argument('--month', '-m', help='Month name (e.g. September)', required=True)
    p.add_argument('--out', '-o', help=r'Output directory (default: F:\\MF Holdings)', default=r'F:\MF Holdings')
    p.add_argument('--url', help='Page URL (default monthly portfolio)', default='https://www.hdfcfund.com/statutory-disclosure/portfolio/monthly-portfolio')
    p.add_argument('--dry-run', action='store_true', help='Only list matches, do not download')
    args = p.parse_args()

    month = normalize_month_input(args.month)
    year_num = None
    if args.year:
        # accept '2025-2026' or '2025'
        m = re.match(r'^(\d{4})', args.year)
        if m:
            year_num = m.group(1)
        else:
            # try if user passed fiscal label "2025-2026"
            if '-' in args.year:
                year_num = args.year.split('-')[0]
    # If not provided, don't filter by year

    outdir = os.path.expanduser(args.out)
    os.makedirs(outdir, exist_ok=True)

    print('Fetching page:', args.url)
    resp = requests.get(args.url, timeout=30)
    resp.raise_for_status()
    html = resp.text

    print('Extracting embedded monthPortfolioContent JSON...')
    try:
        mp = find_month_portfolio_content(html)
    except Exception as e:
        print('Error extracting JSON:', e)
        sys.exit(1)

    files = mp.get('files') or []
    print('Total files in JSON:', len(files))

    matches = []
    for entry in files:
        title = entry.get('title') or ''
        fileobj = entry.get('file') or {}
        url = fileobj.get('url')
        if not url:
            continue
        # Filter by month and year appearing in filename or URL
        # Example filename contains '30 September 2025'
        ok_month = month in title or month in url
        ok_year = True
        if year_num:
            ok_year = (year_num in title) or (year_num in url)
        if ok_month and ok_year:
            matches.append((title, url))

    if not matches:
        print('No matching files found for month=%s year=%s' % (month, year_num))
        # As a fallback, list the top 10 files for inspection
        if files:
            print('\nFirst 10 available files:')
            for e in files[:10]:
                t = e.get('title') or ''
                u = (e.get('file') or {}).get('url')
                print('-', t, u)
        sys.exit(0)

    print('\nFound %d matching files:' % len(matches))
    for t, u in matches:
        print('-', t)

    if args.dry_run:
        print('\nDry-run enabled; not downloading. Change to download by removing --dry-run.')
        sys.exit(0)

    session = requests.Session()
    for title, url in matches:
        # sanitize filename
        fname = os.path.basename(url.split('?')[0])
        dest = os.path.join(outdir, fname)
        if os.path.exists(dest):
            print('Skipping existing file:', fname)
            continue
        print('Downloading:', fname)
        try:
            download_file(url, dest, session=session)
            print('Saved to', dest)
        except Exception as exc:
            print('Failed to download', url, '->', exc)


if __name__ == '__main__':
    main()
