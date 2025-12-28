import pandas as pd
from IPython.display import display, clear_output
import os


#function to filter only nuclear
def extract_nuclear_generation(year):
    input_file = f"923_{year}.csv"
    output_file = f"nuclear_generation_{year}.csv"

    #skiprows to get to actual informational rows
    #low memory to prevent dtype errors
    df = pd.read_csv(input_file, skiprows=5, low_memory=False)

    #remove the newline that comes before reported fuel type code
    df.columns = df.columns.str.replace("\n", " ").str.strip()

    #filter to just nuclear
    nuclear_df = df[df["Reported Fuel Type Code"] == "NUC"]

    #create new filtered file
    nuclear_df.to_csv(output_file, index=False)

#call on the function to loop for all years
years = [2021, 2022, 2023, 2024]
for year in years:
    extract_nuclear_generation(year)

#acknowledge all files
df20 = pd.read_csv("nuclear_generation_2021.csv")
df21 = pd.read_csv("nuclear_generation_2022.csv")
df22 = pd.read_csv("nuclear_generation_2023.csv")
df23 = pd.read_csv("nuclear_generation_2024.csv")

#combine all files
combined = pd.concat([df20, df21, df22, df23], ignore_index=True)

#reclean file names
combined.columns = combined.columns.str.replace("\n", " ").str.strip()

#save new combined data
combined.to_csv("nuclear_generation_combined.csv", index=False)

#reads previously made file
df = pd.read_csv("nuclear_generation_combined.csv")

#grabs the netgen (net generation) of each column
netgen_cols = [col for col in df.columns if col.startswith("Netgen")]

#changes netgen values from strings to integers, allowing math
df[netgen_cols] = (
    df[netgen_cols]
    .replace({",": ""}, regex=True)
    .apply(pd.to_numeric, errors="coerce")
)

#groups plants together so they can be evaluated on the plant level
plant_year_df = (
    df
    .groupby(["Plant Name", "YEAR"])[netgen_cols]
    .sum()
    .reset_index()
)

#saves file as data by plant
plant_year_df.to_csv("nuclear_generation_plant_level.csv", index=False)

#brings up the data thus far
df = pd.read_csv("nuclear_generation_plant_level.csv")

#acknowledges netgen columns
netgen_cols = [col for col in df.columns if col.startswith("Netgen")]

#melt to swap columns and rows
ts_df = pd.melt(
    df,
    id_vars=["Plant Name", "YEAR"],
    value_vars=netgen_cols,
    var_name="Month",
    value_name="Netgen_MWh"
)

#Gets rid of the netgen before each month to look better
ts_df["Month"] = ts_df["Month"].str.replace("Netgen ", "")

#creates new file
ts_df.to_csv("nuclear_generation_update.csv", index=False)

#load up data 
gen_df = pd.read_csv("nuclear_generation_update.csv") 

#cleanup 
gen_df["Plant Name"] = gen_df["Plant Name"].astype(str).str.strip()

#adjusts for negative netgen numbers found in data 
#makes them clip to 0 as is typical for calculating capacity factor 
#usually negative due to factors like downtime, waiting on supplies, etc 
gen_df["Netgen_MWh"] = pd.to_numeric(gen_df["Netgen_MWh"], errors="coerce")
gen_df["Netgen_MWh"] = gen_df["Netgen_MWh"].clip(lower=0) 

#other dataframe 
#low memory to reduce dtype issues
cap_df = pd.read_csv("860_2024.csv", header=1, low_memory=False) 

#cleanup 
cap_df.columns = cap_df.columns.str.replace("\n", " ").str.strip() 
cap_df["Plant Name"] = cap_df["Plant Name"].astype(str).str.strip() 

#finds correct column within the file for capacity
capacity_candidates = [c for c in cap_df.columns if ("Capacity" in c and "Summer" in c)]

#exact match force
if "Summer Capacity (MW)" in capacity_candidates:
    capacity_col = "Summer Capacity (MW)"
else:
    capacity_col = capacity_candidates[0]

cap_df[capacity_col] = pd.to_numeric(cap_df[capacity_col], errors="coerce")


#capacity to plant level 
cap_plant = ( 
    cap_df 
    .groupby("Plant Name", as_index=False)[capacity_col] 
    .sum() 
    # (added) rename so your later code can keep using the same column name
    .rename(columns={capacity_col: "Net Summer Capacity (MW)"})
) 

#combine generation and capacity 
df = gen_df.merge( 
    cap_plant, 
    on="Plant Name", 
    how="left" 
)

#drops extra sets that dont belong in the dataset
df = df.dropna(subset=["Net Summer Capacity (MW)"])

#creates hours in each month for max possible generation
days_in_month = {
    "January": 31, "February": 28, "March": 31, "April": 30,
    "May": 31, "June": 30, "July": 31, "August": 31,
    "September": 30, "October": 31, "November": 30, "December": 31
}

#leap year fix (2024 is leap year)
df["DaysInMonth"] = df["Month"].map(days_in_month)
df.loc[(df["YEAR"] == 2024) & (df["Month"] == "February"), "DaysInMonth"] = 29

#converts days to hours
df["HoursInMonth"] = df["DaysInMonth"] * 24

#max possible generation
df["MaxPossible_MWh"] = df["Net Summer Capacity (MW)"] * df["HoursInMonth"]

#raw capacity factor, slightly higher due to capacity rating conventions
df = df[(df["Net Summer Capacity (MW)"] > 0) & (df["HoursInMonth"] > 0)]
df["RawCapacityFactor"] = df["Netgen_MWh"] / df["MaxPossible_MWh"]
df = df[df["RawCapacityFactor"] <= 1.2]

#rounded capacity factor
df["CapacityFactor"] = df["Netgen_MWh"] / df["MaxPossible_MWh"]
#clip to 0-1 for capacity factor
df["CapacityFactor"] = df["CapacityFactor"].clip(lower=0, upper=1)

#months now sort in calendar order
month_order = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

# create datetime column for plotting
df["Date"] = pd.to_datetime(
    df["YEAR"].astype(str) + "-" + df["Month"].astype(str) + "-01",
    errors="coerce"
)

#annual capacity facotr by plant
annual_cf = (
    df
    .groupby(["Plant Name", "YEAR"], as_index=False)
    .agg({
        "Netgen_MWh": "sum",
        "MaxPossible_MWh": "sum"
    })
)

annual_cf["CapacityFactor"] = annual_cf["Netgen_MWh"] / annual_cf["MaxPossible_MWh"]

#removes outlier 0s from data that arise from extended outages
annual_cf = annual_cf[annual_cf["CapacityFactor"] > 0]



#average capacity factor across all years for each plant
plant_ranking = (
    annual_cf
    .groupby("Plant Name", as_index=False)["CapacityFactor"]
    .mean()
    .sort_values("CapacityFactor", ascending=False)
)
#displays top 10 plants by avg capacity factor
print("Top 10 plants by average capacity factor (2021–2024):")
display(plant_ranking.head(10))

#displays bottom 10 plants by avg capacity factor
print("Bottom 10 plants by average capacity factor (2021–2024):")
display(plant_ranking.tail(10))

#downloads plant rankings by avg capacity factor
os.makedirs("outputs", exist_ok=True)
plant_ranking.to_csv(os.path.join("outputs", "plant_ranking.csv"), index=False)


#displays top 15 plants by capacity factor, with a table including the following data
display(df[["Plant Name","CapacityFactor", "RawCapacityFactor","YEAR","Month","Netgen_MWh","Net Summer Capacity (MW)"]].head(15))

#re-numbers index for aesthetic purposes
plant_ranking = plant_ranking.reset_index(drop=True)

import matplotlib.pyplot as plt
import ipywidgets as widgets

# dropdown options
plant_list = sorted(df["Plant Name"].dropna().unique())

plant_dropdown = widgets.Dropdown(
    options=plant_list,
    value=plant_list[0],
    description="Plant:",
    layout=widgets.Layout(width="500px")
)

year_range = widgets.SelectionRangeSlider(
    options=sorted(df["YEAR"].dropna().unique()),
    index=(0, len(sorted(df["YEAR"].dropna().unique())) - 1),
    description="Years:",
    layout=widgets.Layout(width="500px")
)

save_button = widgets.Button(
    description="Save plot",
    button_style="success"
)

out = widgets.Output()

def draw_plot(save=False):
    with out:
        clear_output(wait=True)

        plant = plant_dropdown.value
        y0, y1 = year_range.value

        plant_ts = df[
            (df["Plant Name"] == plant) &
            (df["YEAR"] >= y0) & (df["YEAR"] <= y1)
        ].copy()

        plant_ts = plant_ts.sort_values("Date")

        plt.figure(figsize=(10,5))
        plt.plot(plant_ts["Date"], plant_ts["CapacityFactor"], marker="o")
        plt.ylabel("Capacity Factor")
        plt.title(f"Monthly Capacity Factor – {plant} ({y0}-{y1})")
        plt.ylim(0, 1.1)
        plt.tight_layout()

        if save:
            os.makedirs("outputs", exist_ok=True)
            filename = os.path.join(
                "outputs",
                f"capacity_factor_{plant.replace(' ', '_')}_{y0}_{y1}.png"
            )
            plt.savefig(filename, dpi=300)
            print(f"Saved: {filename}")


        plt.show()

def update_plot(change):
    draw_plot(save=False)

def save_plot(button):
    draw_plot(save=True)

plant_dropdown.observe(update_plot, names="value")
year_range.observe(update_plot, names="value")
save_button.on_click(save_plot)

display(widgets.VBox([plant_dropdown, year_range, save_button, out]))

# initial plot
draw_plot()
