# coding: utf-8
"""
LangChain & LangGraph 研究助手使用示例

本文件展示了如何使用研究助手系统进行各种研究任务。
"""

import os
from research_assistant import ResearchAssistant


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 创建研究助手
    assistant = ResearchAssistant(max_iterations=2)
    
    # 执行研究
    result = assistant.research("Python 异步编程的最佳实践")
    
    # 显示结果
    print("\n最终报告:")
    print("-" * 60)
    print(result["final_report"])
    print("-" * 60)
    print(f"\n迭代次数: {result['iteration_count']}")


def example_simple_interface():
    """简化接口示例"""
    print("\n" + "=" * 60)
    print("示例 2: 简化接口")
    print("=" * 60)
    
    assistant = ResearchAssistant()
    
    # 直接获取报告
    report = assistant.get_report("机器学习模型部署策略")
    print("\n研究报告:")
    print("-" * 60)
    print(report)
    print("-" * 60)


def example_custom_config():
    """自定义配置示例"""
    print("\n" + "=" * 60)
    print("示例 3: 自定义配置")
    print("=" * 60)
    
    assistant = ResearchAssistant(max_iterations=5)
    
    # 使用自定义配置
    config = {
        "configurable": {
            "thread_id": "example-001"
        }
    }
    
    result = assistant.research("微服务架构设计模式", config=config)
    
    print("\n研究结果摘要:")
    print(f"- 主题: {result['topic']}")
    print(f"- 报告长度: {len(result['final_report'])} 字符")
    print(f"- 迭代次数: {result['iteration_count']}")
    print(f"- 搜索结果数: {len(result['search_results'])}")


def example_detailed_analysis():
    """详细分析示例"""
    print("\n" + "=" * 60)
    print("示例 4: 详细分析")
    print("=" * 60)
    
    assistant = ResearchAssistant(max_iterations=3)
    
    result = assistant.research("区块链技术在供应链管理中的应用")
    
    print("\n完整研究过程:")
    print("-" * 60)
    print(f"1. 研究主题: {result['topic']}")
    print(f"\n2. 搜索结果 ({len(result['search_results'])} 条):")
    for i, res in enumerate(result['search_results'][:3], 1):
        print(f"   {i}. {res[:100]}...")
    
    print(f"\n3. 分析结果:")
    print(f"   {result['analysis'][:200]}...")
    
    print(f"\n4. 审核反馈:")
    print(f"   {result['review_feedback'][:200]}...")
    
    print(f"\n5. 最终报告:")
    print(f"   {result['final_report'][:300]}...")
    
    print(f"\n6. 迭代次数: {result['iteration_count']}")
    print("-" * 60)


if __name__ == "__main__":
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请设置: export OPENAI_API_KEY='your-api-key'")
        print("\n继续运行示例（可能会失败）...\n")
    
    # 运行示例
    try:
        example_basic_usage()
        # example_simple_interface()
        # example_custom_config()
        # example_detailed_analysis()
    except Exception as e:
        print(f"\n错误: {e}")
        print("\n请确保:")
        print("1. 已设置 OPENAI_API_KEY 环境变量")
        print("2. 已安装所有依赖: pip install -r requirements.txt")
        print("3. 网络连接正常")