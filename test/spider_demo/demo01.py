import json
from typing import Optional

import requests
from bs4 import BeautifulSoup

import urllib.parse


# 付款申请
def fetch_grid_html(
        cookie: str,
) -> Optional[str]:
    """
    获取明源系统Grid数据（HTML格式）

    Args:
        cookie: 登录Cookie字符串
        page_num: 页码，默认1
        page_size: 每页条数，默认20
        sort_col: 排序字段，默认ApplyDate
        sort_dir: 排序方向，默认descend
        funcid: 功能ID，默认02010412
        xml_path: XML配置路径
        filter_value: 过滤条件
        custom_filter: 自定义过滤条件

    Returns:
        返回HTML字符串，失败返回None
    """

    base_url = "http://tajy.fdcyun.com:90/_grid/griddata.aspx"

    # 请求参数
    params = {
        "xml": "/Cbgl/HTFK/HTFKApply_Grid_ALL.xml",
        "gridId": "appGrid",
        "sortCol": "ApplyDate",
        "sortDir": "descend",
        "vScrollMode": "0",
        "multiSelect": "1",
        "selectByCheckBox": "1",
        "filter": "<filter type=\"and\"><condition attribute=\"Filter\" operator=\"TempValue\" value=\"fce4c068-e136-f111-80c5-c7fdeab6be74\"/></filter>",
        "customFilter": "<TempValue>:0debed30-e036-f111-80c5-c7fdeab6be74",
        "customFilter2": "",
        "dependencySQLFilter": "",
        "location": "",
        "cols": "",
        "pageNum": "1",
        "defaultSelected": "1",
        "pageSize": "100",
        "appName": "Default",
        "showPageCount": "1",
        "funcid": "02010412",
        "application": "",
        "cp": ""
    }

    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            print(f"请求成功，状态码: {response.status_code}")
            return response.text
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"请求异常: {e}")
        return None

def extract_with_structured_fields(html_content):
    # 假设html_content是你的HTML内容
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. 提取表格数据
    table = soup.find('table', id='gridBodyTable')
    rows = table.find_all('tr')

    data_list = []
    for row in rows:
        # 提取tr标签的所有属性（包括oid、ContractGUID等隐藏id）
        row_attrs = dict(row.attrs)

        # 提取每个单元格的数据
        cells = row.find_all('td')
        cell_data = []
        for cell in cells:
            # 获取单元格文本内容
            cell_text = cell.get_text(strip=True)
            # 获取单元格内的checkbox（如果有）
            checkbox = cell.find('input', type='checkbox')
            cell_info = {
                'text': cell_text,
                'has_checkbox': checkbox is not None,
                'checked': checkbox.get('checked') if checkbox else None
            }
            cell_data.append(cell_info)

        row_data = {
            'attributes': row_attrs,
            'cells': cell_data
        }
        data_list.append(row_data)

    # 2. 提取所有隐藏的input字段
    hidden_inputs = {}
    for inp in soup.find_all('input', type='hidden'):
        input_id = inp.get('id', '')
        input_name = inp.get('name', '')
        input_value = inp.get('value', '')

        key = input_id if input_id else input_name
        if key:
            hidden_inputs[key] = {
                'id': input_id,
                'name': input_name,
                'value': input_value
            }

    # 3. 提取表格属性信息
    table_attrs = {
        'pagenum': table.get('pagenum'),
        'pagecount': table.get('pagecount'),
        'pagesize': table.get('pagesize'),
        'rowcount': table.get('rowcount'),
        'loc': table.get('loc')
    }

    # 4. 提取所有重要的隐藏ID汇总
    all_hidden_ids = {
        'oids': [],
        'contract_guids': [],
        'htfk_plan_guids': [],
        'apply_type_guids': []
    }

    for row in rows:
        oid = row.get('oid')
        contract_guid = row.get('contractguid')
        htfk_plan_guid = row.get('htfkplanguid')
        apply_type_guid = row.get('applytypeguid')

        if oid:
            all_hidden_ids['oids'].append(oid)
        if contract_guid:
            all_hidden_ids['contract_guids'].append(contract_guid)
        if htfk_plan_guid:
            all_hidden_ids['htfk_plan_guids'].append(htfk_plan_guid)
        if apply_type_guid:
            all_hidden_ids['apply_type_guids'].append(apply_type_guid)

    # 5. 提取脚本中的关键变量
    scripts = soup.find_all('script')
    script_vars = {}
    for script in scripts:
        if script.string:
            # 提取__MYSESSIONSTATE值
            if '___MYSESSIONSTATE' in script.string:
                import re
                session_match = re.search(r"value='([^']+)'", script.string)
                if session_match:
                    script_vars['___MYSESSIONSTATE'] = session_match.group(1)

    # 6. 简化的表格数据提取（仅文本，便于查看）
    simple_table_data = []
    for row in rows:
        row_data = {
            '序号': None,
            '状态': None,
            '类型': None,
            '付款事由': None,
            '单据编号': None,
            '申请部门': None,
            '申请人': None,
            '合同名称': None,
            '申请日期': None,
            '申请金额': None,
            'oid': row.get('oid'),
            'ContractGUID': row.get('contractguid'),
            'HTFKPlanGUID': row.get('htfkplanguid'),
            'ProjType': row.get('projtype'),
            'OperationState': row.get('operationstate'),
            'ApplyState': row.get('applystate'),
            'ApplyAmount': row.get('applyamount'),
            'ApplyTypeGUID': row.get('applytypeguid')
        }

        cells = row.find_all('td')
        if len(cells) >= 11:
            row_data['序号'] = cells[1].get_text(strip=True)
            row_data['状态'] = cells[2].get_text(strip=True)
            row_data['类型'] = cells[3].get_text(strip=True)
            row_data['付款事由'] = cells[4].get_text(strip=True)
            row_data['单据编号'] = cells[5].get_text(strip=True)
            row_data['申请部门'] = cells[6].get_text(strip=True)
            row_data['申请人'] = cells[7].get_text(strip=True)
            row_data['合同名称'] = cells[8].get_text(strip=True)
            row_data['申请日期'] = cells[9].get_text(strip=True)
            row_data['申请金额'] = cells[10].get_text(strip=True)

        simple_table_data.append(row_data)

    # 输出结果
    result = {
        'table_attributes': table_attrs,
        'hidden_inputs': hidden_inputs,
        'all_hidden_ids': all_hidden_ids,
        'script_vars': script_vars,
        'row_count': len(rows),
        'table_data': simple_table_data,
        'detailed_data': data_list
    }

    # 打印或保存为JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如果需要单独导出某个部分：
    # 导出所有oid列表
    print("\n=== 所有OID ===")
    for oid in all_hidden_ids['oids']:
        print(oid)

    # 导出所有ContractGUID
    print("\n=== 所有ContractGUID ===")
    for guid in all_hidden_ids['contract_guids']:
        print(guid)


cookie = 'keeplastname=18318036926; mycrm_isendcompany=1; mycrm_company=b14e0295-ce0b-ec11-80c0-ae2d6a9e3b11; ASP.NET_SessionId=bvebog55usbsd4bnzw00d02c; _NavToFunction=0201,; userToken=F9C3C8F1C470276C16ADD683C894138D19454A4E9DB0BB00FE98B2C6BFC2DE5C1F3DB014AE06E2D16FDC73E52D8495568ACAD898806F86A7194499F4DB1DC4D5BC2A861545D256C4B7E412A5E3A46027FF3D4C3B5AF5C23EE686BD90C8BFD1138C6781024930FF060F5DC7589FD04E40DB6A1FA080100D1815F6335C735093D6D67782D55D06AB8A77D9CFB207A6B99D4E3AF8C54923457CB3AB47360D937804B35086FA10015B01AFA66BD10F7014BB13B86F0D96D8092B1ADCF06E46EA1C849C8D434DFEC22CA5B07A11A51D2D66EF628A8F58001A75402FD839288E1E620A419B7DB41A66157F64C146F6380B9A38BDDD87E84F50678C03F9CBA6D8288E37F8F403C26DF99AFEAFFE6B8975F026093C5DDEAFFA391DC31162E3275FBDA5CAA91D02ECFB0303650765F3E645BF1D04E5BFC3055E7F72FA2D132FACB58AFD9BBF860F890F01B61C539FEE1089305D9C1343A86A473D5D9D781762B86E89A4A9C1822A91E10FE1F48EA441A7F24AD8FCDB06C2119D1FB03994D08463A333691AA9442CFB; ck_login_out=91ceb967-82eb-eb11-80c0-ae2d6a9e3b11; _m6_prelogin=c=eyJTaXRlIjoiaHR0cDovL3RhankuZmRjeXVuLmNvbTo4MCIsIlVzZXIiOiIxODMxODAzNjkyNiIsIkxvZ291dFVybCI6Ii9QdWJQbGF0Zm9ybS9OYXYvTG9naW4vTG9nb3V0LmFzcHgiLCJUaW1lb3V0IjozMDB9&t=1776072169&v=678548EB505009A3'
html_content = fetch_grid_html(cookie)


extract_with_structured_fields(html_content)
# df = pd.DataFrame(contracts)
# print(df.head())
