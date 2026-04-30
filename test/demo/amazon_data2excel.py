# 使用提醒:
# 1. xbot包提供软件自动化、数据表格、Excel、日志、AI等功能
# 2. package包提供访问当前应用数据的功能，如获取元素、访问全局变量、获取资源文件等功能
# 3. 当此模块作为流程独立运行时执行main函数
# 4. 可视化流程中可以通过"调用模块"的指令使用此模块

import xbot
import re
import os
import requests
from xbot import print, sleep
from . import package
from typing import List, Dict, Optional
import pandas as pd

from .package import variables as glv
from bs4 import BeautifulSoup
from PIL import Image  # 用于获取图片真实尺寸


class AmazonExcelBot:
    def __init__(self, output_path="Amazon_Data_Master.xlsx"):
        self.output_path = os.path.abspath(output_path)
        self.row_height_pt = 130
        self.img_width_col = 25

    def _get_image_scale(self, img_path):
        """动态计算缩放比例，确保图片不超出单元格"""
        try:
            if not img_path or not os.path.exists(img_path): return 0.1
            with Image.open(img_path) as img:
                width, height = img.size
            target_height_px = self.row_height_pt * 1.3  # pt转px
            scale = (target_height_px * 0.9) / height
            return scale
        except:
            return 0.1

    def _format_more_data(self, more_data):
        if not more_data or not isinstance(more_data, dict): return ""
        if isinstance(more_data, str): return more_data  # 如果是读取回来的旧数据，已经是字符串了

        lines = []
        for group_name, details in more_data.items():
            if isinstance(details, dict):
                for k, v in details.items():
                    lines.append(f"• {k}: {v}")
            else:
                lines.append(f"• {group_name}: {details}")
        return "\n".join(lines)

    def _flatten(self, item):
        """将原始字典转换为扁平行"""
        # 如果已经是清洗过的数据(读取旧文件得到的)，直接返回
        if '_all_local_paths' in item: return item

        all_paths = [img.get('本地路径') for img in item.get('product_imgs_data', []) if img.get('本地路径')]
        # 将路径列表转为字符串存储，方便在Excel中存取，中间用逗号隔开
        paths_str = ",".join(all_paths)

        return {
            'ASIN': item.get('asin'),
            '产品标题': item.get('title'),
            '单价': item.get('price'),
            '评分情况': f"{item.get('rating', 'N/A')} ({item.get('review_count', '0')})",
            '五点描述': "\n".join(item.get('bullet_points', [])),
            '详细参数': self._format_more_data(item.get('product_more_datas', {})),
            '购买链接': item.get('product_url'),
            '_all_local_paths': paths_str  # 隐藏列：存储所有图片路径
        }

    def save(self, new_raw_data):
        """
        保存数据，如果文件存在则追加
        """
        # 1. 处理新数据
        new_df = pd.DataFrame([self._flatten(i) for i in new_raw_data])

        # 2. 读取旧数据并合并
        if os.path.exists(self.output_path):
            try:
                old_df = pd.read_excel(self.output_path, engine='openpyxl')
                # 合并旧数据和新数据
                combined_df = pd.concat([old_df, new_df], ignore_index=True)
                # 根据 ASIN 去重，保留最后一次出现的数据
                combined_df.drop_duplicates(subset=['ASIN'], keep='last', inplace=True)
                df = combined_df
                print(f"检测到旧数据，合并后共 {len(df)} 条记录")
            except Exception as e:
                print(f"读取旧文件失败，将创建新文件。错误: {e}")
                df = new_df
        else:
            df = new_df

        # 计算最大图片列数
        # 将路径字符串转回列表来计算长度
        path_series = df['_all_local_paths'].fillna("").set_axis(range(len(df)))
        max_imgs = max([len(str(p).split(',')) if p else 0 for p in path_series])

        # 3. 重新写入 Excel
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        try:
            with pd.ExcelWriter(self.output_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Amazon产品库', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Amazon产品库']

                # 样式
                body_fmt = workbook.add_format(
                    {'valign': 'top', 'text_wrap': True, 'font_size': 9, 'border': 1, 'border_color': '#EEEEEE'})
                header_fmt = workbook.add_format(
                    {'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

                # 设置基本列格式
                worksheet.set_column('A:A', 15, body_fmt)
                worksheet.set_column('B:B', 30, body_fmt)
                worksheet.set_column('C:D', 12, body_fmt)
                worksheet.set_column('E:F', 40, body_fmt)
                worksheet.set_column('G:G', 15, body_fmt)

                # 隐藏路径存储列 (关键：如果不隐藏，Excel会很难看)
                path_col_idx = df.columns.get_loc('_all_local_paths')
                worksheet.set_column(path_col_idx, path_col_idx, None, None, {'hidden': True})

                # 动态生成图片表头
                start_img_col = len(df.columns)
                for j in range(max_imgs):
                    col_idx = start_img_col + j
                    worksheet.write(0, col_idx, f"图片 {j + 1}", header_fmt)
                    worksheet.set_column(col_idx, col_idx, self.img_width_col, body_fmt)

                # 重新遍历每一行，插入图片
                for i, row in df.iterrows():
                    ex_row = i + 1
                    worksheet.set_row(ex_row, self.row_height_pt)

                    # 将路径字符串拆分为列表
                    paths = str(row['_all_local_paths']).split(',') if row['_all_local_paths'] else []
                    for img_idx, p in enumerate(paths):
                        p = p.strip()
                        if p and os.path.exists(p):
                            scale = self._get_image_scale(p)
                            worksheet.insert_image(ex_row, start_img_col + img_idx, p, {
                                'x_scale': scale, 'y_scale': scale,
                                'x_offset': 5, 'y_offset': 5,
                                'object_position': 1
                            })

                worksheet.freeze_panes(1, 0)
                worksheet.hide_gridlines(2)

            print(f"数据追加成功！当前总行数: {len(df)}")
            return self.output_path
        except Exception as e:
            print(f"写入失败: {e}")


def extract_product_details(html_content, product_url):
    """
    提取商品详情信息

    Args:
        product_url: 商品详情页URL

    Returns:
        包含商品信息的字典
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    product_data = {
        'product_url': product_url,
        'product_imgs_url': [],
        'title': '',
        'asin': '',
        'price': '',
        'rating': '',
        'review_count': '',
        'category_path': '',  # 完整类目路径
        'category_name': '',  # 当前类目名称
        'department': '',  # 部门/大类
        'subcategory': '',  # 子类目
        'attributes': {},
        'bullet_points': [],
        'description': '',
        'reviews': []
    }

    try:
        # 提取标题
        title_element = soup.find('span', {'id': 'productTitle'})
        if title_element:
            product_data['title'] = title_element.get_text(strip=True)

        # 提取ASIN
        asin_element = soup.find('input', {'id': 'ASIN'})
        if asin_element:
            product_data['asin'] = asin_element.get('value', '')
        else:
            # 从URL中提取ASIN
            if '/dp/' in product_url:
                product_data['asin'] = product_url.split('/dp/')[1].split('/')[0]

        # 提取价格
        price_element = soup.find('span', {'id': 'tp_price_block_total_price_ww'}).find('span',
                                                                                        {'class': 'a-offscreen'})
        if price_element:
            product_data['price'] = price_element.get_text(strip=True)

        # 提取评分
        rating_element = soup.find('span', {'class': 'a-icon-alt'})
        if rating_element:
            rating_text = rating_element.get_text(strip=True)
            if 'out of 5 stars' in rating_text:
                product_data['rating'] = rating_text.split(' out of')[0]

        # 提取评论数
        review_count_element = soup.find('span', {'id': 'acrCustomerReviewText'})
        if review_count_element:
            product_data['review_count'] = review_count_element.get_text(strip=True)

        # 提取商品图片链接
        ul = soup.find('ul', class_='desktop-media-mainView')
        image_data = []
        img_dir = "amazon_images"
        if ul:
            # 2. 找到所有 li 标签
            lis = ul.find_all('li', {'data-csa-c-media-type': 'IMAGE'})
            print('图片长度', len(lis))
            for idx, li in enumerate(lis):
                # 优先寻找 data-old-hires 属性
                img_div = li.find('div', {'class': 'imgTagWrapper'})
                img_tag = img_div.find('img') or img_div.find('div')
                high_res = img_tag.get('data-old-hires')

                if not high_res and img_tag:
                    high_res = img_tag.get('src')

                print(f"{product_data['asin']}: high_res", high_res)
                if high_res:
                    # 3. 通过正则提取原图 URL
                    # 亚马逊原图通常是把 ._AC_... 部分去掉
                    original_url = re.sub(r'\._AC_.*?\.', '.', high_res)
                    original_url = re.sub(r'\._SX\d+_', '', original_url)
                    original_url = re.sub(r'\._SY\d+_', '', original_url)

                    # 下载图片
                    if not os.path.exists(os.path.join(img_dir)):
                        os.mkdir(os.path.join(img_dir))

                    img_name = f"{product_data['asin']}_image_{idx}.jpg"
                    img_path = os.path.join(img_dir, img_name)
                    try:
                        response = requests.get(original_url, proxies={"http": None, "https": None}, timeout=10)
                        if response.status_code == 200:
                            with open(img_path, 'wb') as f:
                                f.write(response.content)
                            image_data.append({
                                "文件名": img_name,
                                "本地路径": img_path,
                                "原始链接": original_url
                            })
                    except Exception as e:
                        print(f"下载失败: {original_url}, 错误: {e}")

            product_data['product_imgs_data'] = image_data

        print(image_data)
        # 打印结果
        for img in list(image_data):  # 去重
            print('img: ', img)

        # 提取商品属性
        product_features = soup.find('div', {'id': 'twister-plus-inline-twister-card'}) or soup.find('div', {
            'id': 'inline-twister-dim-title-style_name'})
        specs = {}

        if product_features:
            # 查找所有li标签
            items = product_features.find_all('li', role='listitem')

            for item in items:
                # 获取标签名（在第一个div的span中）
                label_div = item.find('div', class_='a-column a-span5')
                if label_div:
                    label = label_div.get_text(strip=True)

                    # 获取值（在第二个div中）
                    value_div = item.find('div', class_='a-column a-span7 a-span-last')
                    if value_div:
                        # 值可能在span或a标签中
                        value_span = value_div.find('span', class_='a-size-base')
                        if value_span:
                            value = value_span.get_text(strip=True)
                        else:
                            # 如果有链接的情况
                            value = value_div.get_text(strip=True)

                        specs[label] = value
            product_data['attributes'] = specs

        # 提取五点描述
        bullet_points_container = soup.find('div', {'id': 'feature-bullets'})
        if bullet_points_container:
            bullet_points = bullet_points_container.find_all('span', {'class': 'a-list-item'})
            for bp in bullet_points:
                text = bp.get_text(strip=True)
                if text and not text.startswith('Next'):
                    product_data['bullet_points'].append(text)

        # 提取长描述
        description_element = soup.find('div', {'id': 'feature-bullets'})
        if description_element:
            paragraphs = description_element.find_all('p')
            if paragraphs:
                product_data['description'] = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            else:
                product_data['description'] = description_element.get_text(strip=True)

        # 提取产品详情
        product_detail_element = soup.find('div', {'id': 'productDetails_feature_div'})
        product_more_datas = extract_product_more(product_detail_element)
        product_data['product_more_datas'] = product_more_datas

        # 提取评论
        # product_data['reviews'] = self.extract_reviews(product_url)

    except Exception as e:
        raise Exception("解析报错了")

    return product_data


def data2excel(datas: list):
    pass


def extract_product_more(html_element):
    data = {}
    # 1. 提取隐藏的元数据 (标题、价格、ASIN等)
    hidden_inputs = html_element.find_all('input', type='hidden')
    meta_info = {}
    for inp in hidden_inputs:
        if inp.get('id'):
            meta_info[inp.get('id')] = inp.get('value')

    data['基础信息'] = {
        '产品名称': meta_info.get('productTitle'),
        '当前价格': f"{meta_info.get('priceSymbol')}{meta_info.get('priceValue')}",
        'ASIN': meta_info.get('asin'),
        '品牌': "BABESIDE"
    }

    # 2. 提取所有表格数据并分类
    tables = html_element.find_all('table', class_='prodDetTable')

    def parse_table(table):
        results = {}
        rows = table.find_all('tr')
        for row in rows:
            header = row.find('th')
            value = row.find('td')
            if header and value:
                key = header.get_text(strip=True)
                val = value.get_text(strip=True)
                if key:
                    results[key] = val
        return results

    # 遍历所有表格进行分类
    all_specs = {}
    for table in tables:
        all_specs.update(parse_table(table))

    # 3. 数据分类整理
    data['物理规格'] = {
        '尺寸': all_specs.get('Item Dimensions L x W x H'),
        '大小': all_specs.get('Size'),
        '单位数量': all_specs.get('Unit Count'),
        '是否需要组装': all_specs.get('Is Assembly Required')
    }

    data['外观与设计'] = {
        '动物主题': all_specs.get('Animal Theme'),
        '色彩': all_specs.get('Color'),
        '主题': all_specs.get('Theme'),
        '风格': all_specs.get('Style'),
        '适合场景': all_specs.get('Occasion')
    }

    data['制造信息'] = {
        '厂商型号': all_specs.get('Model Number'),
        '建议最小年龄': all_specs.get('Manufacturer Minimum Age (MONTHS)'),
        '材质': all_specs.get('Material Type'),
        '包含组件': all_specs.get('Included Components')
    }

    data['市场表现'] = {
        '评分': html_element.find('span', class_='a-size-small a-color-base').get_text(strip=True) if html_element.find(
            'span', class_='a-size-small a-color-base') else "4.6",
        '评论数': html_element.find('span', id='acrCustomerReviewText').get_text(strip=True) if html_element.find(
            'span', id='acrCustomerReviewText') else "",
        '销售排名': all_specs.get('Best Sellers Rank')
    }
    return data


def main(args):
    html_content = xbot.web.get_active(mode="chrome").get_html()
    # 2. 初始化结果列表
    result_data = []

    soup = BeautifulSoup(html_content, 'html.parser')

    # 4. 根据你提供的 HTML 特征查找所有商品链接
    # 目标标签是 <a>，类名包含 's-line-clamp-4' 和 's-link-style'
    # 这里使用 CSS 选择器进行模糊匹配，确保能抓全
    links = soup.select('a.s-line-clamp-4.s-link-style.a-text-normal')
    # 5. 遍历提取数据
    num = 1
    for link in links:
        # 注意：亚马逊的 href 通常是相对路径（如 /dp/xxx），需要拼接域名
        href = link.get('href', '')
        if href.startswith('/'):
            url = 'https://www.amazon.com' + href
        else:
            url = href

        if num > 3:
            break
        num += 1

        detail_page = xbot.web.create(url, mode="chrome")
        detail_html_content = detail_page.get_html()
        product_data = extract_product_details(detail_html_content, url)
        result_data.append(product_data)
        # detail_page.close()
        sleep(0.5)

    desktop_file = os.path.join(os.path.expanduser("~"), "Desktop", "Amazon_Data.xlsx")
    bot = AmazonExcelBot(desktop_file)
    bot.save(result_data)
