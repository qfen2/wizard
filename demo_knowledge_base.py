# coding: utf-8
"""
知识库服务使用演示
演示如何正确使用文件路径上传和查询文档
"""

import os

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_project_file(relative_path):
    """
    获取项目根目录下的文件绝对路径
    
    Args:
        relative_path: 相对于项目根目录的路径
        
    Returns:
        文件的绝对路径
    """
    return os.path.join(PROJECT_ROOT, relative_path).replace('\\', '/')


def main():
    print("=" * 60)
    print("知识库服务使用演示")
    print("=" * 60)
    
    # 导入服务
    from app.services.knowledge_base_service import KnowledgeBaseService
    
    # 创建服务实例
    kb_service = KnowledgeBaseService(persist_directory="./data/vector_store")
    
    # 示例1: 使用绝对路径上传文档
    print("\n【示例1】上传文档")
    print("-" * 60)
    
    # 方式1: 使用 get_project_file 函数
    file_path = get_project_file("app/utils/langchain_langgraph/user_uploads/manual.txt")
    print(f"文件路径: {file_path}")
    print(f"文件存在: {os.path.exists(file_path)}")
    
    # 方式2: 直接构造绝对路径
    # file_path = "C:/Users/liukk/Desktop/wizard/app/utils/langchain_langgraph/user_uploads/manual.txt"
    
    # 方式3: 使用 os.path.join
    # file_path = os.path.join(PROJECT_ROOT, "app/utils/langchain_langgraph/user_uploads/manual.txt")
    
    if os.path.exists(file_path):
        result = kb_service.upload_document(
            file_path=file_path,
            collection_name="demo_manuals",
            metadata={
                "category": "产品手册",
                "department": "技术部",
                "version": "1.0"
            }
        )
        
        if result.get('success'):
            print(f"✓ 上传成功")
            print(f"  文档ID: {result.get('document_id')}")
            print(f"  分块数量: {result.get('chunk_count')}")
            print(f"  集合名称: {result.get('collection_name')}")
        else:
            print(f"✗ 上传失败: {result.get('message')}")
    else:
        print(f"✗ 文件不存在: {file_path}")
    
    # 示例2: 搜索文档
    print("\n【示例2】语义搜索")
    print("-" * 60)
    
    query = "连接网络"
    print(f"查询: {query}")
    
    results = kb_service.search(
        query=query,
        collection_name="demo_manuals",
        k=3
    )
    
    if results:
        print(f"✓ 找到 {len(results)} 个相关结果")
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"  内容: {result['content'][:100]}...")
            print(f"  来源: {result['metadata'].get('file_name', 'N/A')}")
            print(f"  相似度: {result.get('score', 'N/A')}")
    else:
        print("✗ 未找到相关结果")
    
    # 示例3: 智能问答
    print("\n【示例3】智能问答 (RAG)")
    print("-" * 60)
    
    question = "如何清理传感器？"
    print(f"问题: {question}")
    
    qa_result = kb_service.ask(
        question=question,
        collection_name="demo_manuals",
        return_sources=True
    )
    
    if qa_result.get('success'):
        print(f"✓ 回答: {qa_result['answer']}")
        
        if 'sources' in qa_result:
            print(f"\n来源文档 ({len(qa_result['sources'])} 个):")
            for i, source in enumerate(qa_result['sources'], 1):
                print(f"\n来源 {i}:")
                print(f"  文件: {source['metadata'].get('file_name', 'N/A')}")
                print(f"  内容: {source['content'][:80]}...")
    else:
        print(f"✗ 问答失败: {qa_result.get('answer')}")
    
    # 示例4: 列出文档
    print("\n【示例4】列出文档")
    print("-" * 60)
    
    docs = kb_service.list_documents(collection_name="demo_manuals")
    
    if docs:
        print(f"✓ 共 {len(docs)} 个文档")
        for doc in docs:
            print(f"\n文档:")
            print(f"  ID: {doc['id']}")
            print(f"  标题: {doc['title']}")
            print(f"  类型: {doc['file_type']}")
            print(f"  大小: {doc['file_size']} 字节")
            print(f"  分块: {doc['chunk_count']} 个")
            print(f"  上传时间: {doc['created_at']}")
    else:
        print("✗ 没有文档")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()