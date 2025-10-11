import pandas as pd

def read_csv_file(file_path)-> pd.DataFrame:
    with open(file_path, 'r') as file:
        df = pd.read_csv(file)
        if df.empty:
            raise ValueError("The CSV file is empty.")
        return df