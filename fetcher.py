import requests
import os
import json
import re
import pandas as pd
from lxml import html

def fetch_fund_yield_json(fund_code: str, save_dir: str = 'cache') -> str:
    """
    抓取天天基金全历史净值数据并计算累计收益率
    """
    os.makedirs(save_dir, exist_ok=True)
    url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        js_text = resp.text
    except Exception as e:
        print(f"基金 {fund_code} 历史净值请求失败: {e}")
        return None

    match = re.search(r"var Data_netWorthTrend\s*=\s*(\[\{.*?\}\]);", js_text, re.S)
    if not match:
        print(f"基金 {fund_code} 历史净值数据未找到")
        return None

    try:
        data_json = json.loads(match.group(1))
    except Exception as e:
        print(f"基金 {fund_code} 历史净值解析失败: {e}")
        return None

    df = pd.DataFrame(data_json)
    df['date'] = pd.to_datetime(df['x'], unit='ms')
    df['value'] = df['y']
    df['yield'] = (df['value'] / df['value'].iloc[0] - 1) * 100

    save_path = os.path.join(save_dir, f"{fund_code}_收益率.json")
    df[['date', 'yield']].to_json(save_path, orient='records', force_ascii=False)
    return save_path


def get_year_end_scale_all_years(fund_code: str) -> dict:
    """
    抓取2015-2024历年末资产规模，自动识别规模变动表格
    """
    url = f"http://fundf10.eastmoney.com/gmbd_{fund_code}.html"
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 初始化所有年份为 None
    year_scale = {str(y): None for y in range(2015, 2025)}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        tree = html.fromstring(resp.text)
    except Exception as e:
        print(f"基金 {fund_code} 历史规模请求失败: {e}")
        return year_scale

    # 遍历页面中所有表格，尝试找到包含日期和规模的表
    tables = tree.xpath('//table')
    for table in tables:
        rows = table.xpath('.//tr')
        for row in rows:
            cols = [c.text_content().strip() for c in row.xpath('./td')]
            if len(cols) >= 2:
                date_text = cols[0]
                scale_text = cols[1]
                # 判断是否是有效日期和规模
                if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                    year = date_text.split('-')[0]
                    if year.isdigit() and 2015 <= int(year) <= 2024:
                        try:
                            scale_value = float(re.findall(r"[\d\.]+", scale_text)[0])
                            year_scale[year] = scale_value
                        except:
                            year_scale[year] = None
    return year_scale
