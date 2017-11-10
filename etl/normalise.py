from fuzzywuzzy import fuzz, process
import pandas as pd
import os
import re

df_depts = pd.read_csv('metadata/departments.csv')
df_files = pd.read_json('etl-data/scraped.jsonl', lines=True)

df_files = df_files.loc[df_files['year'] >= 2015]

years = set(df_depts['financial_year'].tolist())
geographic_regions = set(df_depts['geographic_region'].tolist())

for year in years:
    for region in geographic_regions:
        clean_sheets = {}
        clean_chapters = {}

        names = df_files.loc[
            (df_files['geographic_region'] == region) &
            (df_files['year'] == year)
        ]['name'].tolist()

        chapter_names = df_depts.loc[
            (df_depts['geographic_region'] == region) &
            (df_depts['financial_year'] == year)
        ]['chapter_title'].tolist()

        for chapter in chapter_names:
            clean_chapters[re.sub('Vote \d+ : ', '', chapter)] = chapter

        sheets = [name for name in names if 'xls' in name and 'summary' not in name.lower()]

        for sheet in sheets:
            clean_sheets[re.sub('[A-Z]+ - ', '', os.path.splitext(sheet)[0])] = sheet

        for sheet in clean_sheets.keys():
            if 'cogta' in sheet.lower():
                mod_sheet = 'Cooperative Governance and Traditional Affairs'
            elif 'finance' in sheet.lower():
                # This shouldn't replace Treasury with Finance.
                mod_sheet = 'Treasury'
            else:
                mod_sheet = sheet
            chapter = process.extractOne(mod_sheet, clean_chapters.keys(), scorer=fuzz.partial_ratio)[0]
            df_files.loc[
                (df_files['geographic_region'] == region) &
                (df_files['year'] == year) &
                (df_files['name'] == clean_sheets[sheet]),
                'name'
            ] = clean_chapters[chapter]

df_files.sort_values(['geographic_region', 'name'], inplace=True)
df_files.sort_values('year', ascending=False, inplace=True, kind='mergesort')

df_files.to_csv('etl-data/scrape_normalised.csv')
