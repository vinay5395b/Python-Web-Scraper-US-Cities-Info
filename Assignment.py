# -*- coding: utf-8 -*-
"""
Created on Wed May 22 17:02:49 2019

@author: Vinay Burhade
"""

import pandas as pd
from pandas import DataFrame, Series

from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests

url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"
def PageContent(url):
    result = requests.get(url)
    c = result.content
    page_content = BeautifulSoup(c)
    return page_content

content = PageContent(url)    

tables = content.find_all('table')
for table in tables:
    print(table.prettify())
    

table = content.find('table', {'class' : 'wikitable sortable'})
rows = table.find_all('tr')

#Getting individual links for the cities for additional info 
for row in rows:
    cells = row.find_all('td')
    if len(cells) > 1:
        city_link = cells[1].find('a')
        print(city_link.get('href'))
        

        
 #getting Time zone information from individual sites       
def getAdditionalInfo(url):
    try:
        city_page = PageContent('https://en.wikipedia.org' + url)
        table = city_page.find('table', {'class' : 'infobox geography vcard'})
        additional_details = []
        read_content = False
        for tr in table.find_all('tr'):
            if (tr.get('class') == ['mergedtoprow'] and not read_content):
                link = tr.find('a')
                if (link and (link.get_text().strip() == 'Time zone')):
                    read_content = True
            
            elif ((tr.get('class') == ['mergedbottomrow']) or tr.get('class') == ['mergedrow'] and read_content):
                additional_details.append(tr.find('td').get_text().strip('\n'))
                if (tr.find('td').get_text().strip() == 'MDT' or tr.find('td').get_text().strip() == 'CDT' or tr.find('td').get_text().strip() == 'DST' or tr.find('td').get_text().strip() == 'PDT'):
                    read_content = False
        return additional_details
    except Exception as error:
        print('Error occured: {}'.format(error))
        return []


data = []

for row in rows:
    cells = row.find_all('td')
    if len(cells) > 1:
        print(cells[1].get_text())
        city_link = cells[1].find('a')
        city_info = [cell.text.strip('\n') for cell in cells]
        additional_details = getAdditionalInfo(city_link.get('href'))
        #if (len(additional_details) == 1):
        city_info += additional_details
        data.append(city_info)


#getting each city's official website links from individual sites
base = 'https://en.wikipedia.org'
offi_web = []
with requests.Session() as s:
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            city_link = cells[1].find('a')
            r = s.get(base + city_link.get('href'))
            soup = BeautifulSoup(r.content, 'lxml')
            result = soup.select_one('th:contains(Website) + td > [href]')
            #print(result)
            if result is None:
                #print(city, 'selector failed to find url')
                offi_web.append('None')
            else:
                #print(city, result['href'])
                offi_web.append(result['href'])


dataset = pd.DataFrame(data)
dataset[11] = dataset[12]
dataset[12] = dataset[13]

#Arranging the data in appropriate columns  (column mismatch while scraping the data)
dataset[12].apply(str)
result = dataset[12].apply(lambda job: job and job.startswith('UTC'))
dataset[13]=result
idx = (dataset[13] == True )
dataset.loc[idx,[11,12]] = dataset.loc[idx,[12,11]].values

dataset[12] = offi_web

dataset1 = dataset #dataset backup
dataset.drop(dataset.columns[[13,14,15,16,17,18,19,20,21]], axis=1, inplace=True)


# Define column headings
headers = ["Rank","City","State","Population(2017)","Population(2010)","Change(%)","Land Area(sq mi)","Land Area(sq km)","Popuation Density(sq mi)","Popuation Density(sq km)","Coordinates","Time Zone","Official Website"]
dataset.columns = headers


#Selecting only the cities with full info(dropping the cities whose website info returned 'none' or other than an url)
dataset = dataset[dataset['Official Website'].str.contains("http", na=False)]

#cleaning the data
for column in dataset.columns:
    dataset[column] = dataset[column].str.replace(r"\(.*\)", "")
    dataset[column] = dataset[column].str.replace(r"\[.*\]", "")


for column in dataset.columns:
    dataset[column] = dataset[column].str.replace(r'[^\x00-\x7f]', '')


dataset['Time Zone'].apply(str)
dataset.dropna()
dataset = dataset[dataset['Time Zone'].str.contains("UTC", na=False)]

dataset[headers] = dataset[headers].replace({'\%': '', '\+': '', 'sqmi': '', 'km2':'', '\/sqmi':'', '\/km2':''}, regex=True)
dataset[headers] = dataset[headers].replace({'\/': ''}, regex=True)
dataset["Time Zone"] = dataset["Time Zone"].replace({':': '', '0':'', ' ':'', '\-':''}, regex=True)
dataset['Coordinates'] = dataset['Coordinates'].str.replace(r"\(.*\)","")


dataset.to_csv("Dataset.csv", index = False)
