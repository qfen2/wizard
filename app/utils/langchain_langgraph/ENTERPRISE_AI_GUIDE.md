# 企业级 LangChain AI 平台 - 使用指南

## 概述

本项目实现了一个完整的企业级 AI 平台，包含以下五大核心功能：

1. **企业知识库与 RAG 系统** - 文档管理、向量化存储、智能检索
2. **多智能体协作系统** - 客服、审批、数据分析等专用智能体
3. **智能客服与业务流程自动化** - 会话管理、意图识别、流程编排
4. **数据分析与报告生成** - 数据提取、分析、可视化、报告生成
5. **安全与权限控制** - 基于角色的访问控制、API鉴权、数据脱敏

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

确保已安装以下新增依赖：
- `chromadb` - 向量数据库
- `pandas` - 数据分析
- `openpyxl` - Excel文件支持

### 2. 配置环境变量

在 `config.py` 或环境变量中配置：

```python
LLM = {
    'openai': {
        'api_key': 'your-openai-api-key',
        'base_url': 'https://api.openai.com/v1',
        'model_name': 'gpt-4o-mini'
    }
}
```

### 3. 启动服务

```bash
python run.py
```

服务将在 `http://127.0.0.1:5005` 启动。

## API 接口文档

### 知识库相关

#### 上传文档

```bash
POST /ai/upload_document
Content-Type: application/json

{
  "file_path": "/path/to/document.pdf",
  "collection_name": "manuals",
  "metadata": {
    "category": "产品手册",
    "department": "技术部"
  }
}
```

#### 搜索知识库

```bash
POST /ai/search_knowledge
Content-Type: application/json

{
  "query": "如何连接网络",
  "collection_name": "manuals",
  "k": 3
}
```

#### 向知识库提问

```bash
POST /ai/ask_knowledge
Content-Type: application/json

{
  "question": "如何清理传感器？",
  "collection_name": "manuals"
}
```

#### 列出文档

```bash
POST /ai/list_documents
Content-Type: application/json

{
  "collection_name": "manuals"
}
```

### 智能体相关

#### 客服智能体对话

```bash
POST /ai/customer_service_chat
Content-Type: application/json

{
  "user_id": "user123",
  "query": "我的订单什么时候能发货？"
}
```

#### 审批请求处理

```bash
POST /ai/approval_request
Content-Type: application/json

{
  "request_id": "req001",
  "request_type": "expense",
  "request_data": "申请报销差旅费 3000 元",
  "requester": "张三"
}
```

#### 数据分析

```bash
POST /ai/data_analysis
Content-Type: application/json

{
  "analysis_task": "分析2024年Q1销售趋势",
  "data_source": "sales_database"
}
```

### 工作流相关

#### 处理用户消息（智能路由）

```bash
POST /ai/process_message
Content-Type: application/json

{
  "user_id": "user123",
  "message": "如何申请退款？",
  "session_id": "optional-session-id",
  "context": {
    "department": "客服部"
  }
}
```

#### 获取会话历史

```bash
POST /ai/get_session_history
Content-Type: application/json

{
  "session_id": "session-uuid"
}
```

#### 关闭会话

```bash
POST /ai/close_session
Content-Type: application/json

{
  "session_id": "session-uuid"
}
```

### 报告相关

#### 生成数据分析报告

```bash
POST /ai/generate_report
Content-Type: application/json

{
  "data_type": "sales",
  "report_type": "销售分析",
  "query": "SELECT * FROM sales WHERE date >= '2024-01-01'"
}
```

#### 快速数据分析

```bash
POST /ai/quick_analysis
Content-Type: application/json

{
  "data_source": "/path/to/data.csv",
  "columns": ["sales", "profit", "region"]
}
```

### 安全相关

#### 用户登录

```bash
POST /ai/login
Content-Type: application/json

{
  "user_id": "user123",
  "password": "password123"
}
```

返回：
```json
{
  "success": true,
  "token": "access-token-here",
  "role": "employee",
  "expires_in": 3600
}
```

#### 用户登出

```bash
POST /ai/logout
Content-Type: application/json

{
  "token": "access-token-here"
}
```

#### 检查访问权限

```bash
POST /ai/check_access
Content-Type: application/json

{
  "token": "access-token-here",
  "permission": "access_data_analysis"
}
```

#### 脱敏敏感数据

```bash
POST /ai/mask_data
Content-Type: application/json

{
  "data": {
    "name": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com"
  },
  "fields": ["phone", "email"]
}
```

返回：
```json
{
  "masked_data": {
    "name": "张三",
    "phone": "138****8000",
    "email": "zh***@example.com"
  }
}
```

#### 分配用户角色

```bash
POST /ai/assign_role
Content-Type: application/json

{
  "user_id": "user123",
  "role": "manager"
}
```

## 编程接口使用

### 1. 知识库服务

```python
from app.services.knowledge_base_service import KnowledgeBaseService

# 创建服务实例
kb_service = KnowledgeBaseService(persist_directory="./data/vector_store")

# 上传文档
result = kb_service.upload_document(
    file_path="path/to/document.pdf",
    collection_name="manuals",
    metadata={"category": "产品手册"}
)

# 搜索
results = kb_service.search(
    query="如何连接网络",
    collection_name="manuals",
    k=3
)

# 问答
qa_result = kb_service.ask(
    question="如何清理传感器？",
    collection_name="manuals"
)
```

### 2. 智能体服务

```python
from app.services.enterprise_agents import (
    CustomerServiceAgent,
    ApprovalAgent,
    DataAnalysisAgent
)

# 客服智能体
cs_agent = CustomerServiceAgent()
result = cs_agent.chat(
    user_id="user123",
    query="我的订单什么时候能发货？"
)

# 审批智能体
approval_agent = ApprovalAgent()
result = approval_agent.approve_request(
    request_id="req001",
    request_type="expense",
    request_data="申请报销差旅费 3000 元",
    requester="张三"
)

# 数据分析智能体
analysis_agent = DataAnalysisAgent()
result = analysis_agent.analyze(
    analysis_task="分析2024年Q1销售趋势",
    data_source="sales_database"
)
```

### 3. 工作流服务

```python
from app.services.workflow_service import WorkflowOrchestrator

# 创建流程编排器
orchestrator = WorkflowOrchestrator()

# 处理消息（自动路由到合适的智能体）
result = orchestrator.process_message(
    user_id="user123",
    message="如何申请退款？"
)

# 获取会话历史
history = orchestrator.get_session_history(result['session_id'])

# 关闭会话
orchestrator.close_session(result['session_id'])
```

### 4. 报告服务

```python
from app.services.report_service import DataAnalysisService

# 创建报告服务
report_service = DataAnalysisService()

# 生成完整报告
result = report_service.analyze_report(
    data_type='sales',
    report_type='销售分析'
)

# 快速分析
quick_result = report_service.quick_analysis(
    data_source="data.csv",
    columns=['sales', 'profit']
)
```

### 5. 安全服务

```python
from app.services.security_service import SecurityService, Permission

# 创建安全服务
security = SecurityService()

# 用户登录
login_result = security.login("user123", "password123")
token = login_result['token']

# 检查权限
access_result = security.check_access(
    token=token,
    permission=Permission.ACCESS_DATA_ANALYSIS
)

# 脱敏数据
masked_data = security.mask_sensitive_data(
    data={
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com"
    }
)
```

## 权限系统

### 角色定义

- `admin` - 管理员：所有权限
- `manager` - 经理：部门权限
- `employee` - 员工：基础权限
- `guest` - 访客：只读权限

### 权限列表

| 权限名称 | 描述 |
|---------|------|
| `access_customer_service` | 访问客服智能体 |
| `access_approval` | 访问审批智能体 |
| `access_data_analysis` | 访问数据分析智能体 |
| `view_knowledge_base` | 查看知识库 |
| `upload_document` | 上传文档 |
| `delete_document` | 删除文档 |
| `export_data` | 导出数据 |
| `manage_users` | 管理用户 |

## 支持的文件类型

知识库支持以下文件类型：

- `.pdf` - PDF文档
- `.docx`, `.doc` - Word文档
- `.md`, `.markdown` - Markdown文档
- `.xlsx`, `.xls` - Excel文档
- `.txt` - 文本文件

## 部署说明

### 开发环境

```bash
python run.py
```

### 生产环境

使用 Gunicorn + Supervisor：

```bash
# 安装依赖
pip install gunicorn supervisor

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5005 run:app
```

或使用 Supervisor 配置文件：

```bash
supervisord -c conf/supervisor_wizard.conf
```

## 注意事项

1. **API 密钥安全**: 不要将 API 密钥提交到版本控制系统
2. **数据备份**: 定期备份向量数据库和关系数据库
3. **性能优化**: 对于大规模数据，建议使用专业的向量数据库（如 Milvus、Pinecone）
4. **监控日志**: 启用日志记录和监控，便于问题排查
5. **权限管理**: 定期审查用户权限，确保最小权限原则

## 扩展开发

### 添加新的智能体

1. 在 `app/services/enterprise_agents.py` 中定义新的智能体类
2. 在 `app/services/workflow_service.py` 中注册智能体
3. 在 `app/views/ai_views.py` 中添加 API 接口

### 添加新的工具

在 `app/utils/langchain_langgraph/common_tools/` 中创建新的工具文件。

### 自定义权限

在 `app/services/security_service.py` 中添加新的权限定义和角色映射。

## 故障排除

### 常见问题

1. **向量数据库初始化失败**
   - 检查磁盘空间
   - 确保目录有写入权限

2. **OpenAI API 调用失败**
   - 检查 API 密钥是否正确
   - 确认账户有足够的额度

3. **文档上传失败**
   - 检查文件路径是否正确
   - 确认文件类型是否支持

4. **权限检查失败**
   - 确认用户角色已正确设置
   - 检查 token 是否有效

## 技术支持

如有问题，请查看：
- 项目 README.md
- LangChain 官方文档
- LangGraph 官方文档

## 更新日志

### v1.0.0 (2026-03-04)

- 实现企业知识库与 RAG 系统
- 实现多智能体协作系统
- 实现智能客服与业务流程自动化
- 实现数据分析与报告生成
- 实现安全与权限控制
- 提供 REST API 接口