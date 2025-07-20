import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = os.path.join(os.path.dirname(__file__), '../tracking/sector_data/')

# Find all yfinance CSVs
csv_files = glob.glob(os.path.join(DATA_DIR, 'yfinance_*.csv'))

# Load and combine all data
frames = []
for file in csv_files:
    df = pd.read_csv(file)
    df['source_file'] = os.path.basename(file)
    frames.append(df)

if frames:
    all_data = pd.concat(frames, ignore_index=True)
    print('Loaded data from:', len(csv_files), 'files')
    print(all_data.head())

    # Example: plot last close prices for each ticker
    if 'Close' in all_data.columns:
        all_data['Ticker'] = all_data['source_file'].str.extract(r'yfinance_(.*?)_')
        last_prices = all_data.groupby('Ticker')['Close'].last()
        last_prices.plot(kind='bar', title='Latest Close Price per Ticker')
        plt.ylabel('Close Price (USD)')
        plt.show()
else:
    print('No yfinance CSV data found in', DATA_DIR)
