import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import re


class ContractListFile:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://tajy.fdcyun.com:90/_grid/griddata.aspx"

        # 设置请求头，模拟浏览器
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://tajy.fdcyun.com:90/",
            'Cookie': 'keeplastname=18318036926; mycrm_isendcompany=1; mycrm_company=b14e0295-ce0b-ec11-80c0-ae2d6a9e3b11; ASP.NET_SessionId=5hmyvv45idejf545mzohk245; _NavToFunction=0201,; userToken=51D56D39692EC8DA79EFCCCD46AC18F4574A1357C4B562039FA321966A9E1A92E9F7995CB1C46C1FE6ABE3F4F35A9C39DD534FCB7B90E7ECA330192148BFF9B3816DD4A1A17FDFB14BFD0D9DA7C95FD3049054840E295E8A62417FD4078DB06408A508DAA77CF151004BE4F70AB168F231DED5CEA0E06DE26DA911A5354E557ACEF83ED7D145E428C4B77EC3359B937D65DC390FF4ABD35E62BFA932E8176E2F3B4FAB31AA320EFFC2543B45CBEDACF73183BA165EF2F71C0338FC0352DA5ACEA2BD5C6846FCACB793FF26331896603910BE134BB91D563BE55CFAD1F40A8729A2CF48FB3798FB7124B2B9649C647103C9D2E5D4FAFED9A3C778027366BD112CF65D4354EF07974AB069CE0BB7644E38455FBFC2311C2F69238DE2C5B074642C5D6366471D7449304F6341E6987D4E8781C93C4570D67E4E737AF68819C23C08E22F91B5B0A910B046E7FBE0DE8D5ED6989A641BED6331E2997947C76E7E10E515999C83EE37895499A0626068B81015A44D014CE64B4EB5C49608D1C38E0BC70AFEEBF3; ck_login_out=91ceb967-82eb-eb11-80c0-ae2d6a9e3b11; _m6_prelogin=c=eyJTaXRlIjoiaHR0cDovL3RhankuZmRjeXVuLmNvbTo4MCIsIlVzZXIiOiIxODMxODAzNjkyNiIsIkxvZ291dFVybCI6Ii9QdWJQbGF0Zm9ybS9OYXYvTG9naW4vTG9nb3V0LmFzcHgiLCJUaW1lb3V0IjozMDB9&t=1777478238&v=8ACB2DA7EFFF4ECE'
        })

    def get_contract_file_by_id(self, oid):
        url = 'http://tajy.fdcyun.com:90/_grid/griddata.aspx'
        params = {
            "xml": "/cbgl/pub/tab_doclist.xml",
            "gridId": "appGrid",
            "sortCol": "",
            "sortDir": "",
            "vscrollmode": "0",
            "multiSelect": "1",
            "selectByCheckBox": "0",
            "filter": f"<filter type='and'> <condition attribute='FkGUID' operator='eq' datatype='text' value='{oid}'/> <condition attribute='DocType' operator='eq' datatype='text' value='合同登记'/></filter>",
            "processNullFilter": "1",
            "customFilter": "2=2",
            "customFilter2": "",
            "dependencySQLFilter": "",
            "location": "",
            "pageNum": "1",
            "pageSize": "20",
            "showPageCount": "1",
            "appName": "Default",
            "application": "",
            "cp": ""
        }

        response = self.session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.text

    def extract_contract_file_path(self,html_content, contract_name):
        soup = BeautifulSoup(html_content, 'lxml')
        table = soup.find('table', id='gridBodyTable')
        BASE_URL = 'http://tajy.fdcyun.com:90'
        if table:
            rows = table.find_all('tr')

            print(f"找到 {len(rows)} 个文件，准备开始下载...\n")

            for row in rows:
                oid = row.get('oid')
                rel_url = row.get('filename')  # 相对路径，如 /UpFiles/...
                docname = row.get('docname')  # 原始文件名，如 延期承诺函.pdf

                # 如果缺少关键属性则跳过该行
                if not oid or not rel_url:
                    continue

                # 4. 拼接完整的下载链接
                full_download_url = BASE_URL + rel_url

                # 获取文件后缀名 (例如 '.pdf')
                _, ext = os.path.splitext(docname)
                temp_save_path = os.path.join(os.getcwd(), contract_name)
                save_path = os.path.join(os.getcwd(), contract_name, docname)
                if not os.path.exists(temp_save_path):
                    os.mkdir(temp_save_path)
                print(f"正在下载: {docname}")
                print(f"请求URL: {full_download_url}")

                try:
                    # 5. 发送请求下载文件
                    # 使用 stream=True 可以边下边存，防止大文件吃满内存
                    response = requests.get(full_download_url, stream=True, timeout=30)

                    if response.status_code == 200:
                        # 写入到当前目录
                        with open(save_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"✅ 下载成功，已保存为: {save_path}\n")
                    else:
                        print(f"❌ 下载失败，状态码: {response.status_code}\n")

                except Exception as e:
                    print(f"❌ 下载发生异常: {e}\n")
        else:
            print("未在 HTML 中找到附件列表 (id='gridBodyTable')")

    def get_contract_list(self, pageNum):
        """获取应付进度款列表数据"""
        # 基础URL
        base_url = "http://tajy.fdcyun.com:90/_grid/griddata.aspx"

        # 参数
        params = {
            "xml": "/CBGL/HTDL/Contract_WF_Grid.xml",
            "gridId": "appGrid",
            "sortCol": "ContractCode",
            "sortDir": "ascend",
            "vScrollMode": "0",
            "multiSelect": "0",
            "selectByCheckBox": "0",
            "filter": """<entity name="cb_Contract" primarykey="ContractGUID"><filter type="and"><filter type="and"><filter type="and"><filter type="and"/><filter><condition attribute="replace" operator="replace" value=" JbDeptCode='zb.BT3Q' or JbDeptCode like 'zb.BT3Q.%' "/></filter>\r\n\t</filter><filter><condition attribute="replace" operator="replace" value=" 88=88 "/></filter>\r\n</filter><filter type="and"><condition attribute="1" operator="eq" value="1"/></filter></filter></entity>""",
            "customFilter": "<TempValue>:e869661f-1642-f111-80c5-c7fdeab6be74",
            "customFilter2": "",
            "dependencySQLFilter": "",
            "location": "",
            "cols": "",
            "pageNum": f"{pageNum}",
            "defaultSelected": "1",
            "pageSize": "100",
            "appName": "Default",
            "showPageCount": "1",
            "funcid": "02010304",
            "application": "",
            "cp": ""
        }

        try:
            # 发送请求
            response = self.session.get(base_url, params=params, timeout=30)

            if response.status_code == 200 and '用户登录' not in response.text:
                # 尝试解析响应
                return response.text
            else:
                print(f"请求失败: {response.status_code}")
                return None

        except requests.RequestException as e:
            print(f"请求异常: {e}")
            return None

    def extract_contract_info_from_html(self, html_content):
        """从HTML中提取所有oid"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 2. 找到 ID 为 gridBodyTable 的表格
        table = soup.find('table', id='gridBodyTable')

        # 用于存放所有提取的合同数据
        contract_list = []

        if table:
            # 3. 提取表格中所有的 <tr> (每一行代表一个合同)
            rows = table.find_all('tr')

            for row in rows:
                # 获取 tr 标签的 oid 属性 (如果不为空，说明是有效的数据行)
                oid = row.get('oid')
                if not oid:
                    continue

                # 提取 tr 标签上的隐藏属性 (可选，很多有用的内部标识)
                ht_type_code = row.get('HtTypeCode')
                proj_type = row.get('ProjType')

                # 4. 获取该行所有的 <td> 列
                tds = row.find_all('td')

                # 确保列数足够，防止解析异常的空行
                if len(tds) >= 11:
                    # BeautifulSoup 的 .text 会自动去除内部的 <nobr> 标签，只保留纯文本
                    contract_data = {
                        "oid": oid,  # 唯一标识符
                        "序号": tds[0].text.strip(),
                        "审核状态": tds[1].text.strip(),
                        "结算状态": tds[2].text.strip(),
                        "合同类型": tds[3].text.strip(),
                        "合同编号": tds[4].text.strip(),
                        "合同名称": tds[5].text.strip(),
                        "合同金额(元)": tds[6].text.strip(),  # 注意：包含千分位逗号
                        "签订日期": tds[7].text.strip(),
                        "乙方/供应商": tds[8].text.strip(),
                        "所属项目/地块": tds[9].text.strip(),
                        "锁定状态": tds[10].text.strip(),
                        "内部项目类型": proj_type,  # 来自 tr 属性
                    }

                    contract_list.append(contract_data)

        return contract_list

    def extract_schedule_info(self, html_content):
        """提取应付进度款的所有数据，返回中文字段名"""
        soup = BeautifulSoup(html_content, 'html.parser')

        data = {}

        # 定义所有需要提取的字段及其中文名称
        fields = {
            # 基本信息
            'ContractCode': {'type': 'input', 'name': 'appForm_ContractCode', 'label': '合同编号'},
            'ContractName': {'type': 'input', 'name': 'appForm_ContractName', 'label': '合同名称'},
            'ApproveState': {'type': 'input', 'name': 'appForm_ApproveState', 'label': '审核状态'},

            # 金额字段 - 注意：这些input没有appForm_前缀
            'ApplyAmount_Bz': {'type': 'input', 'name': 'ApplyAmount_Bz', 'label': '上报金额'},
            'ApplyAmount': {'type': 'input', 'name': 'ApplyAmount', 'label': '上报金额(人民币)'},
            'ApproveAmount': {'type': 'input', 'name': 'ApproveAmount', 'label': '审定金额'},
            'ScheduleAmount_Bz': {'type': 'input', 'name': 'ScheduleAmount_Bz', 'label': '应付进度款'},
            'ScheduleAmount': {'type': 'input', 'name': 'ScheduleAmount', 'label': '应付进度款(人民币)'},
            'ScheduleConsult': {'type': 'input', 'name': 'ScheduleConsult', 'label': '应付进度参考'},
            'ItemAmount': {'type': 'input', 'name': 'ItemAmount', 'label': '甲供材料款'},
            'OtherDeduct': {'type': 'input', 'name': 'OtherDeduct', 'label': '其它扣款'},
            'PayPercent': {'type': 'input', 'name': 'PayPercent', 'label': '进度款支付比例(%)'},
            'Rate': {'type': 'input', 'name': 'Rate', 'label': '汇率'},

            # 人员信息
            'Applicant': {'type': 'input', 'name': 'Applicant', 'label': '上报人'},
            'ApprovedBy': {'type': 'input', 'name': 'ApprovedBy', 'label': '审定人'},
            'Budgeteer': {'type': 'input', 'name': 'Budgeteer', 'label': '预算人'},

            # 单据编号
            'BudgetDocNo': {'type': 'input', 'name': 'BudgetDocNo', 'label': '预算书编号'},
            'ApproveDocNo': {'type': 'input', 'name': 'ApproveDocNo', 'label': '应付进度款单号'},

            # 币种信息
            'CurrencyName': {'type': 'input', 'name': 'appForm_CurrencyName', 'label': '币种'},
            'Bz': {'type': 'input', 'name': 'appForm_Bz', 'label': '币种GUID'},

            # 日期字段
            'ApplyDate': {'type': 'input', 'name': 'ApplyDate', 'label': '上报日期'},
            'ApproveDate': {'type': 'input', 'name': 'ApproveDate', 'label': '审定日期'},

            # 文本域
            'PerformRemarks': {'type': 'textarea', 'name': 'PerformRemarks', 'label': '合同履行情况'},
            'RefHtTerms': {'type': 'textarea', 'name': 'RefHtTerms', 'label': '合同相关条款'},

            # 隐藏字段
            'oid': {'type': 'input', 'name': 'oid', 'label': '应付进度款GUID'},
            'ContractGUID': {'type': 'input', 'name': 'ContractGUID', 'label': '合同GUID'},
            'HtKind': {'type': 'input', 'name': 'appForm_HtKind', 'label': '合同类型'},
            'FKGUID': {'type': 'input', 'name': 'appForm_FKGUID', 'label': '附件GUID'},
            'YcfAmount': {'type': 'input', 'name': 'appForm_YcfAmount', 'label': '已拆分金额'},
            'IfBalanceUsed': {'type': 'input', 'name': 'appForm_IfBalanceUsed', 'label': '是否被结算使用'},
        }

        # 提取每个字段
        for field_name, field_info in fields.items():
            if field_name=='PerformRemarks':
                print(1)
            if field_info['type'] == 'input':
                element = soup.find('input', {'name': field_info['name']})
            else:  # textarea
                element = soup.find('textarea', {'name': field_info['name']})

            if element:
                if field_info['type'] == 'textarea':
                    data[field_info['label']] = element.get_text(strip=True)
                else:
                    data[field_info['label']] = element.get('value', '')
            else:
                data[field_info['label']] = None

        # 额外提取所有隐藏参数
        hidden_params = {
            'txtCfMode': '拆分模式',
            'txtJsState': '结算状态',
            'txtEnableHTScheduleSP': '是否启用工作流',
            'txtDeductAmount': '扣款总额',
            'txtDoneMode': '完成模式',
            '__mode': '页面模式',
            '__title': '页面标题'
        }

        for param, label in hidden_params.items():
            elem = soup.find('input', {'name': param})
            data[label] = elem.get('value', '') if elem else None

        return data

    def map_detail_to_database(self, datas):
        """将提取的应付进度款信息映射到数据库字段"""
        db_datas = list()
        for detail in datas:
            # 数据库映射
            db_data = {
                # 基本信息
                'op_num': detail.get('op_num'),  # 应付进度款GUID作为op_num
                'contract_id': detail.get('ContractGUID'),  # 合同GUID

                # 金额信息
                'pay_rate': detail.get('进度款支付比例'),  # 支付比例
                'payment_temp_amount': float(detail.get('应付进度参考').replace(',', '')),  # 应付进度款参考
                'payment_amount': float(detail.get('应付进度款').replace(',', '')),  # 应付进度款
                'report_amount': float(detail.get('上报金额').replace(',', '')),  # 上报金额
                'part_a_amount': float(detail.get('甲供材料款').replace(',', '')),  # 甲供材料款
                'other_amount': float(detail.get('其它扣款').replace(',', '')),  # 其他扣款
                'approved_amount': float(detail.get('审定金额').replace(',', '')),  # 审定金额

                # 日期信息
                'report_at': detail.get('上报日期'),  # 上报时间
                'approved_at': detail.get('审定日期'),  # 审定日期

                # 文本信息
                'contract_performance': detail.get('合同履行情况'),  # 合同履行情况
                'contract_clause': detail.get('合同相关条款'),  # 合同相关条款

                # 单据编号
                'budget_sn': detail.get('预算书编号'),  # 预算书编号
                'payment_sn': detail.get('应付进度款单号'),  # 应付进度款编号

                # 人员信息（需要根据用户名查询对应的用户ID）
                'reporter': detail.get('上报人'),  # 上报人（需转换为ID）
                'budgeter': detail.get('预算人'),  # 预算人（需转换为ID）
                'approver': detail.get('审定人'),  # 审定人（需转换为ID）
                'sender': detail.get('上报人'),  # 创建人（需转换为ID）

                # 状态信息
                'status': self._map_approve_state(detail.get('审核状态')),  # 审批状态
                'is_lock': '0',  # 是否锁定，默认未锁定

                # 其他字段
                'group_id': detail.get('group_id'),  # 集团ID，需要从其他地方获取
                'team_id': detail.get('team_id'),  # 团队ID，需要从其他地方获取
                'project_id': None,  # 项目ID，需要从其他地方获取
                'contract_name': detail.get('contract_name'),
                'oid': detail.get('oid'),
                # 扣款明细和工程量清单（JSON格式）
                'cut_lists': detail.get('cut_lists'),  # 扣款明细
                'bill_lists': detail.get('bill_lists'),  # 工程量清单
                'file_md5s': detail.get('附件'),  # 附件
            }

            # 清理None值和空字符串
            db_data = {k: v for k, v in db_data.items() if v not in (None, '', [])}
            db_datas.append(db_data)

        return db_datas

    def _map_approve_state(self, state):
        """映射审核状态到数据库状态码"""
        state_map = {
            '未审核': 0,
            '审核中': 1,
            '已审核': 2,
            '已驳回': 3
        }
        return state_map.get(state, 0)

    def generate_insert_sql(self, datas):
        """生成INSERT SQL语句"""
        print(f'插入了{len(datas)}条数据')
        all_data = self.map_detail_to_database(datas)
        # 获取所有字段的并集
        all_columns = set()
        for data in all_data:
            all_columns.update(data.keys())

        # 固定列顺序，确保每次生成的SQL一致
        columns = sorted(all_columns)
        columns_sql = ', '.join([f'`{col}`' for col in columns])

        # 构建VALUES部分
        values_list = []
        for data in all_data:
            row_values = []
            for col in columns:
                value = data.get(col)
                if value is None:
                    row_values.append('NULL')
                elif isinstance(value, str):
                    # 转义单引号
                    escaped_value = value.replace("'", "''")
                    row_values.append(f"'{escaped_value}'")
                elif isinstance(value, (int, float)):
                    row_values.append(str(value))
                else:
                    row_values.append(f"'{value}'")
            values_list.append(f"({', '.join(row_values)})")

        values_sql = ',\n    '.join(values_list)

        sql = f"""INSERT INTO `dynamic_cost_contract_payment_payable_test` ({columns_sql}) 
        VALUES 
            {values_sql};"""

        with open('payment_sql.txt', 'a', encoding='utf-8') as f:
            f.write(sql+'\n')

        return sql


# 使用示例
if __name__ == "__main__":
    # 创建实例
    client = ContractListFile()

    try:
        # for pageNum in range(1, 6):
        payment_list_html = client.get_contract_list(1)

        contract_list = client.extract_contract_info_from_html(payment_list_html)

        for contract in contract_list:
            # 获取详情
            html_content = client.get_contract_file_by_id(contract.get('oid'))
            client.extract_contract_file_path(html_content, contract.get('合同名称'))

    except Exception as err:
        print(f"程序异常: {err}")