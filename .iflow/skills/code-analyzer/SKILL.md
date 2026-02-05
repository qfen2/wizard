# Code Analyzer

## Description
这是一个用于分析代码结构和质量的技能，可以帮助开发者快速理解代码逻辑、发现潜在问题、优化代码结构。

## Usage Scenarios
- 需要理解新项目的代码结构
- 查找代码中的潜在bug或性能问题
- 分析代码的复杂度和可维护性
- 生成代码文档或注释
- 重构前的代码审查

## Implementation

### Trigger Conditions
当用户询问以下类型的问题时自动触发：
- "分析这个文件"
- "解释这段代码"
- "找出代码问题"
- "代码审查"
- "代码结构分析"
- "analyze this file"
- "explain this code"
- "find issues in code"
- "code review"
- "code structure analysis"

### Analysis Steps
1. **文件识别**：识别用户指定的代码文件或目录
2. **代码解析**：读取并解析代码内容
3. **结构分析**：
   - 识别类、函数、变量的定义和关系
   - 分析模块依赖关系
   - 检测代码重复和复杂度
4. **问题检测**：
   - 潜在的bug
   - 性能问题
   - 安全隐患
   - 代码规范问题
5. **报告生成**：生成清晰的分析报告，包括：
   - 代码结构概览
   - 发现的问题列表
   - 改进建议
   - 相关代码片段和行号

### Output Format
```markdown
## 代码分析报告

### 文件信息
- 文件路径：...
- 代码行数：...

### 结构概览
- 主要类：...
- 主要函数：...

### 发现的问题
1. [严重性] 问题描述
   - 位置：文件名:行号
   - 建议：...

### 改进建议
- ...
```

### Tools Usage
- 使用 `read_file` 读取代码文件
- 使用 `search_file_content` 查找特定模式
- 使用 `glob` 查找相关文件
- 使用 `list_directory` 分析目录结构