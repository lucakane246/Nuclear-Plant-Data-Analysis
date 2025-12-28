U.S. Nuclear Plant Capacity Factor Data Analysis (2021–2024)
I. Overview
This project analyzes performance of U.S. nuclear power plants from 2021-2024 by calculating plant-level capacity factors using publicly available data from the U.S. Energy Information Administration. Monthly net electricity generation data are added with plant capacity ratings to evaluate how consistently each plant operated relative to its maximum potential output.
This analysis produces month-month plotting and multi-year plant rankings based on average capacity factor.
Data Sources:
The project uses two EIA datasets,
1. EIA-923: Monthly net electricity generation by plant and fuel type. Net generation represents the amount of electricity delivered to the grid after plant consumption.
2. EIA-860: Generator and plant characteristics, including net summer capacity. Net summer capacity represents the maximum power output a plant can reliably achieve under peak summer conditions, when cooling is most cost inefficient.
Data files are included in the zip file “CSVs.zip”, compressed for performance.

II. Methods
Monthly net generation data from EIA-923 was filtered to include only nuclear plant data, instead of all forms of used commercial electricity production. Generation values are resized to the plant level and reshaped into a long, time-series format.
Plant capacity data from EIA-860 are resized to the plant level using net summer capacity. Monthly maximum possible generation is calculated by multiplying net summer capacity by the number of hours in each month, with an additional day applied for February 2024, due to the leap year.
Capacity factor is calculated as the ratio of actual net generation to maximum possible generation. Unreasonable values from reporting conventions (unbounded) or extended outages (0) are filtered, and final capacity factors are forced between zero and one for clarity.
Annual capacity factors are computed using the ratio of total annual generation to total annual maximum possible generation. Multi-year plant rankings are based on the average annual capacity factor over the study period.

Capacity Factor=(Actual Net Generation/Output)/(Maximum Possible Generation/Output)
Equation 1.
III. Results
The analysis produces the following outputs:
1. A CSV file containing plant-level average capacity factors across 2021–2024.
2. A time-series plot illustrates monthly capacity factor trends for a selected plant.
These outputs summarize both short-term operational variability and long-term plant performance, as well as recent historical performance and information.

IV. How to Run
The analysis is implemented in Python using pandas and matplotlib. Running the Jupyter notebook from top to bottom reproduces all results.
Required packages are listed in requirements.txt, as well as the CSVs.zip file. 
After running data, use dropdown and slider with the plot produced to vary it for different data. “Save Button” feature allows saving to the “Outputs” folder.

