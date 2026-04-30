import requests

# URL
url = "http://tajy.fdcyun.com:90/Cbgl/HTFK/Pay_PayDetailByHTFKApply_Grid.aspx"

# 请求参数
params = {
    "mode": "2",
    "oid": "3cd56ce7-9305-f111-80c5-c7fdeab6be74",
    "ContractGUID": "4212d5d1-0bc0-ee11-80c4-b1fe5a19d94c",
    "IsFyControl": "0",
    # "PayState": "完全支付",
    "funcid": "02010408"
}

# 请求头（可选，模拟浏览器访问）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    'Cookie': 'keeplastname=18318036926; mycrm_isendcompany=1; mycrm_company=b14e0295-ce0b-ec11-80c0-ae2d6a9e3b11; ASP.NET_SessionId=bvebog55usbsd4bnzw00d02c; _NavToFunction=0201,; ck_login_out=91ceb967-82eb-eb11-80c0-ae2d6a9e3b11; userToken=FAC04D2A2668018774188FA746B0CC33ABD0D3BF42B7BFAAE09B5DC646C4A41097EE635431FA21F07FDEEAA0A8DF7F7414E2AC94DCF35C2B0DDF06011DCF5224ECDD9B7B37DD0E39A69D0AF0C8E83A351923A6B4C9864DC7916831B1BF38C6A2DC83B58088DE1D4C328208836C0625827246E7E974C86DF4777B586EC6797F283E4D7855575F67D25BC2C0AAFF51B49844C52B66882D9E3523A96DC51EDB4627B85568B660BF3FFAD7EE6512AF08C02CF65CB3F0AC9C594BFB640806080E0FC72141ED7FF361F453AAD50EE64DCCB9589484E274F32D3AF42655546D9E62CF1AD68622025610DD652F5F03925346E732BCDA4BA9D5170C7326F7EF63E5DBE0316F0D31CF4203A4558E2CC66B32C9ECCE577429C94AFF0D76C50DF1FC40FDACFDFED1EC7C665261EFF0D14AE46C124DBCC2A8BBB04258C98C9677F665963637FE388BB1A4BB4286B019AE349436A581A6A10AAAC664726435F31A35FD60967CBDB6388F68F8C775397065C8BB8D12F136DA1C5F4446FE536D94809A18327664952BB3A43C; _m6_prelogin=c=eyJTaXRlIjoiaHR0cDovL3RhankuZmRjeXVuLmNvbTo4MCIsIlVzZXIiOiIxODMxODAzNjkyNiIsIkxvZ291dFVybCI6Ii9QdWJQbGF0Zm9ybS9OYXYvTG9naW4vTG9nb3V0LmFzcHgiLCJUaW1lb3V0IjozMDB9&t=1776157810&v=5BA67AB6A521F726'
}

try:
    # 发送 GET 请求
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()

    # 设置编码（根据返回内容自动检测或手动设置）
    response.encoding = response.apparent_encoding  # 或 'utf-8'

    print("状态码:", response.status_code)
    print("=" * 50)
    print("返回内容:")
    print(response.text)

    # 如果返回的是 JSON 格式，可以使用 response.json() 解析
    # 如果返回的是 HTML/XML，可以使用 BeautifulSoup 或正则表达式解析

except requests.exceptions.Timeout:
    print("请求超时，请检查网络连接")
except requests.exceptions.ConnectionError:
    print("连接错误，无法访问服务器")
except requests.exceptions.HTTPError as e:
    print(f"HTTP 错误: {e}")
except requests.exceptions.RequestException as e:
    print(f"请求出错: {e}")