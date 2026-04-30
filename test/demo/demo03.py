import pandas as pd
import json

# 原始数据
data = {
    'product_url': 'https://www.amazon.com/BABESIDE-Realistic-Accessories-Pretend-Collection/dp/B0CY4X37RD/...',
    'title': 'BABESIDE Baby Dolls, 17inch Large Realistic Cute Soft Body Baby Doll Real Life Baby Dolls with Accessories for 3+ Year Old Girls Gifts, Pretend Play, Collection',
    'asin': 'B0CY4X37RD',
    'price': '$23.98',
    'rating': '4.6',
    'review_count': '(4,080)',
    'category_path': '',
    'category_name': '',
    'department': '',
    'subcategory': '',
    'attributes': {},
    'bullet_points': [
        'More Life-like Realism: ...',
        'Irresistibly Cute and Soft: ...',
        'Inspiring Imagination and Play: ...',
        'Exciting Accessories for Interactive Fun: ...',
        'Perfect Gift for Every Occasion: ...'
    ],
    'description': "More Life-like Realism: ...",
    'reviews': [],
    'product_more_datas': {
        '基础信息': {'产品名称': 'BABESIDE Baby Dolls...', '当前价格': '$23.98', 'ASIN': 'B0CY4X37RD',
                     '品牌': 'BABESIDE'},
        '物理规格': {'尺寸': '17\\"L x 7\\"W x 5\\"H', '大小': '17 inches', '单位数量': '1.0 Count',
                     '是否需要组装': 'No'},
        '外观与设计': {'动物主题': 'Unicorn', '色彩': 'A Pink', '主题': 'Fantasy', '风格': 'Modern',
                       '适合场景': 'Baby Shower...'},
        '制造信息': {'厂商型号': 'RSG004NIWA-YJ', '建议最小年龄': '36.0', '材质': 'Cotton, Vinyl',
                     '包含组件': 'doll & accessories'},
        '市场表现': {'评分': '4.6', '评论数': '(4,080)', '销售排名': '#1,578 in Toys & Games...'}
    }
}


def flatten_amazon_data(item):
    # 1. 复制一份基础数据，排除掉需要特殊处理的嵌套字典
    flat_item = {k: v for k, v in item.items() if
                 k not in ['product_more_datas', 'bullet_points', 'reviews', 'attributes']}

    # 2. 处理 bullet_points (列表转为换行字符串)
    if 'bullet_points' in item and isinstance(item['bullet_points'], list):
        flat_item['features'] = "\n".join(item['bullet_points'])

    # 3. 处理 product_more_datas (扁平化嵌套字典)
    if 'product_more_datas' in item:
        for category, details in item['product_more_datas'].items():
            for key, value in details.items():
                # 拼接列名，如：物理规格_尺寸
                column_name = f"{category}_{key}"
                # 处理转义的双引号 \" 还原为 "
                if isinstance(value, str):
                    value = value.replace('\\"', '"')
                flat_item[column_name] = value

    return flat_item


# --- 执行转换 ---
# 扁平化数据
processed_data = flatten_amazon_data(data)

# 转换为 DataFrame (传入列表，因为是一个产品)
df = pd.DataFrame([processed_data])

# --- 导出到 Excel ---
file_name = "amazon_product_details.xlsx"
try:
    # index=False 不保存行索引
    df.to_excel(file_name, index=False, engine='openpyxl')
    print(f"成功导出到: {file_name}")
except Exception as e:
    print(f"导出失败: {e}")