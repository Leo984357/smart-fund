import pandas as pd

def parse_yield_json_to_df(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_json(file_path)
        if 'date' not in df.columns or 'yield' not in df.columns:
            print(f"收益率文件结构异常: {file_path}")
            return pd.DataFrame()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"收益率解析失败: {file_path}, 错误: {e}")
        return pd.DataFrame()
