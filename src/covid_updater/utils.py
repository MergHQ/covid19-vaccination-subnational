import pandas as pd
from covid_updater.tracking import update_country_tracking


ALL_COLUMNS = ["location", "region", "date", "location_iso", "region_iso", 
             "total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]


def keep_min_date(df):
    df = df.copy()
    cols = df.columns
    # Remove NaNs
    count_cols = ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]
    count_cols = [col for col in count_cols if col in cols]
    df.loc[:, count_cols] = df.loc[:, count_cols].fillna(-1).astype(int)
    # Goup by    
    df = df.groupby(
        by=[col for col in df.columns if col != "date"]
    ).min().reset_index()

    # Bring NaNs back
    df.loc[:, count_cols] = df.loc[:, count_cols].astype("Int64").replace({-1: pd.NA})
    return df.loc[:, cols]


def export_data(df, data_url_reference, output_file):
    locations = df["location"].unique().tolist()
    if len(locations) != 1:
        raise Exception("More than one country detected!")
    country = locations[0]
    last_update = df["date"].max()

    # Reorder columns
    cols = [col for col in ALL_COLUMNS if col in df.columns]
    df = df[cols]

    # Avoid repeating reports
    df = keep_min_date(df)

    # Export
    df = df.sort_values(by=["region", "date"])
    df.to_csv(output_file, index=False)

    # Tracking
    update_country_tracking(
        country=country,
        url=data_url_reference,
        last_update=last_update
    )