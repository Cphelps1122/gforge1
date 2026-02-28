from utils.formatting import money

def prepare_map_data(df):
    df_map = df.copy()
    df_map["Formatted Cost"] = df_map["$ Amount"].apply(money)
    return df_map
