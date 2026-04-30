# coding: utf-8
"""调试知识库问题"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.knowledge_base_service import KnowledgeBaseService
import shutil

# 创建知识库服务
kb_service = KnowledgeBaseService(persist_directory="./data/vector_store")
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
file_path = os.path.join(base_dir, "app/utils/langchain_langgraph/user_uploads/manual.txt")

result = kb_service.upload_document(
    file_path='C:/Users/liukk/Desktop/wizard/app/utils/langchain_langgraph/user_uploads/manual.txt',
    collection_name="manuals",
    metadata={"category": "产品手册", "department": "技术部"}
)
print(result)
print("=" * 60)
print("调试知识库问题")
print("=" * 60)

# 1. 检查向量存储状态
print("\n1. 检查向量存储状态...")
try:
    store = kb_service.vector_manager.get_or_create_store("manuals")
    if hasattr(store, '_collection'):
        collection = store._collection
        count = collection.count()
        print(f"向量存储中的文档数量: {count}")
    else:
        print("无法获取集合信息")
except Exception as e:
    print(f"检查失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试检索
print("\n2. 测试检索...")
query = "错误代码E01"
print(f"查询: {query}")

try:
    results = kb_service.search(query=query, collection_name="manuals", k=3)
    print(f"检索结果数量: {len(results)}")
    for i, result in enumerate(results):
        print(f"\n结果 {i+1}:")
        print(f"内容: {result['content']}")
except Exception as e:
    print(f"检索失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 检查数据库记录
print("\n3. 检查数据库记录...")
try:
    docs = kb_service.list_documents(collection_name="manuals")
    print(f"数据库中的文档数量: {len(docs)}")
    for doc in docs:
        print(f"文档: {doc['title']}, ID: {doc['id']}, 片段数: {doc['chunk_count']}")
except Exception as e:
    print(f"检查失败: {e}")

# 4. 测试直接检索器调用
print("\n4. 测试直接检索器调用...")
try:
    store = kb_service.vector_manager.get_or_create_store("manuals")
    retriever = store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    print(f"检索到的文档数量: {len(docs)}")
    for i, doc in enumerate(docs):
        print(f"\n文档 {i+1}:")
        print(f"完整内容: {doc.page_content}")
        print(f"元数据: {doc.metadata}")
except Exception as e:
    print(f"检索失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试问答
print("\n5. 测试问答...")
try:
    result = kb_service.ask(question=query, collection_name="manuals", return_sources=True)
    print(f"回答: {result['answer']}")
    print(f"来源数量: {len(result.get('sources', []))}")
    if result.get('sources'):
        for i, source in enumerate(result['sources']):
            print(f"来源 {i+1}: {source['content']}")
except Exception as e:
    print(f"问答失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("调试完成")
print("=" * 60)