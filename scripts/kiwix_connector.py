#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urljoin, urlparse
from urllib.request import Request, urlopen

HOST = "0.0.0.0"
PORT = 3003
KIWIX_BASE = "http://127.0.0.1:3002"
CATALOG_URL = f"{KIWIX_BASE}/catalog/v2/entries?count=-1"
SEARCH_URL = f"{KIWIX_BASE}/search?pattern={{pattern}}"


def fetch(url: str, timeout: int = 20) -> tuple[int, str, dict[str, str]]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 KiwixConnector/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", "replace")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, data, headers
    except HTTPError as e:
        data = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        headers = {k.lower(): v for k, v in getattr(e, "headers", {}).items()} if getattr(e, "headers", None) else {}
        return e.code, data, headers


def list_titles() -> list[dict[str, str]]:
    status, body, _ = fetch(CATALOG_URL)
    if status != 200:
        return []
    titles: list[dict[str, str]] = []
    entry_blocks = re.findall(r"<entry>(.*?)</entry>", body, re.S)
    for entry in entry_blocks:
        title_m = re.search(r"<title>(.*?)</title>", entry, re.S)
        link_m = re.search(r'<link[^>]+href="([^"]+)"', entry)
        summary_m = re.search(r"<summary[^>]*>(.*?)</summary>", entry, re.S)
        if not title_m or not link_m:
            continue
        titles.append(
            {
                "title": html.unescape(re.sub(r"\s+", " ", title_m.group(1))).strip(),
                "href": html.unescape(link_m.group(1)).strip(),
                "summary": html.unescape(re.sub(r"\s+", " ", summary_m.group(1))).strip() if summary_m else "",
            }
        )
    return titles


class SearchResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._in_li = False
        self._current = None
        self._text = []
        self._href = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "li":
            self._in_li = True
            self._current = {"title": "", "href": "", "text": ""}
            self._text = []
            self._href = None
        elif self._in_li and tag == "a" and self._href is None:
            self._href = attrs.get("href", "")
            if self._current is not None and not self._current["title"]:
                self._current["title"] = ""

    def handle_endtag(self, tag):
        if self._in_li and tag == "li":
            txt = html.unescape(re.sub(r"\s+", " ", " ".join(self._text))).strip()
            if self._current is not None:
                self._current["text"] = txt
                self._current["href"] = self._href or ""
                if not self._current["title"]:
                    self._current["title"] = txt.split(" from ")[0].strip()
                self.results.append(self._current)
            self._in_li = False
            self._current = None
            self._text = []
            self._href = None

    def handle_data(self, data):
        if not self._in_li:
            return
        s = data.strip()
        if not s:
            return
        self._text.append(s)
        if self._current is not None and not self._current["title"]:
            self._current["title"] = html.unescape(s)


def search(pattern: str, limit: int = 8) -> list[dict[str, str]]:
    url = SEARCH_URL.format(pattern=quote(pattern))
    status, body, _ = fetch(url)
    if status != 200:
        return []
    parser = SearchResultParser()
    parser.feed(body)
    results = []
    for item in parser.results:
        href = item.get("href", "")
        if not href:
            continue
        text = item.get("text", "")
        source = ""
        m = re.search(r"from\s+(.+?)\s+\d[\d,]*\s+words", text)
        if m:
            source = m.group(1).strip()
        words = ""
        wm = re.search(r"(\d[\d,]*)\s+words", text)
        if wm:
            words = wm.group(1)
        results.append(
            {
                "title": item.get("title", "").strip(),
                "url": urljoin(KIWIX_BASE, href),
                "source": source,
                "words": words,
                "snippet": text[:500],
            }
        )
        if len(results) >= limit:
            break
    return results


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", html.unescape(title))).strip().lower()


def search_by_title(pattern: str, limit: int = 8) -> list[dict[str, str]]:
    needle = normalize_title(pattern)
    if not needle:
        return []

    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in search(pattern, limit=max(limit * 5, 20)):
        url = item.get("url", "")
        if not url or url in seen:
            continue
        candidates.append(item)
        seen.add(url)

    for item in list_titles():
        url = item.get("url", "")
        if not url or url in seen:
            continue
        title = item.get("title", "")
        norm = normalize_title(title)
        if norm == needle or norm.startswith(f"{needle} ") or needle in norm:
            candidates.append(item)
            seen.add(url)

    ranked: list[tuple[int, int, dict[str, str]]] = []
    for item in candidates:
        title = item.get("title", "")
        if not title:
            continue
        norm = normalize_title(title)
        if norm == needle:
            bucket = 0
        elif norm.startswith(f"{needle} "):
            bucket = 1
        elif needle in norm:
            bucket = 2
        else:
            bucket = 3
        ranked.append((bucket, len(title), item))

    ranked.sort(key=lambda row: (row[0], row[1], row[2].get("title", "").lower()))
    results: list[dict[str, str]] = []
    seen.clear()
    for _, _, item in ranked:
        url = item.get("url", "")
        if not url or url in seen:
            continue
        results.append(item)
        seen.add(url)
        if len(results) >= limit:
            break

    return results[:limit]


class ArticleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_content = False
        self.depth = 0
        self.text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id") == "mw-content-text":
            self.in_content = True
            self.depth = 1
            return
        if self.in_content:
            self.depth += 1
            if tag in {"script", "style"}:
                self._skip = True

    def handle_endtag(self, tag):
        if self.in_content and tag in {"script", "style"}:
            self._skip = False
        if self.in_content:
            self.depth -= 1
            if self.depth <= 0:
                self.in_content = False

    def handle_data(self, data):
        if self._skip or not self.in_content:
            return
        s = re.sub(r"\s+", " ", data).strip()
        if s:
            self.text.append(s)


def fetch_article(url: str) -> dict[str, str]:
    status, body, _ = fetch(url)
    if status != 200:
        return {"error": f"HTTP {status}", "url": url}
    parser = ArticleTextParser()
    parser.feed(body)
    title_m = re.search(r"<title>(.*?)</title>", body, re.S)
    page_title = html.unescape(re.sub(r"\s+", " ", title_m.group(1))).strip() if title_m else url.rsplit("/", 1)[-1]
    text = "\n".join(parser.text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return {"title": page_title, "url": url, "text": text}


def json_response(handler: BaseHTTPRequestHandler, code: int, payload: dict):
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(data)


def text_response(handler: BaseHTTPRequestHandler, code: int, text: str, content_type: str = "text/plain; charset=utf-8"):
    data = text.encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(data)


OPENAPI = {
    "openapi": "3.1.0",
    "info": {
        "title": "Kiwix Local Wikipedia Connector",
        "version": "1.0.0",
        "description": "Search the local Kiwix mirror and fetch article text from the offline library.",
    },
    "servers": [{"url": f"http://{urlparse(KIWIX_BASE).hostname}:{PORT}"}],
    "paths": {
        "/health": {"get": {"summary": "Health check", "responses": {"200": {"description": "OK"}}}},
        "/search": {
            "get": {
                "summary": "Search the local Kiwix library",
                "parameters": [
                    {"name": "pattern", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "default": 8}},
                ],
                "responses": {"200": {"description": "Search results"}},
            }
        },
        "/search_title": {
            "get": {
                "operationId": "search_title",
                "summary": "Search for an exact or near-exact article title",
                "parameters": [
                    {"name": "pattern", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "default": 8}},
                ],
                "responses": {"200": {"description": "Title-matched search results"}},
            }
        },
        "/lookup": {
            "get": {
                "summary": "Search and return the first matching article text",
                "parameters": [{"name": "pattern", "in": "query", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Article text"}},
            }
        },
        "/page": {
            "get": {
                "summary": "Fetch a specific article by exact Kiwix content URL",
                "parameters": [{"name": "url", "in": "query", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Article text"}},
            }
        },
    },
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        if path == "/health":
            titles = list_titles()
            return json_response(self, 200, {"ok": True, "catalog_titles": len(titles), "kiwix_base": KIWIX_BASE})
        if path == "/openapi.json":
            return json_response(self, 200, OPENAPI)
        if path == "/search":
            pattern = (qs.get("pattern") or [""])[0].strip()
            if not pattern:
                return json_response(self, 400, {"error": "pattern query parameter is required"})
            limit = int((qs.get("limit") or ["8"])[0])
            return json_response(self, 200, {"query": pattern, "results": search(pattern, limit)})
        if path == "/search_title":
            pattern = (qs.get("pattern") or [""])[0].strip()
            if not pattern:
                return json_response(self, 400, {"error": "pattern query parameter is required"})
            limit = int((qs.get("limit") or ["8"])[0])
            return json_response(self, 200, {"query": pattern, "results": search_by_title(pattern, limit)})
        if path == "/lookup":
            pattern = (qs.get("pattern") or [""])[0].strip()
            if not pattern:
                return json_response(self, 400, {"error": "pattern query parameter is required"})
            results = search_by_title(pattern, 1) or search(pattern, 1)
            if not results:
                return json_response(self, 404, {"query": pattern, "results": []})
            article = fetch_article(results[0]["url"])
            return json_response(self, 200, {"query": pattern, "match": results[0], "article": article})
        if path == "/page":
            url = (qs.get("url") or [""])[0].strip()
            if not url:
                return json_response(self, 400, {"error": "url query parameter is required"})
            return json_response(self, 200, {"article": fetch_article(url)})
        if path == "/":
            return text_response(self, 200, "Kiwix Local Wikipedia Connector\nUse /health, /search?pattern=..., /search_title?pattern=..., /lookup?pattern=..., /openapi.json\n")
        return json_response(self, 404, {"error": "not found", "path": path})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving Kiwix connector on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
