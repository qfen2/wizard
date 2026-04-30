"""
亚马逊产品爬虫 - Playwright版本
功能：搜索产品列表 + 获取详情
"""
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os

# ============ 配置区 ============
KEYWORD = "hardware tools"          # 搜索关键词
MAX_LIST = 50                       # 列表数量
GET_DETAIL_COUNT = 10               # 获取详情的数量
OUTPUT_FILE = r"C:\Users\liukk\Desktop\amazon_products.xlsx"
# ================================

async def extract_list(page):
    """提取搜索结果列表"""
    await page.wait_for_selector('[data-component-type="s-search-results"]', timeout=10000)

    js_code = """
    () => {
        const products = [];
        const items = document.querySelectorAll('[data-component-type="s-search-results"] .s-result-item');
        items.forEach((item) => {
            try {
                const asin = item.getAttribute('data-asin') || '';
                const titleEl = item.querySelector('h2 a span, .a-text-normal');
                const title = titleEl ? titleEl.textContent.trim() : '';
                const imgEl = item.querySelector('img.s-image');
                const image = imgEl ? imgEl.src : '';
                const priceWhole = item.querySelector('.a-price-whole');
                const priceFraction = item.querySelector('.a-price-fraction');
                let price = '';
                if (priceWhole) {
                    price = '$' + priceWhole.textContent.replace(/,/g, '');
                    if (priceFraction) price += '.' + priceFraction.textContent;
                }
                const ratingEl = item.querySelector('.a-icon-alt');
                const rating = ratingEl ? ratingEl.textContent.replace(' out of 5 stars', '') : '';
                const reviewsEl = item.querySelector('.s-underline-text');
                const reviews = reviewsEl ? reviewsEl.textContent : '';
                if (asin && title) {
                    products.push({
                        asin,
                        title: title.substring(0, 200),
                        image: image.split('._AC_')[0] + '._AC_SY400_.jpg',
                        price: price || 'N/A',
                        rating: rating || 'N/A',
                        reviews: reviews || '0'
                    });
                }
            } catch (e) {}
        });
        return products;
    }
    """
    return await page.evaluate(js_code)

async def extract_detail(page):
    """提取产品详情页"""
    js_code = """
    () => {
        const data = {
            title: '', price: '', rating: '', reviews: '',
            mainImage: '', images: [], bullets: [], specs: {}, seller: ''
        };

        const titleEl = document.querySelector('#productTitle');
        data.title = titleEl ? titleEl.textContent.trim() : '';

        const priceEl = document.querySelector('.a-price .a-offscreen');
        data.price = priceEl ? priceEl.textContent : '';

        const ratingEl = document.querySelector('#acrPopover .a-icon-alt');
        data.rating = ratingEl ? ratingEl.textContent.replace(' out of 5 stars', '') : '';

        const reviewsEl = document.querySelector('#acrCustomerReviewText');
        data.reviews = reviewsEl ? reviewsEl.textContent : '';

        const mainImg = document.querySelector('#landingImage, #imgBlkFront');
        data.mainImage = mainImg ? mainImg.src : '';

        const thumbs = document.querySelectorAll('#thumbnails li.item img, #altImages li img');
        data.images = Array.from(thumbs).slice(0, 10).map(img =>
            (img.src || img.getAttribute('data-old-hires') || '')
        ).filter(s => s);

        const bulletItems = document.querySelectorAll('#feature-bullets li.a-unordered-list-item');
        data.bullets = Array.from(bulletItems).map(li => li.textContent.trim()).filter(t => t);

        const specRows = document.querySelectorAll('#productDetails_techSpec_section_1 tr');
        specRows.forEach(row => {
            const key = row.querySelector('th');
            const val = row.querySelector('td');
            if (key && val) data.specs[key.textContent.trim()] = val.textContent.trim();
        });

        const sellerEl = document.querySelector('#sellerProfileTriggerId');
        data.seller = sellerEl ? sellerEl.textContent.trim() : '';

        return data;
    }
    """
    return await page.evaluate(js_code)

async def main():
    print("=" * 50)
    print(f"亚马逊产品爬虫 - 关键词: {KEYWORD}")
    print("=" * 50)

    all_products = []

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # -------- 获取产品列表 --------
        print(f"\n[1/2] 搜索产品: {KEYWORD}")

        page_num = 1
        while len(all_products) < MAX_LIST:
            url = f"https://www.amazon.com/s?k={KEYWORD}&page={page_num}"
            print(f"  正在获取第 {page_num} 页...")

            try:
                await page.goto(url, timeout=30000, wait_until='networkidle')
                products = await extract_list(page)

                if not products:
                    print("  没有更多产品")
                    break

                for p in products:
                    if len(all_products) >= MAX_LIST:
                        break
                    p['排名'] = len(all_products) + 1
                    all_products.append(p)

                print(f"  本页获取 {len(products)} 个，累计 {len(all_products)} 个")
                page_num += 1
                await asyncio.sleep(2)  # 延时

            except Exception as e:
                print(f"  获取失败: {e}")
                break

        # -------- 获取产品详情 --------
        detail_count = min(GET_DETAIL_COUNT, len(all_products))
        print(f"\n[2/2] 获取前 {detail_count} 个产品详情...")

        for i, prod in enumerate(all_products[:detail_count]):
            try:
                print(f"  [{i+1}/{detail_count}] {prod['title'][:40]}...")

                await page.goto(f"https://www.amazon.com/dp/{prod['asin']}",
                               timeout=20000, wait_until='networkidle')

                detail = await extract_detail(page)

                prod['五点描述'] = ' | '.join(detail['bullets'][:5])
                prod['规格'] = '; '.join([f"{k}: {v}" for k, v in list(detail['specs'].items())[:10]])
                prod['主图'] = detail['mainImage']
                prod['图片列表'] = ', '.join(detail['images'][:5])
                prod['卖家'] = detail['seller']

                await asyncio.sleep(1.5)

            except Exception as e:
                print(f"    获取详情失败: {e}")

        await browser.close()

    # -------- 保存Excel --------
    if all_products:
        # 确保列顺序
        columns = ['排名', 'ASIN', '标题', '价格', '评分', '评论数',
                   '五点描述', '规格', '主图', '图片列表', '卖家']
        for col in columns:
            for p in all_products:
                if col not in p:
                    p[col] = ''

        df = pd.DataFrame(all_products)[columns]
        df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')

        print(f"\n完成！已保存到: {OUTPUT_FILE}")
        print(f"共 {len(all_products)} 个产品")
    else:
        print("\n没有获取到任何产品")

if __name__ == "__main__":
    asyncio.run(main())