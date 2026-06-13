# fund-agent-base

基于 LLM 的基金行业知识智能体系统，支持基金信息查询、风险分析、合规检查与知识库问答。

## 项目概述

本项目是一个完整的**基金智能问答系统**，后端基于 LangGraph 构建智能体工作流，前端使用 React + Ant Design 构建对话界面。系统内置模拟基金数据库与 RAG 知识库，支持自然语言交互式的基金信息查询与投资分析。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.11+, FastAPI, Uvicorn |
| 智能体框架 | LangChain 0.3.30, LangGraph, LangGraph Checkpoint SQLite |
| LLM | 阿里云 Qwen-max（兼容 OpenAI API） |
| 向量数据库 | ChromaDB |
| 嵌入模型 | BAAI/bge-small-zh-v1.5（HuggingFace） |
| 前端框架 | React 19, TypeScript 5, Vite 8 |
| UI 组件 | Ant Design 6, Zustand（状态管理） |
| 数据校验 | Pydantic, Pydantic-Settings |

## 系统架构

### 后端智能体工作流

用户输入 → 意图识别 → 工具选择 → 数据获取 → 分析计算 → 合规检查 → 回复生成

6 个节点构成的 LangGraph StateGraph：

1. **intent_recognizer** — 识别用户意图（query / analyze / compare / compliance）
2. **tool_selector** — 根据意图匹配合适的工具集
3. **data_fetcher** — 提取基金代码，从模拟数据库获取数据
4. **analyzer** — 计算收益率、夏普比率、最大回撤等分析指标
5. **compliance_checker** — 投资者风险等级（C1-C5）与基金风险等级（R1-R5）匹配检查
6. **response_generator** — LLM 整合上下文生成格式化中文回复

### 内置工具（14 个）

**查询工具：** 基金信息查询、净值查询、排名查询、持仓查询、基金经理查询、基金搜索

**分析工具：** 多基金对比、区间收益率计算、风险分析（夏普比率/最大回撤/波动率）、组合分析（HHI 集中度/行业分布）

**合规工具：** 风险匹配检查、合规内容检查、风险提示书生成

**RAG 工具：** 基于知识库的语义检索问答

### 项目结构

```
fund-agent-base/
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── main.py          # FastAPI 入口（端口 8000）
│   │   ├── config.py         # 配置加载（.env）
│   │   ├── api/              # API 路由（/api/chat, /api/chat/stream）
│   │   ├── agent/            # LangGraph 智能体（state / graph / nodes / router）
│   │   ├── models/           # Pydantic 数据模型
│   │   ├── services/         # 模拟基金数据服务（3 只基金）
│   │   ├── tools/            # 智能体工具函数
│   │   ├── prompts/          # LLM 系统提示词
│   │   ├── rag/              # RAG 实现（嵌入 / 向量存储 / 文档加载）
│   │   └── docs/             # RAG 知识库源文档
│   ├── data/chroma_db/       # 向量数据库持久化
│   ├── requirements.txt
│   └── .env                  # 环境变量配置
├── frontend/                 # TypeScript 前端
│   ├── src/
│   │   ├── App.tsx           # 主应用组件
│   │   ├── components/       # UI 组件
│   │   └── main.tsx          # 入口
│   ├── vite.config.ts        # Vite 配置（/api 代理到 :8000）
│   └── package.json
└── README.md
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- 阿里云 DashScope API Key（或其它兼容 OpenAI 的 API）

### 后端启动

```bash
cd backend

# 创建虚拟环境
conda create -n fund-agent python=3.11
conda activate fund-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
  .env 内容参考 .env.example
# 编辑 .env，填入 API Key 和模型配置

# 启动服务
python -m app.main
# 服务运行在 http://localhost:8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
# 开发服务器运行在 http://localhost:5173
# Vite 自动将 /api 请求代理到后端
```

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/chat` | 非流式聊天 |
| POST | `/api/chat/stream` | 流式聊天（SSE） |
| GET | `/api/agent/graph/mermaid` | 获取智能体流程图（Mermaid） |
| GET | `/api/agent/graph/image` | 获取智能体流程图（PNG） |

## 内置模拟基金数据

| 基金代码 | 名称 | 类型 | 风险等级 |
|----------|------|------|----------|
| 000001 | 华夏成长混合 | 混合型 | 中风险 |
| 005827 | 易方达蓝筹精选混合 | 混合型 | 中高风险 |
| 110011 | 易方达中小盘混合 | 混合型 | 中高风险 |

## 注意事项

- 当前数据为**模拟数据**，不包含真实市场信息
- 前端**尚未对接后端 API**，当前展示的是独立 UI 组件
- 嵌入模型首次运行时会从 HuggingFace 国内镜像（hf-mirror.com）下载
- 如需使用 RAG 功能，需先运行向量库初始化脚本