import requests
import re
from fetcher import fetch_fund_yield_json, get_year_end_scale_all_years
from parser import parse_yield_json_to_df
from fee_extractor import extract_fee_info
import json
import pandas as pd
import os
from tqdm import tqdm


def get_all_fund_codes():
    """
    从天天基金获取全部基金代码列表
    """
    url = "http://fund.eastmoney.com/js/fundcode_search.js"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        data = resp.text
    except Exception as e:
        print(f"基金代码列表获取失败: {e}")
        return []
    codes = re.findall(r'\["(\d{6})"', data)
    return codes


summary_data = []

if __name__ == '__main__':
    os.makedirs('output', exist_ok=True)

    FUND_CODES = get_all_fund_codes()
    print(f"共获取基金代码数量: {len(FUND_CODES)}")

    # 只跑前 500 个
    FUND_CODES = FUND_CODES[:500]
    print(f"本次遍历前 {len(FUND_CODES)} 个基金代码")

    for fund_code in tqdm(FUND_CODES, desc="Processing Funds"):
        try:
            # ====== 收益率 ======
            yield_path = fetch_fund_yield_json(fund_code)
            df = parse_yield_json_to_df(yield_path)
            yearly_data = {}
            for year in range(2015, 2025):
                date = pd.to_datetime(f"{year}-12-31")
                closest = df.index[df.index <= date].max() if not df.empty else None
                yearly_data[f"{year}_收益"] = (
                    df.loc[closest, 'yield'] if closest is not None and pd.notna(closest) else None
                )


            yearly_scale = get_year_end_scale_all_years(fund_code)
            for year in range(2015, 2025):
                yearly_data[f"{year}_规模"] = yearly_scale.get(str(year), None)


            fee_path = extract_fee_info(fund_code)
            with open(fee_path, 'r') as f:
                fee = json.load(f)

            summary_data.append({
                '基金代码': fund_code,
                '基金类型': fee.get("基金类型"),
                '管理费率': fee.get("管理费率"),
                '托管费率': fee.get("托管费率"),
                '最新资产规模': fee.get("最新资产规模"),
                '披露日': fee.get("披露日") or "缺失",
                **yearly_data
            })

        except Exception as e:
            print(f"基金 {fund_code} 处理失败: {e}")

    df_summary = pd.DataFrame(summary_data)
    df_summary.to_csv('output/fund_summary_full.csv', index=False, encoding='utf-8-sig')
    print("\n📄 已保存至 output/fund_summary_full.csv")
