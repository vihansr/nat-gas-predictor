import json
from urllib.request import Request, urlopen
import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def get_forecast():
    url = "https://www.investing.com/economic-calendar/natural-gas-storage-386"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "eventHistoryTable386"})

        if table is None:
            # Fallback to any table if specific ID fails
            table = soup.find("table")

        if table is None:
            raise ValueError("Could not find storage data table on the page.")

        # Parse table rows
        rows = []
        for tr in table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cols and len(cols) >= 4:
                rows.append(cols)

        if not rows:
            raise ValueError("No data rows found in the table.")

        def parse_val(val):
            try:
                return float(val.replace('B', '').replace('K', '').strip())
            except:
                return 0.0

        cur_forecast = parse_val(rows[0][3])
        prev_forecast = parse_val(rows[1][3])

        forecast = {
            "current" : cur_forecast,
            "prev" : prev_forecast
        }
        
        return forecast
    except Exception as e:
        print(f"Error in get_forecast: {e}")
        return {"current": 0.0, "prev": 0.0}

def get_storage_data():
    url = "https://ir.eia.gov/ngs/wngsr.txt"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        text = response.text
        lines = text.splitlines()
        
        def find_val_in_line(label, line_hint=None):
            import re
            start_row = 0
            if line_hint is not None:
                start_row = max(0, line_hint - 2)
            
            for i in range(start_row, len(lines)):
                if label.lower() in lines[i].lower():
                    # Clean the line by removing commas and looking for numbers
                    # EIA values are typically at the end of the line or after a colon
                    line = lines[i].replace(',', '')
                    # Regex for numbers: ignoring dates like 12/12/25
                    # We look for a number that isn't preceded or followed by a /
                    # A better way is to split by colon and take the last part
                    if ':' in line:
                        target_part = line.split(':')[-1]
                    else:
                        target_part = line
                        
                    # Find all floats/ints in the target part
                    nums = re.findall(r'-?\d+\.?\d*', target_part)
                    if nums:
                        try:
                            return float(nums[0])
                        except:
                            pass
            return 0.0

        storage = {
            "current": find_val_in_line("Total (", 1), 
            "week_ago": find_val_in_line("Total (", 2),
            "net_change": find_val_in_line("Net Change", 3),
            "imp_flow": find_val_in_line("Implied Flow", 4),
            "yr_ago": find_val_in_line("Year ago stocks", 5),
            "pct_cng_yr_ago": find_val_in_line("from year ago", 6),
            "5_yr_avg": find_val_in_line("5-year avg stocks", 7),
            "pct_cng_5_yr_avg": find_val_in_line("from 5-year avg", 8),
            "exp_change": get_forecast()["prev"]
        }
        
        total_lines = [i for i, line in enumerate(lines) if "total (" in line.lower()]
        if len(total_lines) >= 2:
            storage["current"] = find_val_in_line("Total (", total_lines[0]+1)
            storage["week_ago"] = find_val_in_line("Total (", total_lines[1]+1)
            
        return storage
    except Exception as e:
        print(f"Error in get_storage_data: {e}")
        return {}

def get_rig_count_data():
    url = "https://rigcount.bakerhughes.com/rig-count-overview"

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")
        if table:
            df = pd.read_html(str(table))[0]
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error in get_rig_count_data: {e}")
        return pd.DataFrame()

def get_nat_gas_reports():
    url = "https://natgasweather.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        def safe_get_text(selector_type, class_name, slice_start=0):
            elem = soup.find(selector_type, class_=class_name)
            return elem.get_text().strip()[slice_start:] if elem else "Data not available"

        reps = {
            "daily_head": safe_get_text("div", "elementor-element elementor-element-a3c9f2e elementor-widget elementor-widget-heading"),
            "weekly_report": safe_get_text("div", "elementor-element elementor-element-2bf1038 elementor-widget__width-inherit elementor-widget elementor-widget-text-editor"),
            "daily_report": safe_get_text("div", "elementor-element elementor-element-638200e elementor-widget elementor-widget-text-editor"),
            "day_one_rep": safe_get_text("div", "elementor-element elementor-element-0e0482f elementor-widget elementor-widget-text-editor"),
        }

        return reps
    except Exception as e:
        print(f"Error in get_nat_gas_reports: {e}")
        return {}