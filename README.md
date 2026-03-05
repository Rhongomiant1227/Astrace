# Astrace

Language: **English** | [简体中文](README.zh-CN.md)

Astrace is an MCP research server designed for **AstrBot + NapCat** scenarios.

Core goals:
- Provide a stable research capability layer for QQ bot workflows.
- Keep one shared Python codebase across Windows/Linux.
- Support deployment as local process or Docker service.
- Let the model choose research depth: `auto`, `shallow`, `deep`.

## Why Astrace

Plain search tools are often too shallow for plugin ecosystems and large-topic investigation.
Astrace exposes a traceable pipeline:

1. Query planning
2. Multi-source search
3. Web extraction
4. Iterative expansion (deep mode)
5. Structured report with findings and source references

This makes it easier to build a "compatibility layer + research layer" for AstrBot/NapCat.

## Tools Exposed

- `research(topic, mode, max_iterations, max_pages, max_results_per_query, include_raw_text)`
- `start_research(...)`
- `get_research_status(task_id)`
- `get_research_result(task_id)`
- `research_health()`

`mode` behavior:
- `auto`: planner decides deep or shallow.
- `shallow`: single-pass, low-latency lookup.
- `deep`: iterative expansion for broad or comparative research.

## Runtime Environment Variables

- `MCP_HOST` (default `0.0.0.0`)
- `MCP_PORT` (default `8788`)
- `SEARCH_MAX_RESULTS` (default `8`)
- `REQUEST_TIMEOUT` (default `15`)
- `MAX_TEXT_CHARS` (default `12000`)
- `ASTRACE_TASK_WORKERS` (default `2`)

## Windows (First-Class Path)

```powershell
cd Astrace
.\scripts\windows\setup.ps1
.\scripts\windows\test.ps1
.\scripts\windows\start.ps1
```

Server endpoint:
- `http://127.0.0.1:8788/mcp`

## Linux

```bash
cd Astrace
chmod +x scripts/linux/*.sh
./scripts/linux/setup.sh
./scripts/linux/test.sh
./scripts/linux/start.sh
```

Server endpoint:
- `http://127.0.0.1:8788/mcp`

## Docker

```bash
cd Astrace
cp docker/.env.example docker/.env
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml logs -f astrace
```

Server endpoint (host):
- `http://127.0.0.1:8788/mcp`

If AstrBot runs in another container on the same network, use the service name:
- `http://astrace:8788/mcp`

## AstrBot MCP Integration

Template file:
- `examples/astrbot_mcp_servers.example.json`

Typical mapping (field names vary by AstrBot version):
- `transport`: `streamable_http`
- `url`: `http://127.0.0.1:8788/mcp` (or Docker service URL)
- `headers`: optional custom headers

If your AstrBot build has a different schema, keep the same endpoint/transport semantics and map keys accordingly.

## Testing

Windows:
```powershell
.\scripts\windows\test.ps1
```

Linux:
```bash
./scripts/linux/test.sh
```

Both include:
- deterministic self-test (`python -m astrace.server --self-test`)
- unit tests (`pytest -q`)

## File Layout

- `astrace/` shared core (Windows/Linux/Docker all use this)
- `scripts/windows/` Windows bootstrap/start/test
- `scripts/linux/` Linux bootstrap/start/test
- `docker/` Dockerfile + compose + env template
- `examples/` AstrBot MCP config template
