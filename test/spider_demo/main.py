
if __name__ == "__main__":
    # 创建实例
    from test.spider_demo.contract_list_file import ContractListFile

    client = ContractListFile()

    try:
        for pageNum in range(1, 6):
            payment_list_html = client.get_contract_list(pageNum)

            contract_list = client.extract_contract_info_from_html(payment_list_html)

            for contract in contract_list:
                # 获取详情
                html_content = client.get_contract_file_by_id(contract.get('oid'))
                client.get_contract_file_path(html_content, contract.get('合同名称'))

    except Exception as err:
        print(f"程序异常: {err}")