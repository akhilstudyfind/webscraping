from requests.models import LocationParseError
import requests
from bs4 import BeautifulSoup
import csv
import re

def getinfo():

    #NAME OF ORGANIZATION
    content = soup.find("div", {"class": "left-col"})
    if(content == None):
        return ["N/A", "N/A", "N/A", "N/A"]
    orgname = content.find("h1").text.strip()
    if(orgname == "Unknown Organization"):
        return ["N/A", "N/A", "N/A", "N/A"]

    ein = "N/A"
    classification = "N/A"
    taxcode = "N/A"

    #GATHERING INFO
    info = content.find("div", {"class": "profile-info"})
    informationli = info.find_all("li")

    #Going through "li" list of information
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

def getfinancials():

    # Iterate over each revenue container, skipping the header row
    for revenue_container in revenues_container.find_all("div", {"class": "single-filing"}):

        yearloc = revenue_container.find("h4", {"class": "year-label"})

        year = "N/A"
        revenue = "N/A"
        expenses = "N/A"
        income = "N/A"

        if(yearloc != None):
            year = yearloc.text.strip()
            year = year.split(" ")[1]
            revenue_table = revenue_container.find("table", {"class": "revenue"})

            #write revenue, expenses, income data if exists, else continue
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

            #if any financial data is filled out, break and write
            if(revenue != "N/A" or expenses != "N/A" or income != "N/A"):
                break
            
    return([year, revenue, expenses, income])

csv_file = open("revenues.csv", "w", newline="")
writer = csv.writer(csv_file)
writer.writerow(["Name of Organization", "EIN", "Classification", "Nonprofit Tax Code Designation: 501(c)(3)", 
                "FISCAL YEAR", "Total Revenue", "Total Functional Expenses", "Net Income"])



count = 0

urlformat = "https://projects.propublica.org/nonprofits/organizations/"

orgstxt = open("data-download-pub78.txt", "r")

for line in orgstxt:
    id = line.split("|")[0]
    url = urlformat+id
    
            
    # Send a GET request to the URL
    response = requests.get(url)
    if(response.status_code != 200):
        continue

    # Parse the HTML content of the page with Beautiful Soup
    soup = BeautifulSoup(response.content, "lxml")

    # Find the div with all revenues
    revenues_container = soup.find("div", {"class": "filings"})
    if(revenues_container == None):
        continue

    # Create a CSV file to write the data to

    info = []
    financials = []
    info = getinfo()
    if(info[0] == "Unknown Organization" or info[0] == "N/A"):
        continue

    
    financials = getfinancials()

    total = info + financials

    #print(total)
    writer.writerow(total)
    count+=1
    if(count > 100):
        break

csv_file.close()
orgstxt.close()


