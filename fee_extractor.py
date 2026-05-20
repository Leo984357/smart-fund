import requests
from lxml import html
import json
import os
import re

def extract_fee_info(fund_code: str, save_dir: str = 'cache') -> str:
    os.makedirs(save_dir, exist_ok=True)
    url = f"http://fundf10.eastmoney.com/jbgk_{fund_code}.html"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
    except Exception as e:
        print(f"基金 {fund_code} 费用信息请求失败: {e}")
        return None

    tree = html.fromstring(resp.text)
    info_text = tree.xpath('//table[@class="info w790"]//text()')
    text = ''.join([t.strip() for t in info_text if t.strip()])

    def extract(pattern):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    result = {
        '管理费率': extract(r'管理费率[:：]?\s*([\d\.]+%（每年）)'),
        '托管费率': extract(r'托管费率[:：]?\s*([\d\.]+%（每年）)'),
        '基金类型': extract(r'基金类型[:：]?\s*([^\d：，]+)'),
        '最新资产规模': extract(r'资产规模[:：]?\s*([\d\.]+亿元)'),
        '披露日': extract(r'截止至[:：]?\s*(\d{4}-\d{2}-\d{2})')
    }

    file_path = os.path.join(save_dir, f"{fund_code}_费用信息.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return file_path
