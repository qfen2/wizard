import pandas as pd
import os
from PIL import Image


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

# --- 影刀执行入口 ---
if __name__ == "__main__":
    # 模拟数据
    test_data = [{
                     'product_url': 'https://www.amazon.com/sspa/click?ie=UTF8&spc=MTo3OTIxOTc2NjgwNjcwMDk4OjE3NzczNzIyMjI6c3BfYXRmOjIwMDA3OTgzNjgwMzM3MTo6MDo6&url=%2FBarbie-2-Seater-Convertible-Sundress-Sunglasses%2Fdp%2FB015CCR6UC%2Fref%3Dsr_1_1_sspa%3Fcrid%3D3RAQJAJBZKS3O%26dib%3DeyJ2IjoiMSJ9.W5i03qIegSFoDjEH88lLUjYSZ-HIVL2K9vLnC-EUShsajXzRsexka_-Rg8DWYWELpVdUvtPR10NUEAK8jpc7LJP3YLWYhZ-y5XpssUX-2EzmhffEdDH1YN2ebPtikA3ehJlslox9Ny0__bLWpN0IrUOZnZzd5WU-f5lZykHxXGho32VqnZ4XpKKYx6RZQ0ID6z9hqw-gE_GcxbbsRCUfiS4UwY5DouWo2sC-xUOW-fYWnID6JPnKGI0NG2fAnVqcJf6IyK8p3K9reWu6d7K8pJCTsolTQ1VDCPgUjOr2jVw.iZnTQ0AD-n4CA4C-DwKG3blcCey1oXXFslhpVBL1LTo%26dib_tag%3Dse%26keywords%3Ddolls%26qid%3D1777372221%26sbo%3DRZvfv%252F%252FHxDF%252BO5021pAnSA%253D%253D%26sprefix%3Ddolls%252Caps%252C317%26sr%3D8-1-spons%26sp_csd%3Dd2lkZ2V0TmFtZT1zcF9hdGY%26psc%3D1',
                     'product_imgs_url': [],
                     'title': 'Barbie Playset with Sparkly Pink 2-Seater Toy Convertible Car Featuring Glam Details & Fashion Doll in Sundress & Sunglasses (Amazon Exclusive)',
                     'asin': 'B015CCR6UC', 'price': '$31.03', 'rating': '4.7', 'review_count': '(11,992)',
                     'category_path': '', 'category_name': '', 'department': '', 'subcategory': '', 'attributes': {},
                     'bullet_points': ['Hit the road in style with this super glam Barbie convertible car.',
                                       'Barbie doll is ready for anything dressed in a pink dress with graphic white print, strappy pink shoes and sunglasses perfect for a sunny drive.',
                                       'Her two-seater vehicle is designed in a sparkly pink with silvery accents.',
                                       'Realistic tires are ready to roll into adventure.',
                                       'Black interior seats feature seat belts for safety and Barbie “upholstery” labels for style.',
                                       'Hop in to drive into imagination and off into adventure because with Barbie, anything is possible!'],
                     'description': 'Hit the road in style with this super glam Barbie convertible car.Barbie doll is ready for anything dressed in a pink dress with graphic white print, strappy pink shoes and sunglasses perfect for a sunny drive.Her two-seater vehicle is designed in a sparkly pink with silvery accents.Realistic tires are ready to roll into adventure.Black interior seats feature seat belts for safety and Barbie “upholstery” labels for style.Hop in to drive into imagination and off into adventure because with Barbie, anything is possible!›See more product details',
                     'reviews': [], 'product_imgs_data': [
            {'文件名': 'B015CCR6UC_image_0.jpg', '本地路径': 'amazon_images\\B015CCR6UC_image_0.jpg',
             '原始链接': 'https://m.media-amazon.com/images/I/71nHAz-+VWL.jpg'},
            {'文件名': 'B015CCR6UC_image_1.jpg', '本地路径': 'amazon_images\\B015CCR6UC_image_1.jpg',
             '原始链接': 'https://m.media-amazon.com/images/I/71KNarWF7ML.jpg'},
            {'文件名': 'B015CCR6UC_image_2.jpg', '本地路径': 'amazon_images\\B015CCR6UC_image_2.jpg',
             '原始链接': 'https://m.media-amazon.com/images/I/71JM1X-L-wL.jpg'},
            {'文件名': 'B015CCR6UC_image_3.jpg', '本地路径': 'amazon_images\\B015CCR6UC_image_3.jpg',
             '原始链接': 'https://m.media-amazon.com/images/I/714NOoQ+DAL.jpg'},
            {'文件名': 'B015CCR6UC_image_4.jpg', '本地路径': 'amazon_images\\B015CCR6UC_image_4.jpg',
             '原始链接': 'https://m.media-amazon.com/images/I/716EKNLIfXL.jpg'},
            {'文件名': 'B015CCR6UC_image_5.jpg', '本地路径': 'amazon_images\\B015CCR6UC_image_5.jpg',
             '原始链接': 'https://m.media-amazon.com/images/I/71d3banTFpL.jpg'}], 'product_more_datas': {'基础信息': {
            '产品名称': 'Barbie Playset with Sparkly Pink 2-Seater Toy Convertible Car Featuring Glam Details &amp; Fashion Doll in Sundress &amp; Sunglasses (Amazon Exclusive)',
            '当前价格': '$31.03', 'ASIN': 'B015CCR6UC', '品牌': 'BABESIDE'}, '物理规格': {'尺寸': None,
                                                                                          '大小': 'One Size',
                                                                                          '单位数量': '1.0 Count',
                                                                                          '是否需要组装': 'Yes'},
                                                                                                         '外观与设计': {
                                                                                                             '动物主题': None,
                                                                                                             '色彩': 'Multicolor',
                                                                                                             '主题': 'Car, Fantasy, Vehicle',
                                                                                                             '风格': None,
                                                                                                             '适合场景': None},
                                                                                                         '制造信息': {
                                                                                                             '厂商型号': 'DJR55',
                                                                                                             '建议最小年龄': '36.0',
                                                                                                             '材质': 'Plastic',
                                                                                                             '包含组件': 'Includes Barbie doll wearing fashion and accessories, plus convertible car with details and styling.'},
                                                                                                         '市场表现': {
                                                                                                             '评分': '4.7',
                                                                                                             '评论数': '(11,992)',
                                                                                                             '销售排名': '#11,779 in Toys & Games (See Top 100 in Toys & Games)#6 inDoll Cars#39 inDoll Playsets'}}}]

    desktop_file = os.path.join(os.path.expanduser("~"), "Desktop", "Amazon_Data.xlsx")
    bot = AmazonExcelBot(desktop_file)
    bot.save(test_data)
