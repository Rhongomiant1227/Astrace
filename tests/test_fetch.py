import httpx

from astrace.fetch import WebFetcher


class _StubResponse:
    def __init__(self, url: str, status_code: int, text: str) -> None:
        self.url = url
        self.status_code = status_code
        self.text = text
        self._request = httpx.Request("GET", url)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code} error",
                request=self._request,
                response=httpx.Response(
                    status_code=self.status_code,
                    request=self._request,
                    text=self.text,
                ),
            )


class _StubClient:
    def __init__(self, ddg_text: str, bing_text: str) -> None:
        self.ddg_text = ddg_text
        self.bing_text = bing_text
        self.calls: list[str] = []

    def get(self, url: str, params: dict | None = None) -> _StubResponse:
        self.calls.append(url)
        if "duckduckgo.com" in url:
            return _StubResponse(url=url, status_code=202, text=self.ddg_text)
        if "bing.com" in url:
            return _StubResponse(url=url, status_code=200, text=self.bing_text)
        return _StubResponse(url=url, status_code=404, text="")

    def close(self) -> None:
        return None


def test_search_falls_back_to_bing_when_ddg_has_no_results():
    fetcher = WebFetcher(search_backends=("ddg", "bing"))
    fetcher.client = _StubClient(
        ddg_text="<html><body><div>challenge page</div></body></html>",
        bing_text=(
            "<html><body>"
            "<li class='b_algo'>"
            "<h2><a href='https://example.com/a'>Example A</a></h2>"
            "<div class='b_caption'><p>Result A snippet</p></div>"
            "</li>"
            "</body></html>"
        ),
    )

    results = fetcher.search("astrbot mcp", max_results=3)

    assert len(results) == 1
    assert results[0].url == "https://example.com/a"
    assert results[0].title == "Example A"


def test_search_stops_after_first_backend_if_limit_hit():
    fetcher = WebFetcher(search_backends=("ddg", "bing"))
    fetcher.client = _StubClient(
        ddg_text=(
            "<html><body>"
            "<div class='result'>"
            "<a class='result__a' href='https://example.com/ddg'>DDG Result</a>"
            "<a class='result__snippet'>DDG snippet</a>"
            "</div>"
            "</body></html>"
        ),
        bing_text=(
            "<html><body>"
            "<li class='b_algo'>"
            "<h2><a href='https://example.com/bing'>Bing Result</a></h2>"
            "<div class='b_caption'><p>Bing snippet</p></div>"
            "</li>"
            "</body></html>"
        ),
    )

    results = fetcher.search("astrbot mcp", max_results=1)

    assert len(results) == 1
    assert results[0].url == "https://example.com/ddg"
    assert fetcher.client.calls == ["https://html.duckduckgo.com/html/"]
