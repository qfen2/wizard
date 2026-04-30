import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import re


class HTFKPaymentSchedule:
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

    def extract_oids_from_html(self, html_content):
        """从HTML中提取所有oid"""
        soup = BeautifulSoup(html_content, 'html.parser')

        oids = []

        # 方法1：从表格行中提取oid属性
        rows = soup.find_all('tr', {'oid': True})
        for row in rows:
            oid = row.get('oid')
            if oid:
                oids.append(oid)

        return oids

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
    client = HTFKPaymentSchedule()
    from test.spider_demo.contract_list import contract_dic

    # 参数
    mode = "2"
    title = "查看应付进度款"

    ins_payment_items = list()
    ind = 1
    try:
        for contract_guid, contract_name in contract_dic.items():
            payment_list_html = client.get_payment_list(contract_guid)

            oids = client.extract_oids_from_html(payment_list_html)

            for oid in oids:
                # 获取详情
                html_content = client.get_payment_detail(mode, title, contract_guid, oid)

                detail = client.extract_schedule_info(html_content)
                detail['group_id'] = 1
                detail['team_id'] = 4
                detail['contract_name'] = contract_name
                detail['oid'] = oid
                ins_payment_items.append(detail)
            # ind+=1
            # if ind>10:
            #     raise Exception('测试报错')

            print(f'{contract_name} -- {len(oids)}条数据抓取结束')
            if len(ins_payment_items)>10:
                client.generate_insert_sql(ins_payment_items)
                ins_payment_items = list()

    except Exception as err:
        print(f"程序异常: {err}")
        # 异常时也尝试保存已处理的数据
        if ins_payment_items:
            try:
                sql = client.generate_insert_sql(ins_payment_items)
                print(f"异常退出前已保存{len(ins_payment_items)}条记录")
            except Exception as sql_error:
                print(f"保存SQL时出错: {sql_error}")
