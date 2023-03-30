from requests.models import LocationParseError
import requests
from bs4 import BeautifulSoup
import csv
import re
import threading
import random
import time

def getinfo(soup):
    # NAME OF ORGANIZATION
    content = soup.find("div", {"class": "left-col"})
    if(content == None):
        return ["N/A", "N/A", "N/A", "N/A"]
    orgname = content.find("h1").text.strip()
    if(orgname == "Unknown Organization"):
        return ["N/A", "N/A", "N/A", "N/A"]

    ein = "N/A"
    classification = "N/A"
    taxcode = "N/A"

    # GATHERING INFO
    info = content.find("div", {"class": "profile-info"})
    informationli = info.find_all("li")

    # Going through "li" list of information
    for information in informationli:
        if("EIN" in information.text):
            ein = information.text.strip()
            ein = ein.split(" ")[1]
        if("Classification" in information.text):
            classification = information.text.strip().split("(NTEE)")[1].strip()
            classification = re.sub(r'\n', '', classification)
            classification = re.sub(r'\s+', ' ', classification)
        if("501" in information.text):
            if("501(c)(3)" in information.text):
                taxcode = "Yes"
            else:
                taxcode = "No"

    return([orgname, ein, classification, taxcode])

def getfinancials(revenues_container):
    year = "N/A"
    revenue = "N/A"
    expenses = "N/A"
    income = "N/A"

    # Iterate over each revenue container, skipping the header row
    for revenue_container in revenues_container.find_all("div", {"class": "single-filing"}):
        yearloc = revenue_container.find("h4", {"class": "year-label"})
        if(yearloc != None):
            year = yearloc.text.strip()
            year = year.split(" ")[1]
            revenue_table = revenue_container.find("table", {"class": "revenue"})

            # Write revenue, expenses, income data if exists, else continue
            if(revenue_table!=None):
                pos = revenue_table.find("th", {"class": "pos"})
                if(pos != None):
                    revenueloc = pos.find("h3")
                    if(revenueloc== None):
                        revenue = "N/A"
                    else:
                        revenue = revenueloc.text.strip().replace("$", "").replace(",", "")
                else:
                    revenue == "N/A"
                expensesloc = revenue_table.find("th", {"class": "neg"})
                if(expensesloc == None):
                    expenses = "N/A"
                else:
                    expenses = expensesloc.text.strip().replace("$", "").replace(",", "")
                incomeloc = revenue_table.find("th", {"class": "tablenum pos"})
                if(incomeloc == None):
                    income = "N/A"
                else:
                    income = incomeloc.text.strip().replace("$", "").replace(",", "")

            # If any financial data is filled out, break and write
            if(revenue != "N/A" or expenses != "N/A" or income != "N/A"):
                break
            
    return [year, revenue, expenses, income]

def scrape_org(id, url, sem, writer):
    try:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36 Edge/16.16299",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        ]

        # Set the headers to use a random user agent
        headers = {
            "User-Agent": random.choice(user_agents)
        }
        # Acquire the semaphore before making the request
        sem.acquire()

        # Send a GET request to the URL
        response = requests.get(url)

        # Release the semaphore after the request is complete
        sem.release()

        if(response.status_code != 200):
            return

        # Parse the HTML content of the page with Beautiful Soup
        soup = BeautifulSoup(response.content, "lxml")

        # Find the div with all revenues
        revenues_container = soup.find("div", {"class": "filings"})
        if(revenues_container == None):
            return

        info = []
        financials = []
        info = getinfo(soup)
        if(info[0] == "Unknown Organization" or info[0] == "N/A"):
            return

        financials = getfinancials(revenues_container)

        total = info + financials

        # Acquire the semaphore before writing to the CSV file
        sem.acquire()

        writer.writerow(total)

        # Release the semaphore after writing to the CSV file
        sem.release()
    except Exception as e:
        print(f"Error scraping {url}: {e}")


# Create a semaphore with a maximum of 10 threads allowed to run at a time
sem = threading.Semaphore(100)

# Create a list to hold all threads
threads = []

# Open the CSV file for writing
csv_file = open("revenues.csv", "w", newline="")
writer = csv.writer(csv_file)
writer.writerow(["Name of Organization", "EIN", "Classification", "Nonprofit Tax Code Designation: 501(c)(3)", 
                "FISCAL YEAR", "Total Revenue", "Total Functional Expenses", "Net Income"])

# Open the file with the list of organizations to scrape
orgstxt = open("data-download-pub78.txt", "r")
for line in orgstxt:
    # Get the organization ID and URL
    id = line.split("|")[0]
    url = "https://projects.propublica.org/nonprofits/organizations/" + id

    # Create a thread for each URL request
    thread = threading.Thread(target=scrape_org, args=(id, url, sem, writer))
    threads.append(thread)
    thread.start()
    #time.sleep(random.uniform(1,3))

# Wait for all threads to complete
for thread in threads:
    thread.join()

# Close the CSV and text files
csv_file.close()
orgstxt.close()