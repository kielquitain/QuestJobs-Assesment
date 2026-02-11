from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import argparse
import sqlite3
import json
import os
import time

BASE_URL = "https://ca.indeed.com"

def scrape_jobs_from_soup(soup):
    """Scrape job URLs from BeautifulSoup object"""
    job_urls = []
    cards = soup.find_all('div', attrs={'class': 'job_seen_beacon'})
    for container in cards:
        href = container.get('href') or (container.find('a') and container.find('a').get('href'))
        job_url = urljoin(BASE_URL, href) if href else None
        job_urls.append(job_url)
    return job_urls

def fetch_job_detail(url, headless=False, timeout=10):
    """Fetch job detail from a given URL using Selenium"""
    opts = Options()
    if not headless:
        pass
    else:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, timeout)
    try:
        time.sleep(0.5)
        driver.get(url)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1, #jobDescriptionText, .jobsearch-jobDescriptionText")))
        except Exception:
            time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        detail = parse_detail_panel(soup)
        detail['job_url'] = url
        return detail
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {'job_title': None, 'company': None, 'location': None, 'salary': None, 'description': None, 'job_url': url, 'source': 'indeed', 'error': str(e)}
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def save_jobs_to_sqlite(results, db_name='jobs.db'):
    """Save job results to SQLite database"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        job_title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        job_url TEXT UNIQUE,
        source TEXT,
        scraped_at TEXT
    )''')
    
    for job in results:
        try:
            cursor.execute('''INSERT OR IGNORE INTO jobs 
                (job_title, company, location, salary, job_url, source, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (job.get('job_title'), job.get('company'), job.get('location'), 
                    job.get('salary'), job.get('job_url'), job.get('source'), 
                    job.get('scraped_at')))
        except Exception as e:
            print(f"Error saving job: {e}")
    
    conn.commit()
    conn.close()
   

def process_job_urls_concurrent(job_urls, headless=False, max_workers=3):
    """Process job URLs concurrently to fetch job details"""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_job_detail, url, headless): url for url in job_urls}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {futures[future]}: {e}")
    return results

def parse_detail_panel(soup):
    """Parse job detail panel from BeautifulSoup object."""
    try:
        job_title_elem = soup.find('h1')
        job_title = job_title_elem.get_text(strip=True) if job_title_elem else None
        
        company_container = soup.find('div', {"data-testid":'jobsearch-CompanyInfoContainer'})
        company = company_container.find('a').get_text(strip=True) if company_container and company_container.find('a') else None
        
        location_elem = soup.find('div', {"data-testid":'inlineHeader-companyLocation'})
        location = location_elem.get_text(strip=True) if location_elem else None
        
        salary_container = soup.find('div', {"data-testid":'jobsearch-OtherJobDetailsContainer'})
        salary_elem = salary_container.find('span') if salary_container else None
        salary_text = salary_elem.get_text(strip=True) if salary_elem else "Undisclosed Salary"
        salary = salary_text if "$" in salary_text else "Undisclosed Salary"
        
        description_elem = soup.find('div', class_='jobsearch-JobComponent-description')

        job_details = {
            'job_title': job_title,
            'company': company,
            'location': location,
            'salary': salary,
            'description': str(description_elem),
            'source': 'indeed',
            'scraped_at': time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        return job_details
    except Exception as e:
        print(f"Error parsing detail panel: {e}")


def generate_html_table(db_name='jobs.db', output_file='output/selenium/jobs.html'):
    """Generate an HTML table from job database with clickable URLs."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT job_title, company, location, salary, job_url, scraped_at FROM jobs')
        rows = cursor.fetchall()
        row_count = len(rows)
        print(f"Generating HTML table with {row_count} rows")
    except Exception as e:
        print(f"Error querying database: {e}")
        rows = []
        row_count = 0
    finally:
        conn.close()
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QuestJob Technical Assessment Job Listings</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Job Listings</h1>
        <p>Total Jobs Scraped: <b>{}</b></p>
        <table>
            <thead>
                <tr>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Salary</th>
                    <th>Job URL</th>
                    <th>Scraped At</th>
                </tr>
            </thead>
            <tbody>
    """.format(row_count, row_count)
    
    for row in rows:
        job_title = row[0] or 'N/A'
        company = row[1] or 'N/A'
        location = row[2] or 'N/A'
        salary = row[3] or 'N/A'
        job_url = row[4] or '#'
        scraped_at = row[5] or 'N/A'
        
        html_content += f"""
                <tr>
                    <td>{job_title}</td>
                    <td>{company}</td>
                    <td>{location}</td>
                    <td>{salary}</td>
                    <td><a href="{job_url}" target="_blank">View Job</a></td>
                    <td>{scraped_at}</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML table saved to {output_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument("--out", default="output/selenium/", help="Output directory")
    parser.add_argument("--db", default="output/selenium/jobs.db", help="Database file path")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.out, exist_ok=True)
    
    print(f"Scraping: {args.url}")
    print(f"Output dir: {args.out}")
    print(f"Database: {args.db}")
    
    driver = webdriver.Chrome()
    try:
        driver.get(args.url)
        time.sleep(6)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        jobs = scrape_jobs_from_soup(soup)
        print(f"Found {len(jobs)} job URLs")
        results = process_job_urls_concurrent(jobs, max_workers=3, headless=False)
        
        # Save results to output directory as JSON
        output_file = os.path.join(args.out, 'jobs.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Scraped {len(results)} job details")

        save_jobs_to_sqlite(results, db_name=args.db)
        print(f"Saved to {args.db}")

        # Generate HTML table from database with clickable links
        html_file = os.path.join(args.out, 'jobs.html')
        generate_html_table(db_name=args.db, output_file=html_file)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()