import json
import traceback
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class HTFKOrderSchedule:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://tajy.fdcyun.com:90/_grid/griddata.aspx?xml=%2FCbgl%2FHTFK%2FPay_Grid_ALL.xml&gridId=appGrid&sortCol=ApplyDate&sortDir=descend&vScrollMode=0&multiSelect=1&selectByCheckBox=0&filter=%3Centity+name%3D%22vcb_HTFKApply%22+primarykey%3D%22HTFKApplyGUID%22%3E%3Cfilter+type%3D%22and%22%3E%3Cfilter+type%3D%22and%22%3E%3Cfilter+type%3D%22and%22%3E%3Cfilter+type%3D%22and%22%2F%3E%3Cfilter%3E%3Ccondition+attribute%3D%22replace%22+operator%3D%22replace%22+value%3D%22+c.HierarchyCode%3D%27zb.BT3Q%27+or+c.HierarchyCode+like+%27zb.BT3Q.%25%27+%22%2F%3E%3C%2Ffilter%3E%0D%0A%09%3C%2Ffilter%3E%3Cfilter+type%3D%22and%22%3E%3Ccondition+attribute%3D%221%22+operator%3D%22eq%22+value%3D%221%22%2F%3E%3C%2Ffilter%3E%3C%2Ffilter%3E%3Cfilter%3E%3Ccondition+attribute%3D%22replace%22+operator%3D%22replace%22+value%3D%22+88%3D88+%22%2F%3E%3C%2Ffilter%3E%0D%0A%3C%2Ffilter%3E%3C%2Fentity%3E&customFilter=%3CTempValue%3E%3A885b0bc6-cb37-f111-80c5-c7fdeab6be74&customFilter2=&dependencySQLFilter=&location=&cols=&defaultSelected=1&appName=Default&showPageCount=1&application=&cp="

        # 设置请求头，模拟浏览器
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Cookie': 'keeplastname=18318036926; mycrm_isendcompany=1; mycrm_company=b14e0295-ce0b-ec11-80c0-ae2d6a9e3b11; ASP.NET_SessionId=bvebog55usbsd4bnzw00d02c; _NavToFunction=0201,; userToken=3E805B91D4BB06A46DBFDA33AC80D52DF764F320F5ED830C4865111E79604BA59B76B57147926907148109E7C177FE592844629BF59711166B28AB5AB964155634E261FDE34B4FB08F8ED396FAC92723FD9AB2DE92B83064CF57D0188530414F6F56C62CDFF054BA5F9D745FCC54364E86C0BEFC4C083756B3ABAEF3EA107029F81EEED2BD7B42768C1CE4E64934BD33B857AF2F6106EC1ABA208F764B2F1FB8DB48692E82019222EBD3ED9A753AC6A501A3D8277DAB5C11F249583329B06F9B90D0E004F8CC4905C3DBEEF04F8FBE949A354CB51C58568B1B7D7ADB14D42589A98BF3D89B81FE998E6DD74FBF30BB1828C9714866ADAC744CB14EDABBCB9B01F22B60188D641B4F7726B16B14FA5C1227E61FED6E6509E0D7041F8F32E1B94EAB410D53E9CC9005580804B0121791CFB2BDD1DC83856B76371B0A14813A8D41B3699D1C8A4B0E9CB963B66F5C5980B527F40DB223A2FDBC419B369F69A7B32A190265739AFDF5D479F6EF6337DF6292424CFD1162265DBF9BBE2083A386619439AB7F89; ck_login_out=91ceb967-82eb-eb11-80c0-ae2d6a9e3b11; _m6_prelogin=c=eyJTaXRlIjoiaHR0cDovL3RhankuZmRjeXVuLmNvbTo4MCIsIlVzZXIiOiIxODMxODAzNjkyNiIsIkxvZ291dFVybCI6Ii9QdWJQbGF0Zm9ybS9OYXYvTG9naW4vTG9nb3V0LmFzcHgiLCJUaW1lb3V0IjozMDB9&t=1776244769&v=686858469FAB73E5'
        })

    def fetch_order_list(self, pageNum=1, ):
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
        # 请求参数
        params = {
            'pageNum': f'{pageNum}',
            'pageSize': '100'
        }

        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
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
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. 找到目标表格
        table = soup.find('table', id='gridBodyTable')

        # 2. 定义表头（根据 HTML 中的内容推断）
        titles = [
            "序号", "勾选状态", "付款说明", "申请编号", "申请日期",
            "申请金额", "应付金额", "部门", "经办人", "合同名称",
            "合同编号", "结算单号/账号", "收款单位", "开户行"
        ]

        data_list = []

        # 3. 遍历所有行 (tr)
        rows = table.find_all('tr')
        for row in rows:
            # 提取当前行的所有单元格 (td)
            cols = row.find_all('td')

            # 提取文本并清理（去掉空格和换行）
            # row_data = [ele.get_text(strip=True) for ele in cols]

            # 如果你想获取 tr 上的隐藏属性（如 GUID），可以这样做：
            row_id = row.get('oid')
            contract_guid = row.get('contractguid')
            pay_state = row.get('paystate')

            # 组合一行的数据
            row_values = [ele.get_text(strip=True) for ele in cols]

            # 为了方便后续分析，我们可以把隐藏属性也加进去
            row_dict = dict(zip(titles, row_values))
            row_dict['ContractGUID'] = contract_guid
            row_dict['RecordGUID'] = row_id
            row_dict['PayState'] = pay_state

            data_list.append(row_dict)

        return data_list

    def get_plan_detail(self, oid, contract_guid):
        url = "http://tajy.fdcyun.com:90/Cbgl/HTFK/Pay_PayDetailByHTFKApply_Grid.aspx"

        # 请求参数
        params = {
            "mode": "2",
            "oid": oid,
            "ContractGUID": contract_guid,
            "IsFyControl": "0",
            # "PayState": "完全支付",
            "funcid": "02010408"
        }

        try:
            # 发送 GET 请求
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            # 设置编码（根据返回内容自动检测或手动设置）
            response.encoding = response.apparent_encoding  # 或 'utf-8'

            return response.text

        except Exception as err:
            print(f"程序异常: {err}")

    def extract_plan_info(self, HTFKApplyGUID, ContractGUID):
        order, payed = self.sub_order(HTFKApplyGUID, ContractGUID)
        invoice = self.sub_invoice(HTFKApplyGUID, ContractGUID)
        order_info = self.extract_order(order)
        payed_info = self.extract_payed(payed)

        invoice_result = list()
        for _i in invoice:
            invoice_items = list()
            for _d in _i.get('InvoiceItemDetail'):
                invoice_items.append({
                    'item_name': _i.get("TaxableServiceName"),  # 物品名称 -> 应税服务名称
                    'amount_without_tax': _i.get("ExcludingTaxInvoiceAmount"),  # 不含税价 -> 不含税金额
                    'input_tax_amount': _i.get("InputTaxAmount"),  # 进项税额 -> 进项税额
                    'amount_with_tax': _i.get("InvoiceAmount"),  # 含税价 -> 发票金额
                    'remark': "",  # 备注固定为空字符串
                })
            invoice_result.append({
                'invoice_no': _i.get("InvoNO"),  # 开票编号 -> 票据编号
                'invoice_type': _i.get("InvoiceType"),  # 发票类型 -> 票据类型
                'amount_with_tax': _i.get("InvoiceAmount"),  # 含税价 -> 发票金额
                'amount_without_tax': _i.get("ExcludingTaxInvoiceAmount"),  # 不含税价 -> 不含税金额
                'input_tax_amount': _i.get("InputTaxAmount"),  # 进项税额 -> 进项税额
                'invoice_date': _i.get("InvoiceDate"),  # 开票日期 -> 开票日期
                'invoice_bank': _i.get("SellerCompanyBankNNum"),  # 开票公司 -> 销售方银行账号
                'invoice_unit': _i.get("ReceiveUnitName"),  # 发票单位 -> 收款单位名称
                'remark': _i.get("Remarks"),  # 备注 -> 备注
                'pay_id': _i.get("HTFKApplyGUID"),  # 应付进度款ID -> 付款申请GUID
                'contract_id': _i.get("ContractGUID"),  # 合同ID -> 合同GUID
                'invoice_items': invoice_items,  # 发票信息 -> 发票明细
            })

        return order_info, payed_info, invoice_result

    def sub_order(self, HTFKApplyGUID, ContractGUID):
        url = "http://tajy.fdcyun.com:90/_grid/griddata.aspx"

        params = {
            "xml": "/cbgl/HTFK/Pay_VoucherGrid.xml",
            "funcid": "02010408",
            "gridId": "appGrid",
            "sortCol": "",
            "sortDir": "",
            "vscrollmode": "0",
            "multiSelect": "1",
            "selectByCheckBox": "0",
            "filter": "<filter/>",
            "processNullFilter": "1",
            "customFilter": f"cb_Voucher.ContractGUID='{ContractGUID}' and (HTFKApplyGUID='{HTFKApplyGUID}' OR HTFKApplyGUID='{ContractGUID}')",
            "customFilter2": "",
            "dependencySQLFilter": "",
            "location": "",
            "pageNum": "1",
            "showPageCount": "1",
            "appName": "Default",
            "application": "",
            "cp": ""
        }

        params1 = {
            "xml": "/cbgl/HTFK/Pay_AmountItemGrid.xml",
            "funcid": "02010408",
            "gridId": "appGrid",
            "sortCol": "",
            "sortDir": "",
            "vscrollmode": "0",
            "multiSelect": "0",
            "selectByCheckBox": "0",
            "processNullFilter": "1",
            "customFilter": f"a.ContractGUID='{ContractGUID}' AND (a.HTFKApplyGUID='{ContractGUID}' OR a.HTFKApplyGUID='{HTFKApplyGUID}')",
            "customFilter2": "",
            "dependencySQLFilter": "",
            "location": "",
            "pageNum": "1",
            "showPageCount": "1",
            "appName": "Default",
            "application": "",
            "cp": ""
        }

        try:
            response = self.session.get(url, params=params, timeout=15)
            response1 = self.session.get(url, params=params1, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            response1.encoding = 'utf-8'

            return response.text, response1.text
        except Exception as e:
            print(f"请求失败: {e}")

    def extract_order(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', id='gridBodyTable')

        if not table:
            return []

        # 定义字段名
        fields = ['serial_no', 'status', 'date', 'voucher_type', 'category',
                  'remark', 'amount', 'other_amount', 'difference', 'is_completed', 'operator']

        results = []
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if not cells:
                continue

            row_dict = {}
            for i, cell in enumerate(cells):
                if i >= len(fields):
                    break
                nobr = cell.find('nobr')
                text = nobr.get_text(strip=True) if nobr else cell.get_text(strip=True)
                # 数值类型转换
                if fields[i] in ['amount', 'other_amount', 'difference']:
                    text = float(text.replace(',', '')) if text else 0.0
                row_dict[fields[i]] = text

            # 同时保留行属性
            row_dict['_oid'] = row.get('oid')
            row_dict['_contract_guid'] = row.get('contractguid')

            results.append(row_dict)
        db_datas = list()
        for _ in results:
            db_datas.append({
                "desc": _.get("remark"),
                "bill_typ": _.get("category"),
                "invoice_amount": _.get("amount"),
                "actual_amount": _.get("other_amount"),
                "report_at": _.get("date"),
                "reporter": _.get("operator"),
                "status": _.get("status"),
                "bill_sn": _.get("serial_no"),
                "check_at": _.get("date"),
                "checker": _.get("operator")
            })

        return db_datas

    def extract_payed(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        # 定义列标题（根据实际显示）
        column_titles = [
            "序号", "合同名称", "付款类型", "付款日期", "币种",
            "付款金额", "汇率", "折合同币金额", "发票金额",
            "付款方式", "银行账号", "", "", "票据类型", "", ""
        ]

        # 定义字段名
        field_names = [
            "serial_number", "contract_name", "payment_type", "payment_date", "currency",
            "payment_amount", "exchange_rate", "converted_amount", "invoice_amount",
            "payment_method", "bank_account", "field_12", "field_13",
            "invoice_type", "field_15", "field_16"
        ]

        data_list = []
        table = soup.find('table', id='gridBodyTable')

        if table:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if cells and len(cells) > 1:  # 至少有2个单元格才是数据行
                    row_dict = {}

                    # 提取行元数据
                    row_dict['oid'] = row.get('oid', '')
                    row_dict['vouch_guid'] = row.get('ovouchguid', '')
                    row_dict['vouch_type'] = row.get('ovouchtype', '')
                    row_dict['contract_guid'] = row.get('contractguid', '')
                    row_dict['approve_state'] = row.get('approvestate', '')

                    # 提取单元格数据
                    for idx, cell in enumerate(cells):
                        if idx < len(field_names):
                            # 获取单元格文本
                            nobr = cell.find('nobr')
                            value = nobr.get_text(strip=True) if nobr else cell.get_text(strip=True)

                            # 处理数字格式
                            if field_names[idx] in ['payment_amount', 'exchange_rate', 'converted_amount',
                                                    'invoice_amount']:
                                if value:
                                    # 移除千分位逗号
                                    value = value.replace(',', '')
                                    try:
                                        if field_names[idx] == 'exchange_rate':
                                            value = float(value)
                                        else:
                                            value = float(value)
                                    except:
                                        pass

                            row_dict[field_names[idx]] = value
                            row_dict[column_titles[idx]] = value  # 同时用中文标题

                    data_list.append(row_dict)

        db_datas = list()
        for _i in data_list:
            db_datas.append({
                "currency": _i.get("currency"),
                "converted_amount": _i.get("converted_amount"),
                "exchange_rate": _i.get("exchange_rate"),
                "payment_method": _i.get("payment_method"),
                "bank_name": _i.get("bank_account"),
                "amount": _i.get("payment_amount"),
                "amount_name": _i.get("payment_type"),
                "payment_source": _i.get("payment_type"),
                "remark": _i.get("field_16"),
                "title": _i.get("contract_name"),
                "settlement_method": _i.get("payment_method")
            })
        return db_datas

    def sub_invoice(self, HTFKApplyGUID, ContractGUID):
        import requests

        url = "http://tajy.fdcyun.com:90/CBGL/HTFK/Pay_XMLHTTP.aspx"

        params = {
            "HTFKApplyGUID": HTFKApplyGUID,
            "ContractGUID": ContractGUID,
            "FromPage": "FKApplyInfo",
            "ywtype": "GetInvoiceItemListByHTFkApply",
            "MySessionState": "595e35eb-6838-f111-80c5-c7fdeab6be74",
            "rdnum": "0.9440859755733779"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            'Cookie': 'keeplastname=18318036926; mycrm_isendcompany=1; mycrm_company=b14e0295-ce0b-ec11-80c0-ae2d6a9e3b11; ASP.NET_SessionId=bvebog55usbsd4bnzw00d02c; _NavToFunction=0201,; userToken=3E805B91D4BB06A46DBFDA33AC80D52DF764F320F5ED830C4865111E79604BA59B76B57147926907148109E7C177FE592844629BF59711166B28AB5AB964155634E261FDE34B4FB08F8ED396FAC92723FD9AB2DE92B83064CF57D0188530414F6F56C62CDFF054BA5F9D745FCC54364E86C0BEFC4C083756B3ABAEF3EA107029F81EEED2BD7B42768C1CE4E64934BD33B857AF2F6106EC1ABA208F764B2F1FB8DB48692E82019222EBD3ED9A753AC6A501A3D8277DAB5C11F249583329B06F9B90D0E004F8CC4905C3DBEEF04F8FBE949A354CB51C58568B1B7D7ADB14D42589A98BF3D89B81FE998E6DD74FBF30BB1828C9714866ADAC744CB14EDABBCB9B01F22B60188D641B4F7726B16B14FA5C1227E61FED6E6509E0D7041F8F32E1B94EAB410D53E9CC9005580804B0121791CFB2BDD1DC83856B76371B0A14813A8D41B3699D1C8A4B0E9CB963B66F5C5980B527F40DB223A2FDBC419B369F69A7B32A190265739AFDF5D479F6EF6337DF6292424CFD1162265DBF9BBE2083A386619439AB7F89; ck_login_out=91ceb967-82eb-eb11-80c0-ae2d6a9e3b11; _m6_prelogin=c=eyJTaXRlIjoiaHR0cDovL3RhankuZmRjeXVuLmNvbTo4MCIsIlVzZXIiOiIxODMxODAzNjkyNiIsIkxvZ291dFVybCI6Ii9QdWJQbGF0Zm9ybS9OYXYvTG9naW4vTG9nb3V0LmFzcHgiLCJUaW1lb3V0IjozMDB9&t=1776244769&v=686858469FAB73E5'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            # 如果返回的是JSON，可以解析
            if response.text.strip().startswith('{') or response.text.strip().startswith('['):
                import json
                data = response.json()
                return data
            else:
                raise Exception('发票请求失败')

            return response.text

        except Exception as e:
            print(f"请求失败: {e}")

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

    def add_base_info(self, items, _field, _field_value):
        if isinstance(items, list):
            for item in items:
                item[_field] = _field_value
        if isinstance(items, dict):
            items[_field] = _field_value

    def generate_insert_sql(self, datas: list, file_name, table_name):
        """生成INSERT SQL语句"""
        if not datas:
            return

        # 获取所有字段的并集
        all_columns = set()
        all_columns.update(datas[0].keys())

        # 固定列顺序，确保每次生成的SQL一致
        columns = sorted(all_columns)
        columns_sql = ', '.join([f'`{col}`' for col in columns])

        # 构建VALUES部分
        values_list = []
        for data in datas:
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

        sql = f"""INSERT INTO `{table_name}` ({columns_sql}) 
        VALUES 
            {values_sql};"""

        with open(file_name, 'a', encoding='utf-8') as f:
            f.write(sql + '\n')

        print(f'插入了 {table_name} -- {len(datas)}条数据')

        return sql


# 使用示例
if __name__ == "__main__":
    # 创建实例
    client = HTFKOrderSchedule()
    # 参数
    mode = "2"
    title = "查看应付进度款"

    ins_order_items, ins_payed_items, ins_invoice_items = list(), list(), list()
    ind = 1
    name_oid_map = dict()
    try:
        for pageNum in range(1, 11):
            plan_list_content = client.fetch_order_list(pageNum)

            ids_list = client.extract_with_structured_fields(plan_list_content)
            for ids in ids_list:
                oid = ids['RecordGUID']
                ContractGUID = ids['ContractGUID']
                # oid = '3cd56ce7-9305-f111-80c5-c7fdeab6be74'
                # ContractGUID = '4212d5d1-0bc0-ee11-80c4-b1fe5a19d94c'
                name_oid_map[oid] = ids.get('付款说明')

                # plan_html_content = client.get_plan_detail(oid, ContractGUID)
                order_info, payed_info, invoice_result = client.extract_plan_info(oid, ContractGUID)
                client.add_base_info(order_info, 'plan_name', ids.get('付款说明'))
                client.add_base_info(payed_info, 'plan_name', ids.get('付款说明'))
                client.add_base_info(invoice_result, 'plan_name', ids.get('付款说明'))
                ins_order_items.extend(order_info)
                ins_payed_items.extend(payed_info)
                ins_invoice_items.extend(invoice_result)

            print(f'第{pageNum}页数据处理完成！')
            client.generate_insert_sql(ins_order_items, 'order_sql.txt',
                                       'dynamic_cost_contract_payment_order_test')
            client.generate_insert_sql(ins_payed_items, 'payed_sql.txt',
                                       'dynamic_cost_contract_payment_paid_list_test')
            client.generate_insert_sql(ins_invoice_items, 'invoice_sql.txt',
                                       'dynamic_cost_contract_payment_invoice_list_test')
            ins_order_items, ins_payed_items, ins_invoice_items = list(), list(), list()
    except Exception as err:
        print(f"程序异常: {err}")
        traceback.print_exc()
        # 异常时也尝试保存已处理的数据
        try:
            client.generate_insert_sql(ins_order_items, 'order_sql.txt',
                                       'dynamic_cost_contract_payment_order_test')
            client.generate_insert_sql(ins_payed_items, 'payed_sql.txt',
                                       'dynamic_cost_contract_payment_paid_list_test')
            client.generate_insert_sql(ins_invoice_items, 'invoice_sql.txt',
                                       'dynamic_cost_contract_payment_invoice_list_test')
            print(f"异常退出前已保存{len(ins_order_items)}条记录")
        except Exception as sql_error:
            print(f"保存SQL时出错: {sql_error}")
