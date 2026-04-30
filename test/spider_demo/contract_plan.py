import json
import traceback
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import re


class HTFKPlanSchedule:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://tajy.fdcyun.com:90"

        # 设置请求头，模拟浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cookie': 'keeplastname=18318036926; mycrm_isendcompany=1; mycrm_company=b14e0295-ce0b-ec11-80c0-ae2d6a9e3b11; ASP.NET_SessionId=bvebog55usbsd4bnzw00d02c; _NavToFunction=0201,; ck_login_out=91ceb967-82eb-eb11-80c0-ae2d6a9e3b11; userToken=FAC04D2A2668018774188FA746B0CC33ABD0D3BF42B7BFAAE09B5DC646C4A41097EE635431FA21F07FDEEAA0A8DF7F7414E2AC94DCF35C2B0DDF06011DCF5224ECDD9B7B37DD0E39A69D0AF0C8E83A351923A6B4C9864DC7916831B1BF38C6A2DC83B58088DE1D4C328208836C0625827246E7E974C86DF4777B586EC6797F283E4D7855575F67D25BC2C0AAFF51B49844C52B66882D9E3523A96DC51EDB4627B85568B660BF3FFAD7EE6512AF08C02CF65CB3F0AC9C594BFB640806080E0FC72141ED7FF361F453AAD50EE64DCCB9589484E274F32D3AF42655546D9E62CF1AD68622025610DD652F5F03925346E732BCDA4BA9D5170C7326F7EF63E5DBE0316F0D31CF4203A4558E2CC66B32C9ECCE577429C94AFF0D76C50DF1FC40FDACFDFED1EC7C665261EFF0D14AE46C124DBCC2A8BBB04258C98C9677F665963637FE388BB1A4BB4286B019AE349436A581A6A10AAAC664726435F31A35FD60967CBDB6388F68F8C775397065C8BB8D12F136DA1C5F4446FE536D94809A18327664952BB3A43C; _m6_prelogin=c=eyJTaXRlIjoiaHR0cDovL3RhankuZmRjeXVuLmNvbTo4MCIsIlVzZXIiOiIxODMxODAzNjkyNiIsIkxvZ291dFVybCI6Ii9QdWJQbGF0Zm9ybS9OYXYvTG9naW4vTG9nb3V0LmFzcHgiLCJUaW1lb3V0IjozMDB9&t=1776157810&v=5BA67AB6A521F726'
        })

    def get_payment_list(self, contract_guid):
        """获取应付进度款列表数据"""

        # 基础URL
        base_url = "http://tajy.fdcyun.com:90/_grid/griddata.aspx"

        # 参数
        params = {
            "xml": "/cbgl/HTFK/HTFKPlan_Schedule_Grid.xml",
            "funcid": "02010400",
            "gridId": "appGrid",
            "sortCol": "",
            "sortDir": "",
            "vscrollmode": "0",
            "multiSelect": "0",
            "selectByCheckBox": "0",
            "filter": "<filter/>",
            "processNullFilter": "1",
            "customFilter": f"ContractGUID='{contract_guid}'",
            "customFilter2": "",
            "dependencySQLFilter": "",
            "location": "",
            "pageNum": "1",
            "pageSize": "100",
            "showPageCount": "1",
            "appName": "Default",
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

    def fetch_plan_list(self, pageNum=1, ):
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
            "pageNum": f"{pageNum}",
            "defaultSelected": "1",
            "pageSize": "100",
            "appName": "Default",
            "showPageCount": "1",
            "funcid": "02010412",
            "application": "",
            "cp": ""
        }

        try:
            response = self.session.get(base_url, params=params, timeout=30)
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

    def extract_with_structured_fields(self, html_content):
        # 假设html_content是你的HTML内容
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. 提取表格数据
        table = soup.find('table', id='gridBodyTable')
        rows = table.find_all('tr')

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

        return simple_table_data

    def get_plan_detail(self, oid, htfk_plan_guid, contract_guid):
        """
        获取合同付款申请页面

        参数:
            mode: 模式
            oid: 对象ID
            htfk_plan_guid: 付款计划GUID
            contract_guid: 合同GUID
            open_source: 来源
            apply_state: 申请状态
            proj_type: 项目类型
            funcid: 功能ID

        返回:
            响应对象或None
        """
        # 基础URL
        base_url = "http://tajy.fdcyun.com:90/Cbgl/HTFK/HTFKApply_Edit.aspx"

        # 构建参数字典
        params = {
            'mode': '2',
            'oid': oid,
            'HTFKPlanGUID': htfk_plan_guid,
            'ContractGUID': contract_guid,
            'OpenSource': 'HTFKApply',
            'ApplyState': '2',
            'ProjType': '单项项目',
            'funcid': '02010412'
        }

        # 发送GET请求
        try:
            response = self.session.get(base_url, params=params, timeout=30)
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None

    def get_payment_detail(self, mode, title, contract_guid, oid, form_data=None):
        """如果需要提交表单数据"""
        url = f"{self.base_url}/cbgl/HTFK/HTFKPlan_Schedule_Edit.aspx"

        params = {
            'mode': mode,
            'title': title,
            'ContractGUID': contract_guid,
            'oid': oid
        }

        # 先GET获取页面，提取ViewState
        get_response = self.session.get(url, params=params)
        return get_response.text

    def extract_plan_info(self, html_content):
        """
        从付款申请页面提取关键字段信息

        参数:
            html_content: HTML页面内容

        返回:
            字典: 包含提取的所有字段信息
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # 存储提取的数据
        data = {}

        # 1. 提取所有隐藏字段的值
        hidden_fields = [
            'oid', 'ContractGUID', 'HTFKPlanGUID', 'AppliedBy', 'ApplyState',
            'PayState', 'ApplyClass', 'ApplyCode', 'ApplyTypeName', 'CurrencyGUID',
            'PayProviderGUID', 'ReceiveProviderGUID', 'BankName', 'BankAccounts',
            'ApplyDeptName', 'ApplyDate', 'ApplyAmount', 'YfAmount', 'DfdkAmount',
            'BalanceAmount', 'RemainAmount', 'Rate', 'FundType', 'FundName',
            'ApplyType', 'HTScheduleGUID', 'ProjType', 'OpenSource', 'funcid'
        ]

        for field in hidden_fields:
            elem = soup.find('input', {'name': field})
            if elem and elem.get('value'):
                data[field] = elem.get('value')

        # 2. 提取显示字段
        # 合同名称
        contract_name = soup.find('input', {'name': 'appForm_ContractName'})
        if contract_name:
            data['contract_name'] = contract_name.get('value', '')

        # 主题
        subject = soup.find('input', {'name': 'Subject'})
        if subject:
            data['Subject'] = subject.get('value', '')

        # 申请编号
        apply_code = soup.find('input', {'name': 'ApplyCode'})
        if apply_code:
            data['ApplyCode'] = apply_code.get('value', '')

        # 付款单位（显示文本）
        pay_provider_elem = soup.select_one('#_PayProviderGUID_Table .lui')
        if pay_provider_elem and hasattr(pay_provider_elem, 'text'):
            data['PayProviderName'] = pay_provider_elem.text.strip()

        # 收款单位
        receive_provider = soup.select_one('#_ReceiveProviderGUID_Table .lui')
        if receive_provider:
            data['ReceiveProviderName'] = receive_provider.text.strip()

        # 申请金额（显示值）
        apply_amount_bz = soup.find('input', {'name': 'ApplyAmount_Bz'})
        if apply_amount_bz:
            data['ApplyAmount'] = apply_amount_bz.get('value', '')

        # 应付金额
        yf_amount_bz = soup.find('input', {'name': 'YfAmount_Bz'})
        if yf_amount_bz:
            data['YfAmount'] = yf_amount_bz.get('value', '')

        # 代付代扣
        dfdk_amount = soup.find('input', {'name': 'DfdkAmount_Bz'})
        if dfdk_amount:
            data['DfdkAmountDisplay'] = dfdk_amount.get('value', '')

        # 其它扣款
        qtkk = soup.find('input', {'name': 'QTKK'})
        if qtkk:
            data['QTKK'] = qtkk.get('value', '')

        # 冲账金额
        balance_amount = soup.find('input', {'name': 'BalanceAmount_Bz'})
        if balance_amount:
            data['BalanceAmountDisplay'] = balance_amount.get('value', '')

        # 币种
        currency_name = soup.find('input', {'name': 'appForm_CurrencyName'})
        if currency_name:
            data['CurrencyName'] = currency_name.get('value', '')

        # 汇率
        rate = soup.find('input', {'name': 'Rate'})
        if rate:
            data['Rate'] = rate.get('value', '')

        # 申请人
        applied_by_name = soup.find('input', {'name': 'AppliedByName'})
        if applied_by_name:
            data['AppliedByName'] = applied_by_name.get('value', '')

        # 申请部门
        apply_dept = soup.find('input', {'name': 'appForm_ApplyDeptName'})
        if apply_dept:
            data['ApplyDeptName'] = apply_dept.get('value', '')

        # 申请日期
        apply_date = soup.find('input', {'name': 'ApplyDate'})
        if apply_date:
            data['ApplyDate'] = apply_date.get('value', '')

        # 付款说明
        apply_remarks = soup.find('textarea', {'name': 'ApplyRemarks'})
        if apply_remarks:
            data['ApplyRemarks'] = apply_remarks.text.strip()

        # 3. 提取下拉选择框的值
        # 申请类型（计划内/计划外）
        apply_type_sel = soup.find('input', {'name': 'ApplyType'})
        if apply_type_sel:
            data['ApplyType'] = apply_type_sel.get('returnValue', '')

        # 款项类型
        fund_type_sel = soup.find('input', {'name': 'FundType'})
        if fund_type_sel:
            data['FundType'] = fund_type_sel.get('returnValue', '')

        # 款项名称
        fund_name_sel = soup.find('input', {'name': 'FundName'})
        if fund_name_sel:
            data['FundName'] = fund_name_sel.get('returnValue', '')

        # 付款审批类型
        apply_type_name_sel = soup.find('input', {'name': 'appForm_ApplyTypeName'})
        if apply_type_name_sel:
            data['ApplyTypeName'] = apply_type_name_sel.get('returnValue', '')

        # 4. 提取关联信息
        # 关联应付进度款
        ht_schedule = soup.select_one('#_HTScheduleGUID_Table .lui')
        if ht_schedule:
            data['HTScheduleInfo'] = ht_schedule.text.strip()

        # 5. 提取页面标题
        title_elem = soup.find('title')
        if title_elem:
            data['PageTitle'] = title_elem.text.strip()

        # 6. 提取付款比例信息
        pay_rate_info = soup.find('input', {'name': 'ApplyRateInfo'})
        if pay_rate_info:
            data['ApplyRateInfo'] = pay_rate_info.get('value', '')

        return data

    def map_detail_to_database(self, datas):
        """将提取的应付进度款信息映射到数据库字段"""
        db_datas = list()
        for detail in datas:
            db_data = {
                # 需要关联查询或手动设置的字段
                'id': None,
                'group_id': 1,
                'team_id': 4,
                'project_id': None,
                'contract_id': None,  # 需要根据ContractName或ContractGUID查询
                'contract_name': detail.get('contract_name'),  # 需要根据ContractName或ContractGUID查询
                'pay_id': None,  # 需要根据HTScheduleGUID查询
                'oid': detail.get('HTScheduleGUID'),  # 需要根据HTScheduleGUID查询
                'op_num': None,

                # 类型ID字段（需要映射）
                'typ_id': None,  # 根据ApplyType映射（计划内/计划外）
                'approval_typ_id': None,  # 根据ApplyTypeName映射
                'amount_typ_id': None,  # 根据FundType映射

                # 人员ID字段（需要关联查询）
                'pay_unit_id': None,  # 根据PayProviderName查询
                'payee_id': None,  # 根据ReceiveProviderName查询
                'reporter': None,  # 根据AppliedByName查询用户ID
                'sender': None,  # 创建人ID，可与reporter相同

                # 直接映射的字段
                'title': detail.get('Subject'),
                'sn': detail.get('ApplyCode'),
                'pay_unit': detail.get('PayProviderName'),
                'payee': detail.get('ReceiveProviderName'),
                'bank_name': detail.get('BankName'),
                'bank_card': detail.get('BankAccounts'),
                'remaining_amount': self._parse_amount(detail.get('RemainAmount')),
                'payable_amount': self._parse_amount(detail.get('YfAmount')),
                'debit_amount': self._parse_amount(detail.get('DfdkAmountDisplay')),
                'amount_name': detail.get('FundName'),
                'depart': detail.get('ApplyDeptName'),
                'report_at': detail.get('ApplyDate'),
                'plan_report_at': None,  # 抓取数据中没有
                'desc': detail.get('ApplyRemarks'),

                # 文件字段（抓取数据中没有）
                'file_md5s': None,
                'invoice_file_md5s': None,

                # 信息字段（抓取数据中没有）
                'payment_infos': None,
                'invoice_infos': None,
                'tax_infos': None,

                # 状态字段（需要映射）
                'status': self._map_status(detail.get('ApplyState')),
                'stage': self._map_stage(detail.get('PayState')),

                # 金额字段
                'amount': self._parse_amount(detail.get('ApplyAmount')),
                'plan_amount': None,  # 抓取数据中没有，可能与amount相同
            }

            # 清理None值和空字符串
            db_data = {k: v for k, v in db_data.items() if v not in (None, '', [])}
            db_datas.append(db_data)

        return db_datas

    def _parse_amount(self, amount_str):
        """解析金额字符串，去除逗号并转换为float"""
        if not amount_str:
            return None
        if isinstance(amount_str, str):
            amount_str = amount_str.replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                return None
        return amount_str

    def _map_status(self, apply_state):
        """映射申请状态到status字段"""
        status_map = {
            '审核中': 0,  # 进行中
            '已批准': 1,  # 已付款
            '已驳回': 2,  # 驳回
            '已保存': 0,
            '已提交': 0,
        }
        return status_map.get(apply_state, 0)

    def _map_stage(self, pay_state):
        """映射支付状态到stage字段"""
        stage_map = {
            '未支付': 0,
            '支付中': 1,
            '已支付': 2,
            '支付失败': 3,
        }
        return stage_map.get(pay_state, 0)

    def generate_insert_sql(self, datas:list):
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

        with open('plan_sql.txt', 'a', encoding='utf-8') as f:
            f.write(sql + '\n')

        return sql


# 使用示例
if __name__ == "__main__":
    # 创建实例
    client = HTFKPlanSchedule()
    # 参数
    mode = "2"
    title = "查看应付进度款"

    ins_payment_items = list()
    ind = 1
    try:
        for pageNum in range(1, 12):
            plan_list_content = client.fetch_plan_list(pageNum)

            ids_list = client.extract_with_structured_fields(plan_list_content)
            for ids in ids_list:
                oid = ids['oid']
                HTFKPlanGUID = ids['HTFKPlanGUID']
                ContractGUID = ids['ContractGUID']
                plan_html_content = client.get_plan_detail(oid, HTFKPlanGUID, ContractGUID)
                data = client.extract_plan_info(plan_html_content)
                ins_payment_items.append(data)
            print(f'第{pageNum}页数据处理完成！')
            if len(ins_payment_items) > 10:
                client.generate_insert_sql(ins_payment_items)
                ins_payment_items = list()
    except Exception as err:
        print(f"程序异常: {err}")
        traceback.print_exc()
        # 异常时也尝试保存已处理的数据
        if ins_payment_items:
            try:
                sql = client.generate_insert_sql(ins_payment_items)
                print(f"异常退出前已保存{len(ins_payment_items)}条记录")
            except Exception as sql_error:
                print(f"保存SQL时出错: {sql_error}")
