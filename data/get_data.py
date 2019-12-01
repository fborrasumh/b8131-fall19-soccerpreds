#%% IMPORTS


import os
import pandas as pd
import numpy as np
import pickle
import requests
from bs4 import BeautifulSoup



#%% GETTING RAW DATA FROM DATAHUB AND CONCATENATING


links = [
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1819_csv/data/916634f7ec37dd45c86159bc723eb340/season-1819_csv.csv',
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1718_csv/data/3eb1292e4a07027e7047e46b1dba5a2d/season-1718_csv.csv',
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1617_csv/data/d6b7551d3e130b6e59240d7018524498/season-1617_csv.csv',
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1516_csv/data/09fbe4a898ce2d7d8909ed55c913f2e7/season-1516_csv.csv',
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1415_csv/data/4e5693f4c43c835a61a9cce3d1a2c4f1/season-1415_csv.csv',
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1314_csv/data/2e1cb721e6d34499bda05975afcf11a9/season-1314_csv.csv',
        'https://pkgstore.datahub.io/sports-data/english-premier-league/season-1213_csv/data/5df8e23b4bb4fdd45663452d924597af/season-1213_csv.csv',
]

dfs = list(map(lambda link: pd.read_csv(link), links))
dfs_pruned = list(map(lambda df: df[dfs[0].columns].copy(), dfs))


combined_df = pd.concat(dfs_pruned)
combined_df.to_csv('data/raw_data.csv', index = False)


#%% INITIAL TRANSFORMATIONS AND FILTERING


df = combined_df.copy()

def get_season(row):
    date = row.Date
    year = pd.to_datetime(date, dayfirst=True).year
    month = pd.to_datetime(date).month
    if month < 7: return str(year-1) + '-' + str(year)
    else: return str(year) + '-' + str(year+1)

df['Date'] = pd.to_datetime(df.Date, dayfirst=True)
df['Season'] = df.apply(get_season, axis = 1)

wanted_columns = [
        'Season',
        'Date',
        'HomeTeam',
        'AwayTeam',
        'FTHG',
        'FTAG',
        'FTR',
        'HS',
        'AS',
        'HST',
        'AST',
        'BbAvH',
        'BbAvD',
        'BbAvA'
        ]

clean_df = df[wanted_columns].copy()
clean_df = clean_df.sort_values(by = "Date").reset_index(drop=True)



#%% WEBSCRAPPING MARKET VALUES

# EXTRACTING ALL MARKET VALUES
dates_ref = ['20' + str(y) + '-' + str(m).zfill(2) + '-' + str(1 + d*14).zfill(2) for y in range(10, 20) for m in range(1, 13) for d in range(2)]
rows = []

for date_ref in dates_ref:
    try:
        url = 'https://www.transfermarkt.co.uk/premier-league/marktwerteverein/wettbewerb/GB1/plus/?stichtag=' + date_ref    
        response = requests.get(url, headers={'User-Agent': 'Custom'})
        results_page = BeautifulSoup(response.content, 'lxml')
        set_ = set(results_page.find_all(class_ = "rechts"))
        set_1 = set(results_page.find_all(class_ = "rechts hauptlink"))
        set_2 = set(results_page.find_all(class_ = "rechts greentext"))
        tags = list(set_ - set_1 - set_2)
        
        for tag in tags:
            try:
                team = tag.a['title']
                value_tag = tag.a.string[1:]
                if value_tag[-1] == 'k': value = float(value_tag[:-1])/1000
                elif value_tag[-1] == 'm': value = float(value_tag[:-1])
                elif value_tag[-2:] == 'bn': value = float(value_tag[:-2])*1000
                rows.append([date_ref, team, value])
            except: pass
    except: pass
    
cols = ['date', 'team', 'value']
df_market = pd.DataFrame(rows, columns = cols)



# MAPPING PROPER TEAMS' NAMES
df_raw = clean_df.copy()
teams = df_raw.HomeTeam.unique()
teams_market = df_market.team.unique()

mapping = {}
for team in teams:
    for team_market in teams_market:
        if team in team_market: mapping[team] = team_market

mapping['Man United'] = 'Manchester United'
mapping['Man City'] = 'Manchester City'
mapping['Wolves'] = 'Wolverhampton Wanderers'


# MAPPING TEAM VALUES IN DATASET
def get_values(row):
    date = row.Date
    season = row.Season
    for date_ref in dates_ref[::-1]:
        if date > pd.to_datetime(date_ref): break
    
    try:
        team_h = mapping[row.HomeTeam]
        row['HValue'] = df_market[(df_market.date == date_ref) & (df_market.team == team_h)].value.values[0]
    except: row['HValue'] = -1

    try:
        team_a = mapping[row.AwayTeam]
        row['AValue'] = df_market[(df_market.date == date_ref) & (df_market.team == team_a)].value.values[0]
    except: row['AValue'] = -1
    
    return row

df = df_raw.apply(get_values, axis = 1)

# Teams for which we don't have value are given the season's minimum by default
min_values = df[(df.HValue != -1)].groupby('Season').HValue.min().to_dict()

def fill_values(row):
    if row.HValue == -1:
        season = row.Season
        row['HValue'] = min_values[season]

    if row.AValue == -1:
        season = row.Season
        row['AValue'] = min_values[season]
    
    return row
    
df_final = df.apply(fill_values, axis = 1)

df_final.to_csv('data/cleaned_data.csv', index = False)
