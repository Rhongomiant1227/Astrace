# Astrace

Language / 语言: [简体中文](README.md) | **English**

Astrace is an MCP research service for **AstrBot + NapCat** scenarios.

It can be used in two ways:
- As an **MCP backend for AstrBot** (AstrBot official repo: <https://github.com/AstrBotDevs/AstrBot>)
- As a **standalone MCP server** for any MCP-compatible client

## Name Origin

`Astrace = AstrBot + Trace`

- `Astr`: from the AstrBot ecosystem, focused on bot and plugin workflows
- `Trace`: emphasizes traceable research steps and evidence-chain output

## Core Features

- Research depth control: `auto` / `shallow` / `deep`
- Traceable outputs: findings, evidence sources, iteration traces
- Async tasks for long-running research jobs
- Cross-platform core: shared Python code for Windows/Linux
- Docker deployment support

## Usage Modes

1. AstrBot integration (recommended)
- Connect Astrace endpoint in AstrBot MCP settings
- Template: `examples/astrbot_mcp_servers.example.json`
- AstrBot docs: <https://docs.astrbot.app/>

2. Standalone mode
- Run Astrace directly
- Connect MCP endpoint: `http://127.0.0.1:8788/mcp`

## Exposed Tools

- `research(topic, mode, max_iterations, max_pages, max_results_per_query, include_raw_text)`
- `start_research(...)`
- `get_research_status(task_id)`
- `get_research_result(task_id)`
- `research_health()`

## Runtime Environment Variables

- `MCP_HOST` (default `0.0.0.0`)
- `MCP_PORT` (default `8788`)
- `SEARCH_MAX_RESULTS` (default `8`)
- `REQUEST_TIMEOUT` (default `15`)
- `MAX_TEXT_CHARS` (default `12000`)
- `ASTRACE_TASK_WORKERS` (default `2`)

## Windows (Primary Path)

```powershell
cd Astrace
.\scripts\windows\setup.ps1
.\scripts\windows\test.ps1
.\scripts\windows\start.ps1
```

Default MCP endpoint:
- `http://127.0.0.1:8788/mcp`

## Linux

```bash
cd Astrace
chmod +x scripts/linux/*.sh
./scripts/linux/setup.sh
./scripts/linux/test.sh
./scripts/linux/start.sh
```

Default MCP endpoint:
- `http://127.0.0.1:8788/mcp`

## Docker

```bash
cd Astrace
cp docker/.env.example docker/.env
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml logs -f astrace
```

Host endpoint:
- `http://127.0.0.1:8788/mcp`

If AstrBot runs on the same Docker network, use service name:
- `http://astrace:8788/mcp`

## AstrBot MCP Mapping

Template:
- `examples/astrbot_mcp_servers.example.json`

Typical mapping (schema may vary by AstrBot version):
- `transport`: `streamable_http`
- `url`: `http://127.0.0.1:8788/mcp` (or Docker service URL)
- `headers`: optional

## Tests

Windows:
```powershell
.\scripts\windows\test.ps1
```

Linux:
```bash
./scripts/linux/test.sh
```

## Project Layout

- `astrace/`: shared core
- `scripts/windows/`: Windows one-click scripts
- `scripts/linux/`: Linux one-click scripts
- `docker/`: Dockerfile + compose + env template
- `examples/`: AstrBot MCP config template
