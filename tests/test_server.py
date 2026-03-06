import astrace.server as server


def test_research_health_reports_stateless_default(monkeypatch):
    monkeypatch.delenv("ASTRACE_STATELESS_HTTP", raising=False)

    payload = server.research_health()

    assert payload["stateless_http"] is True


def test_run_server_uses_stateless_http_by_default(monkeypatch):
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)

    monkeypatch.delenv("ASTRACE_STATELESS_HTTP", raising=False)
    monkeypatch.setattr(server.MCP, "run", fake_run)

    server.run_server()

    assert captured["transport"] == "streamable-http"
    assert captured["stateless_http"] is True


def test_run_server_respects_stateless_http_override(monkeypatch):
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)

    monkeypatch.setenv("ASTRACE_STATELESS_HTTP", "false")
    monkeypatch.setattr(server.MCP, "run", fake_run)

    server.run_server()

    assert captured["stateless_http"] is False
