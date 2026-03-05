# Astrace

语言 / Language: **简体中文** | [English](README.en.md)

Astrace 是一个面向 **AstrBot + NapCat** 场景的 MCP 调研服务。

它既可以：
- 作为 **AstrBot 的 MCP 服务** 使用（AstrBot 原项目：<https://github.com/AstrBotDevs/AstrBot>）
- 也可以 **独立部署并单独使用**，作为通用 MCP Research Server

## 名字由来

`Astrace = AstrBot + Trace`

- `Astr`：来自 AstrBot 生态，强调面向机器人与插件场景
- `Trace`：强调可追踪（traceable）的调研过程和证据链输出

## 核心能力

- 调研深度控制：`auto` / `shallow` / `deep`
- 结构化输出：结论、证据来源、迭代轨迹
- 异步任务：支持长时调研任务的启动、查询状态和取回结果
- 跨平台：Windows / Linux 共用一套 Python 核心
- 容器化：支持 Docker 一键部署

## 适配场景

1. AstrBot 集成场景（推荐）
- 在 AstrBot 的 MCP 配置中接入 Astrace 服务地址
- 模板文件：`examples/astrbot_mcp_servers.example.json`
- AstrBot 文档：<https://docs.astrbot.app/>

2. 独立使用场景
- 直接启动 Astrace MCP 服务
- 在任何支持 MCP 的客户端中接入 `http://127.0.0.1:8788/mcp`

## 暴露工具

- `research(topic, mode, max_iterations, max_pages, max_results_per_query, include_raw_text)`
- `start_research(...)`
- `get_research_status(task_id)`
- `get_research_result(task_id)`
- `research_health()`

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

默认 MCP 地址：
- `http://127.0.0.1:8788/mcp`

## Linux

```bash
cd Astrace
chmod +x scripts/linux/*.sh
./scripts/linux/setup.sh
./scripts/linux/test.sh
./scripts/linux/start.sh
```

默认 MCP 地址：
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

如果 AstrBot 在同一 Docker 网络内运行，建议使用服务名：
- `http://astrace:8788/mcp`

## AstrBot MCP 接入说明

参考模板：
- `examples/astrbot_mcp_servers.example.json`

常见映射（不同 AstrBot 版本字段名可能有差异）：
- `transport`: `streamable_http`
- `url`: `http://127.0.0.1:8788/mcp`（或 Docker 服务地址）
- `headers`: 可选

## 测试

Windows：
```powershell
.\scripts\windows\test.ps1
```

Linux：
```bash
./scripts/linux/test.sh
```

## 项目结构

- `astrace/`：共享核心
- `scripts/windows/`：Windows 一键脚本
- `scripts/linux/`：Linux 一键脚本
- `docker/`：Dockerfile + compose + env 模板
- `examples/`：AstrBot MCP 配置模板
