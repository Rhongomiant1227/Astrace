# Astrace

语言： [English](README.md) | **简体中文**

Astrace 是一个面向 **AstrBot + NapCat** 场景的 MCP 调研服务器。

核心目标：
- 提供稳定的调研能力层，服务 QQ 机器人工作流。
- Windows / Linux 共用同一套 Python 核心代码。
- 同时支持本地进程部署与 Docker 部署。
- 支持由模型决定调研深度：`auto`、`shallow`、`deep`。

## 为什么是 Astrace

普通搜索工具在插件生态和复杂话题调研中通常不够用。  
Astrace 暴露的是一条可追踪流程：

1. 查询规划
2. 多源搜索
3. 网页抽取
4. 迭代扩展（deep 模式）
5. 结构化报告（结论 + 来源）

这使得你可以更容易构建 “兼容层 + 调研层” 的 AstrBot/NapCat 能力栈。

## 暴露工具

- `research(topic, mode, max_iterations, max_pages, max_results_per_query, include_raw_text)`
- `start_research(...)`
- `get_research_status(task_id)`
- `get_research_result(task_id)`
- `research_health()`

`mode` 行为：
- `auto`：由规划器决定 shallow/deep。
- `shallow`：单轮低延迟查询。
- `deep`：多轮迭代扩展，适合广泛调研和对比分析。

## 运行环境变量

- `MCP_HOST`（默认 `0.0.0.0`）
- `MCP_PORT`（默认 `8788`）
- `SEARCH_MAX_RESULTS`（默认 `8`）
- `REQUEST_TIMEOUT`（默认 `15`）
- `MAX_TEXT_CHARS`（默认 `12000`）
- `ASTRACE_TASK_WORKERS`（默认 `2`）

## Windows（优先路径）

```powershell
cd Astrace
.\scripts\windows\setup.ps1
.\scripts\windows\test.ps1
.\scripts\windows\start.ps1
```

服务地址：
- `http://127.0.0.1:8788/mcp`

## Linux

```bash
cd Astrace
chmod +x scripts/linux/*.sh
./scripts/linux/setup.sh
./scripts/linux/test.sh
./scripts/linux/start.sh
```

服务地址：
- `http://127.0.0.1:8788/mcp`

## Docker

```bash
cd Astrace
cp docker/.env.example docker/.env
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml logs -f astrace
```

主机访问地址：
- `http://127.0.0.1:8788/mcp`

如果 AstrBot 在同一 Docker 网络内运行，可用服务名：
- `http://astrace:8788/mcp`

## AstrBot MCP 接入

模板文件：
- `examples/astrbot_mcp_servers.example.json`

常见映射（具体字段名可能因 AstrBot 版本不同）：
- `transport`: `streamable_http`
- `url`: `http://127.0.0.1:8788/mcp`（或 Docker 服务地址）
- `headers`: 可选自定义请求头

如果你的 AstrBot 使用其他配置 schema，保持 endpoint 与 transport 语义一致，按你的 schema 映射字段即可。

## 测试

Windows：
```powershell
.\scripts\windows\test.ps1
```

Linux：
```bash
./scripts/linux/test.sh
```

两者都会执行：
- 确定性自检（`python -m astrace.server --self-test`）
- 单元测试（`pytest -q`）

## 项目结构

- `astrace/`：共享核心（Windows/Linux/Docker 全部复用）
- `scripts/windows/`：Windows 一键部署/启动/测试脚本
- `scripts/linux/`：Linux 一键部署/启动/测试脚本
- `docker/`：Dockerfile + compose + 环境变量模板
- `examples/`：AstrBot MCP 配置模板
