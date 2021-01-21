"""
Reference: https://github.com/owid/covid-19-data/blob/master/scripts/scripts/vaccinations/automations/batch/denmark.py
"""
import urllib.request
import tabula
import pandas as pd
from bs4  import BeautifulSoup
from datetime import datetime
from utils import merge_iso


source_file = "data/countries/Denmark.csv"


regions = [
    "Hovedstaden",
    "Midtjylland",
    "Nordjylland",
    "Sjælland",
    "Syddanmark"
]

replace = {
    "Ukendt**": "Others",
    "Ukendt*": "Others",
    "Ukendt": "Others",
    "Sjælland": "Sjaelland"
}


def get_date(dfs_from_pdf):
    df = dfs_from_pdf[1]  # Hardcoded
    df = df.drop([0, 1, 2, 3])
    date = pd.to_datetime(df[0], format="%d-%m-%Y").max().strftime("%Y-%m-%d")
    return date


def main():
    # Load current data
    df_source = pd.read_csv(source_file)

    # Load new data
    url = "https://covid19.ssi.dk/overvagningsdata/vaccinationstilslutning"

    # Locate newest pdf
    html_page = urllib.request.urlopen(url)
    soup = BeautifulSoup(html_page, "html.parser")
    pdf_path = soup.find('a', text="Download her").get("href")  # Get path to newest pdf
    # Get preliminary dataframe
    column_string = {'dtype': str , 'header': None}  # Force dtype to be object because of thousand separator
    kwargs = {'pandas_options': column_string,}
    dfs_from_pdf = tabula.read_pdf(pdf_path, pages="all", **kwargs)  # len(dfs_from_pdf) == 8 ?
    #date = datetime.strptime(pdf_path.split("-")[-2], "%d%m%Y").strftime("%Y-%m-%d")
    date = get_date(dfs_from_pdf)

    # Get preliminary dataframe
    column_string = {'dtype': str , 'header': None}  # Force dtype to be object because of thousand separator
    kwargs = {'pandas_options': column_string,}
    dfs_from_pdf = tabula.read_pdf(pdf_path, pages="all", **kwargs)
    df = dfs_from_pdf[2] # Hardcoded

    if df.shape != (11, 7):
        raise Exception("Shape of table changed!")
    if not all(region in df[0].tolist() for region in regions):
        raise Exception("Region missing!")
    
    # Drop columns
    df = df.drop([0, 1, 2, 3, len(df)-1])
    # Rename columns
    df = df.rename(columns={
        0: "region",
        2: "people_vaccinated",
        4: "people_fully_vaccinated"
    })
    df = df.astype(str)

    # Remove numeric 1000-separator
    df.loc[:, "people_vaccinated"] = df.loc[:, "people_vaccinated"].apply(
        lambda x: int(x.replace(".", ""))).fillna(0).astype(int)
    def del_separator(x):
        if x != 'nan':
            return int(x.replace(".", ""))
        else:
            return 0
    df.loc[:, "people_fully_vaccinated"] = df.loc[:, "people_fully_vaccinated"].apply(lambda x: del_separator(x)).astype("Int64")

    # Process region column
    df.loc[:, "region"] = df.loc[:, "region"].replace(replace)

    # Get new columns
    df.loc[:, "total_vaccinations"] = df.loc[:, "people_vaccinated"] + df.loc[:, "people_fully_vaccinated"]
    df.loc[:, "location"]  = "Denmark"
    df.loc[:, "date"]  = date

    # Add ISO codes
    df = merge_iso(df, country_iso="DK")
    df.loc[df["region"]=="Others", "location_iso"] = "DK"

    # Export
    df_source = df_source.loc[~(df_source.loc[:, "date"] == date)]
    df = pd.concat([df, df_source])
    df = df[["location", "region", "date", "location_iso", "region_iso",
             "total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]]
    df = df.sort_values(by=["region", "date"])
    df.to_csv(source_file, index=False)


if __name__ == "__main__":
    main()