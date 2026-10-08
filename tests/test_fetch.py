import fetch_companies


class FakeResponse:
    """Stands in for a real API response, so tests never call the internet."""

    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def fake_get(responses):
    """Replace requests.get with one that replies with each response in turn."""
    replies = iter(responses)

    def _get(*args, **kwargs):
        return next(replies)

    return _get


def test_returns_data_on_success(monkeypatch):
    monkeypatch.setattr(fetch_companies.requests, "get",
                        fake_get([FakeResponse(200, {"company_name": "TEST LTD"})]))
    assert fetch_companies.get_company("12345678") == {"company_name": "TEST LTD"}


def test_returns_none_when_not_found(monkeypatch):
    monkeypatch.setattr(fetch_companies.requests, "get", fake_get([FakeResponse(404)]))
    assert fetch_companies.get_company("99999999") is None


def test_retries_after_server_error(monkeypatch):
    monkeypatch.setattr(fetch_companies.time, "sleep", lambda seconds: None)  # don't really wait
    monkeypatch.setattr(fetch_companies.requests, "get",
                        fake_get([FakeResponse(500), FakeResponse(200, {"company_name": "TEST LTD"})]))
    assert fetch_companies.get_company("12345678") == {"company_name": "TEST LTD"}