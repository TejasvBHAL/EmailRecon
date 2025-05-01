
EmailRecon

EmailRecon is an asynchronous OSINT (Open-Source Intelligence) tool designed to discover and collect publicly available email addresses associated with a specific organization. It utilizes Google dorking techniques and recursive web crawling to extract email addresses from websites, documents, and indexed pages. This tool is useful for cybersecurity reconnaissance, penetration testing, and even networking or recruitment research.

🔍 Features

- Extracts organization-specific and general email addresses from web content
- Asynchronous web crawling for high performance and scalability
- Utilizes Google dorking queries for advanced data discovery
- Supports domain-specific targeting and custom search queries
- Saves discovered emails in **CSV** or **PDF** formats
- Interactive email filtering and export options by domain

🛠️ Requirements

- Python 3.7+
- Packages:
  - aiohttp
  - beautifulsoup4
  - fpdf
  - pandas
  - lxml

Install dependencies:

bash
pip install aiohttp beautifulsoup4 fpdf pandas lxml


🚀 Usage

Run the script:

bash
python emailrecon.py

You'll be prompted to:

1. Enter the target organization name (used to filter emails).
2. Provide a starting URL for crawling.
3. Specify how many email addresses to collect.
4. Select from pre-defined Google dorking queries or enter custom ones.

Example dorking queries include:

- site:example.com "email
- filetype:pdf site:example.com
- inurl:login site:example.com
- intext:"contact us" "@example.com

💾 Output

The tool allows saving the results in:

- CSV format (emails.csv)
- PDF format (emails.pdf)
- Domain-based email export filters

You'll be asked during execution how you wish to save the results (e.g., organization-specific vs. other domains).

📘 Example Use Cases

- Penetration Testing: Identify email addresses for phishing simulations or social engineering.
- Red Team Recon: Build a profile of organizational infrastructure from open sources.
- Job Search/Networking: Discover recruiter emails on corporate websites.

⚠️ Disclaimer

This tool is intended **solely for ethical and legal purposes**. Do not use EmailRecon for spamming, unauthorized data collection, or any malicious activity. Always obtain proper authorization before using it in a professional or testing environment.

📄 License

This project is provided without any warranties. Use at your own risk. Licensing terms can be added here based on your preferences.
