import requests

data = {'securityCode': '3705', 'cardNumber': '371036213041036', 'month': '05', 'year': '28', 'postalCode': '27040'}
rsp = requests.post('http://18.162.50.43:5005/add_account', data=data)
print(rsp.status_code)

