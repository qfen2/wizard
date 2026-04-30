# coding: utf-8
"""
快速修复脚本 - 安装缺失的依赖并验证配置
"""

import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"执行命令: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✓ 成功")
            if result.stdout:
                print(result.stdout)
        else:
            print("✗ 失败")
            if result.stderr:
                print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("✗ 超时")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def main():
    print("=" * 60)
    print("知识库服务依赖修复工具")
    print("=" * 60)
    
    # 1. 安装 langchain-chroma
    success = run_command(
        "pip install langchain-chroma --upgrade",
        "1. 安装 langchain-chroma 包"
    )
    
    if not success:
        print("\n⚠ 警告: langchain-chroma 安装失败，将继续...")
    
    # 2. 验证 Python 版本
    print(f"\n{'='*60}")
    print("2. Python 版本")
    print(f"{'='*60}")
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("✗ Python 版本过低，需要 3.8+")
        return False
    else:
        print("✓ Python 版本符合要求")
    
    # 3. 检查已安装的关键包
    print(f"\n{'='*60}")
    print("3. 检查关键依赖包")
    print(f"{'='*60}")
    
    packages = [
        'langchain',
        'langchain-core',
        'langchain-openai',
        'langchain-community',
        'langchain-chroma',
        'chromadb',
        'openai',
    ]
    
    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # 提取版本信息
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        version = line.split(':')[1].strip()
                        print(f"✓ {package}: {version}")
                        break
            else:
                print(f"✗ {package}: 未安装")
        except Exception as e:
            print(f"✗ {package}: 检查失败 ({e})")
    
    # 4. 测试导入
    print(f"\n{'='*60}")
    print("4. 测试关键模块导入")
    print(f"{'='*60}")
    
    imports = [
        ("langchain_chroma", "from langchain_chroma import Chroma"),
        ("langchain_openai", "from langchain_openai import OpenAIEmbeddings"),
        ("langchain_core", "from langchain_core.prompts import ChatPromptTemplate"),
    ]
    
    for name, import_cmd in imports:
        try:
            exec(import_cmd)
            print(f"✓ {name} 导入成功")
        except ImportError as e:
            print(f"✗ {name} 导入失败: {e}")
    
    # 5. 检查配置文件
    print(f"\n{'='*60}")
    print("5. 检查配置文件")
    print(f"{'='*60}")
    
    config_files = [
        "conf/auto.yaml",
        "config.py"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✓ {config_file} 存在")
        else:
            print(f"✗ {config_file} 不存在")
    
    # 6. 验证知识库服务
    print(f"\n{'='*60}")
    print("6. 测试知识库服务")
    print(f"{'='*60}")
    
    try:
        from app.services.knowledge_base_service import KnowledgeBaseService
        print("✓ 知识库服务导入成功")
        
        # 创建服务实例
        kb = KnowledgeBaseService(persist_directory="./test_vector_store")
        print("✓ 知识库服务实例创建成功")
        
    except Exception as e:
        print(f"✗ 知识库服务测试失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查 API 密钥配置")
        print("2. 确认网络连接正常")
        print("3. 查看详细错误信息")
    
    # 7. 提供后续步骤
    print(f"\n{'='*60}")
    print("修复完成！后续步骤")
    print(f"{'='*60}")
    
    print("""
1. 配置 API 密钥:
   编辑 conf/auto.yaml，设置正确的 API 密钥
   
2. 运行测试:
   python test_knowledge_base.py
   
3. 运行演示:
   python demo_knowledge_base.py
   
4. 查看文档:
   - INSTALL_DEPS.md - 依赖安装说明
   - app/utils/langchain_langgraph/ENTERPRISE_AI_GUIDE.md - 完整使用指南
    """)
    
    print("\n" + "=" * 60)
    print("所有检查完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()