import distance
import pandas as pd
import os
import re

df = pd.read_json('etl-data/scraped.jsonl', lines=True)

years = set(df['year'].tolist())
geographic_regions = set(df['geographic_region'].tolist())

for year in years:
    for juris in geographic_regions:
        clean_sheets = {}
        clean_chapters = {}
        names = df.loc[(df['geographic_region'] == juris) & (df['year'] == year)]['name'].tolist()
        chapters = [name for name in names if 'Vote' in name]
        for chapter in chapters:
            clean_chapters[re.sub('Vote \d+ : ', '', chapter)] = chapter
        sheets = [name for name in names if 'xls' in name and 'summary' not in name.lower()]
        for sheet in sheets:
            clean_sheets[re.sub('[A-Z]+ - ', '', os.path.splitext(sheet)[0])] = sheet
        for sheet in clean_sheets.keys():
            if 'cogta' in sheet.lower():
                mod_sheet = 'Cooperative Governance and Traditional Affairs'
            elif 'finance' in sheet.lower():
                mod_sheet = 'Treasury'
            else:
                mod_sheet = sheet
            dist, chapter = sorted(distance.ilevenshtein(mod_sheet, clean_chapters.keys()))[0]
            max_len = max(len(chapter), len(mod_sheet))
            dist_pct = 100 * (max_len-dist) / len(chapter)
            df.loc[(df['geographic_region'] == juris) &
                   (df['year'] == year) &
                   (df['name'] == clean_sheets[sheet]),
                   'name'] = clean_chapters[chapter]

df.to_csv('etl-data/scrape_normalised.csv')
