import asyncio
import aiohttp
import re
import urllib.parse
from bs4 import BeautifulSoup
from collections import deque
import pandas as pd
from fpdf import FPDF
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Pre-built dorking queries
DORKING_QUERIES = [
    'site:example.com "email"',
    'filetype:pdf site:example.com',
    'inurl:login site:example.com',
    'filetype:xls site:example.com',
    'intext:"contact" AND intext:"@example.com"',
    'site:edu "email address"',
    'site:gov "contact us"',
    'intitle:"index of" "emails"',
    'site:org "support" "@example.com"',
    'inurl:directory site:example.com',
    'intext:"email" AND "contact" AND "us"',
    'inurl:profile site:example.com',
    'filetype:doc site:example.com',
    'site:info@example.com',
    'intext:"reach us at" "@example.com"',
    'intext:"for inquiries" "@example.com"',
]

# User Input
Organization = input("Enter the name of Organization: ")
url_list = input("Enter starting URL: ")
email_target_count = int(input("Enter the number of emails to find: "))
print("Select one or more dorking queries (comma-separated numbers or press Enter to skip):")
for i, query in enumerate(DORKING_QUERIES):
    print(f"{i + 1}: {query}")
print("Enter your custom dorking query or press Enter to skip: ")
user_input = input("Select numbers or input custom queries: ")

# Determine the dorking queries to use
dork_queries = []
if user_input:
    for num in user_input.split(','):
        if num.strip().isdigit() and 1 <= int(num.strip()) <= len(DORKING_QUERIES):
            dork_queries.append(DORKING_QUERIES[int(num.strip()) - 1])
        else:
            dork_queries.append(num.strip())

# Configurable parameters
max_urls_to_crawl = 1000  # Max URLs to crawl
timeout_duration = 10      # Timeout duration for HTTP requests

urls = deque([url_list])
scraped_urls = set()
emails = set()
other_emails = set()  # Set to store other found emails
found_domains = set()  # Set to store domains of found emails
count = 0

# Improved email regex pattern to capture more email formats
org_email_pattern = re.compile(fr"[a-zA-Z0-9._%+-]+@{re.escape(Organization)}\.[a-zA-Z0-9.-]+")
general_email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Asynchronous fetch function
async def fetch(url, session):
    try:
        async with session.get(url, timeout=timeout_duration) as response:
            response.raise_for_status()  # Raise an error for bad responses
            return await response.text()
    except Exception as e:
        logging.error(f"Failed to retrieve {url}: {e}")
        return None

# Updated parse_content function with email limit check
def parse_content(html, base_url, path):
    global emails, other_emails, found_domains
    
    # Extract organization-specific and general emails from the page
    new_org_emails = set(org_email_pattern.findall(html))
    extracted_other_emails = set(general_email_pattern.findall(html)) - new_org_emails

    # Add only up to the target count for organization-specific emails
    for email in new_org_emails:
        if len(emails) < email_target_count:
            emails.add(email)
            found_domains.add(email.split('@')[1])
        else:
            break  # Stop further additions if target is reached

    # If target not met with org-specific emails, add general emails
    for email in extracted_other_emails:
        other_emails.add(email)
        found_domains.add(email.split('@')[1])

    # Parse the page for links to follow
    soup = BeautifulSoup(html, "lxml")
    for anchor in soup.find_all("a"):
        link = anchor.get('href', '')
        # Normalize and deduplicate links
        if link.startswith('/'):
            link = base_url + link
        elif not link.startswith('http'):
            link = path + link

        if link not in urls and link not in scraped_urls:
            urls.append(link)

# Functions to save emails to CSV and PDF
def save_emails_to_csv(emails):
    df = pd.DataFrame(list(emails), columns=["Emails"])
    df.to_csv("emails.csv", index=False)
    logging.info("Emails saved to emails.csv.")

def save_emails_to_pdf(emails):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Emails Found", ln=True, align='C')
    
    for email in emails:
        pdf.cell(200, 10, txt=email, ln=True)
    
    pdf.output("emails.pdf")
    logging.info("Emails saved to emails.pdf.")

# Main function to manage async crawling
async def crawl():
    global count
    async with aiohttp.ClientSession() as session:
        while urls and len(emails) < email_target_count and count < max_urls_to_crawl:
            url = urls.popleft()
            count += 1

            logging.info(f"[{count}] Processing {url}")

            # Fetch the content asynchronously
            html = await fetch(url, session)
            if html:
                scraped_urls.add(url)
                parse_content(html, urllib.parse.urlsplit(url).scheme + "://" + urllib.parse.urlsplit(url).netloc, url[:url.rfind('/') + 1])

                # Check after every 30 URLs processed
                if count % 30 == 0:
                    # Only preview if target emails are not found
                    if email_target_count!=0:
                        logging.info(f"\n[Preview after {count} URLs]")
                        if emails:
                            logging.info(f"[Emails Found for {Organization}]")
                            for mail in emails:
                                logging.info(mail)
                        if other_emails:
                            logging.info(f"[Other Emails Found]")
                            for other_email in other_emails:
                                logging.info(other_email)

                        # Ask user for saving options for emails found so far
                        if emails or other_emails:
                            save_choice = input("Do you want to save the emails found so far? (y/n): ").strip().lower()
                            if save_choice == 'y':
                                # If organization-specific emails are found, ask for saving format
                                if emails:
                                    save_format = input("In which format do you want to save the organization-specific emails? (csv/pdf/both): ").strip().lower()
                                    if save_format == 'csv':
                                        save_emails_to_csv(emails)
                                    elif save_format == 'pdf':
                                        save_emails_to_pdf(emails)
                                    elif save_format == 'both':
                                        save_emails_to_csv(emails)
                                        save_emails_to_pdf(emails)

                                # Ask for saving specific domain emails from other emails
                                if other_emails:
                                    logging.info("Select which domain emails you want to save (comma-separated):")
                                    unique_domains = sorted(set(email.split('@')[1] for email in other_emails))  # Collect unique domains
                                    for i, domain in enumerate(unique_domains):
                                        logging.info(f"{i + 1}: {domain}")
                                    logging.info("Press 'a' to save all emails.")
                                    domain_input = input("Your choice: ").strip().lower()

                                    # Save specific domains or all based on user input
                                    if domain_input == 'a':
                                        save_format = input("In which format do you want to save the other emails? (csv/pdf/both): ").strip().lower()
                                        if save_format == 'csv':
                                            save_emails_to_csv(other_emails)
                                        elif save_format == 'pdf':
                                            save_emails_to_pdf(other_emails)
                                        elif save_format == 'both':
                                            save_emails_to_csv(other_emails)
                                            save_emails_to_pdf(other_emails)
                                    else:
                                        # Validate selected domains
                                        selected_emails = []
                                        domain_valid = False
                                        for num in domain_input.split(','):
                                            num = num.strip()
                                            if num.isdigit() and 1 <= int(num) <= len(unique_domains):
                                                selected_domain = unique_domains[int(num) - 1]
                                                selected_emails.extend(email for email in other_emails if email.endswith('@' + selected_domain))
                                                domain_valid = True
                                            elif num in unique_domains:  # Check if user input is a valid domain
                                                selected_emails.extend(email for email in other_emails if email.endswith('@' + num))
                                                domain_valid = True

                                        if not domain_valid:
                                            logging.info("No such domain exists. Please retry.")
                                            continue  # Skip to the next iteration if domain is invalid

                                        # Ask for saving format for selected domain emails
                                        if selected_emails:
                                            save_format = input("In which format do you want to save the selected domain emails? (csv/pdf/both): ").strip().lower()
                                            if save_format == 'csv':
                                                save_emails_to_csv(selected_emails)
                                            elif save_format == 'pdf':
                                                save_emails_to_pdf(selected_emails)
                                            elif save_format == 'both':
                                                save_emails_to_csv(selected_emails)
                                                save_emails_to_pdf(selected_emails)

    # Final saving options after crawling
    if emails or other_emails:
        save_choice = input("Do you want to save all the emails found? (y/n): ").strip().lower()
        if save_choice == 'y':
            if emails:
                save_format = input("In which format do you want to save the organization-specific emails? (csv/pdf/both): ").strip().lower()
                if save_format == 'csv':
                    save_emails_to_csv(emails)
                elif save_format == 'pdf':
                    save_emails_to_pdf(emails)
                elif save_format == 'both':
                    save_emails_to_csv(emails)
                    save_emails_to_pdf(emails)

            if other_emails:
                logging.info("Select which domain emails you want to save (comma-separated):")
                unique_domains = sorted(set(email.split('@')[1] for email in other_emails))
                for i, domain in enumerate(unique_domains):
                    logging.info(f"{i + 1}: {domain}")
                logging.info("Press 'a' to save all emails.")
                domain_input = input("Your choice: ").strip().lower()

                if domain_input == 'a':
                    save_format = input("In which format do you want to save the other emails? (csv/pdf/both): ").strip().lower()
                    if save_format == 'csv':
                        save_emails_to_csv(other_emails)
                    elif save_format == 'pdf':
                        save_emails_to_pdf(other_emails)
                    elif save_format == 'both':
                        save_emails_to_csv(other_emails)
                        save_emails_to_pdf(other_emails)
                else:
                    selected_emails = []
                    domain_valid = False
                    for num in domain_input.split(','):
                        num = num.strip()
                        if num.isdigit() and 1 <= int(num) <= len(unique_domains):
                            selected_domain = unique_domains[int(num) - 1]
                            selected_emails.extend(email for email in other_emails if email.endswith('@' + selected_domain))
                            domain_valid = True
                        elif num in unique_domains:
                            selected_emails.extend(email for email in other_emails if email.endswith('@' + num))
                            domain_valid = True

                    if not domain_valid:
                        logging.info("No such domain exists. Please retry.")
                        return  # Exit if domain is invalid

                    if selected_emails:
                        save_format = input("In which format do you want to save the selected domain emails? (csv/pdf/both): ").strip().lower()
                        if save_format == 'csv':
                            save_emails_to_csv(selected_emails)
                        elif save_format == 'pdf':
                            save_emails_to_pdf(selected_emails)
                        elif save_format == 'both':
                            save_emails_to_csv(selected_emails)
                            save_emails_to_pdf(selected_emails)

asyncio.run(crawl())
