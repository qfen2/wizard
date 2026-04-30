# 安装依赖说明

## 问题说明

在使用知识库服务时，遇到了以下问题：

1. **Chroma 已弃用警告**：`langchain_community.vectorstores.Chroma` 已被弃用
2. **无效的模型 ID**：`text-embedding-3-small` 模型不可用

## 解决方案

### 1. 安装新的 Chroma 包

```bash
pip install langchain-chroma
```

### 2. 更新 requirements.txt

将以下依赖添加到 `requirements.txt`：

```
langchain-chroma>=0.1.0
```

### 3. 配置嵌入模型

在 `conf/auto.yaml` 中配置嵌入模型：

#### 使用 OpenAI API
```yaml
llm:
  openai:
    api_key: your-openai-api-key
    base_url: https://api.openai.com/v1
    embedding_model: text-embedding-ada-002
```

#### 使用 ModelScope API
```yaml
llm:
  modelscope:
    api_key: ms-your-api-key
    base_url: https://api-inference.modelscope.cn/v1
    embedding_model: Qwen/Qwen3-Embedding-8B
```

### 4. 环境变量设置

也可以通过环境变量设置：

```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

## 验证安装

运行测试脚本验证修复：

```bash
python test_knowledge_base.py
```

## 支持的嵌入模型

### OpenAI 官方模型
- `text-embedding-ada-002`
- `text-embedding-3-small`
- `text-embedding-3-large`

### ModelScope 模型
- `Qwen/Qwen3-Embedding-8B`
- `BAAI/bge-large-zh-v1.5`
- `BAAI/bge-base-zh-v1.5`

### 其他兼容 API
- 任何兼容 OpenAI Embeddings API 的服务

## 故障排除

### 问题：仍然看到 Chroma 弃用警告

**解决**：确保安装了 `langchain-chroma` 包
```bash
pip install langchain-chroma --upgrade
```

### 问题：嵌入模型无效

**解决**：
1. 检查 API 密钥是否正确
2. 确认 API 端点可访问
3. 尝试使用 `text-embedding-ada-002` 作为默认模型

### 问题：向量存储创建失败

**解决**：
1. 检查磁盘空间
2. 确保有目录写入权限
3. 查看详细错误日志

## 代码变更

已修复的文件：
- `app/services/knowledge_base_service.py`
  - 更新 Chroma 导入：`from langchain_chroma import Chroma`
  - 修复嵌入模型配置
  - 添加错误处理和降级方案

## 最佳实践

1. **始终使用配置文件**：在 `conf/auto.yaml` 中配置模型
2. **测试环境变量**：先在测试环境验证配置
3. **监控 API 使用**：跟踪嵌入 API 的使用量
4. **缓存嵌入结果**：对于相同的文本，缓存嵌入结果以减少 API 调用