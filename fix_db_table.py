from app.services.knowledge_base_service import DocumentModel
from app.utils.db_utils import db_manager

print("修复数据库表...")

# 获取数据库连接
db = db_manager.get('zj3')

# 检查表结构
cursor = db.execute_sql("SHOW CREATE TABLE documents")
result = cursor.fetchone()
print(f"\n当前表结构:")
print(result[1])

# 检查是否有 ID=0 的记录
cursor = db.execute_sql("SELECT id, title, file_path FROM documents WHERE id = 0")
record = cursor.fetchone()
if record:
    print(f"\n发现 ID=0 的记录:")
    print(f"  ID: {record[0]}, Title: {record[1]}, File: {record[2]}")
    print("正在删除...")
    cursor = db.execute_sql("DELETE FROM documents WHERE id = 0")
    db.commit()
    print("已删除")

# 检查其他记录
cursor = db.execute_sql("SELECT id, title, file_path FROM documents")
records = cursor.fetchall()
print(f"\n当前所有记录:")
for rec in records:
    print(f"  ID: {rec[0]}, Title: {rec[1]}, File: {rec[2]}")

print("\n数据库修复完成")