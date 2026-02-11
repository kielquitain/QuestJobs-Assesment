# Indeed Canada Job Scraper

A web scraper that extracts job listings from Indeed Canada and generates HTML tables with clickable job links.

## Features

- Scrapes job listings from Indeed Canada
- Extracts job details (title, company, location, salary)
- Stores data in SQLite database
- Generates dynamic HTML table with clickable job URLs
- Concurrent job fetching for improved performance
- JSON export of scraped data

## Requirements

- Python 3.7+
- Chrome browser (for Selenium WebDriver)
- ChromeDriver (automatically managed by selenium)

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - On Windows:
   ```bash
   venv\Scripts\activate
   ```
   - On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with a URL:

Always add <b>'&l=&from=searchOnHP&l=&from=searchOnHP'</b> in the trail of the url to avoid Cloudflare issues
```bash
python selenium/main.py --url "https://ca.indeed.com/jobs?q=python+software+developer&l=&from=searchOnHP" --out output/selenium/ --db output/selenium/jobs.db
```

### Arguments

- `--url` (required): The Indeed Canada URL to scrape
- `--out` (optional): Output directory for JSON and HTML files (default: `output/selenium/`)
- `--db` (optional): SQLite database file path (default: `output/selenium/jobs.db`)

## Output

The script generates:

1. **jobs.json** - JSON file containing all scraped job data
2. **jobs.html** - Interactive HTML table with clickable job links
3. **jobs.db** - SQLite database containing job records

## Keyword Tests

- Python Software Developer

```bash
python selenium/main.py --url "https://ca.indeed.com/jobs?q=python+software+developer&l=&from=searchOnHP" --out ./results/ --db ./results/jobs.db
```
- Data Mining Engineer
```bash
python selenium/main.py --url "https://ca.indeed.com/jobs?q=data+mining+engineer&l=&from=searchOnHP" --out output/selenium/ --db output/selenium/jobs.db   
```

This will:
- Scrape job listings from the provided URL
- Save data to `./results/jobs.json`
- Create/update `./results/jobs.db` with job records
- Generate `./results/jobs.html` with an interactive table

## Sample Outputs

### HTML Report

![Job Listings Table](output/selenium/screenshots/jobs-html.png)

### Database
![Job Database Table](output/selenium/screenshots/jobs-db.png?v=1)

### Json

![Job Json File](output/selenium/screenshots/jobs-json.png?v=1)


