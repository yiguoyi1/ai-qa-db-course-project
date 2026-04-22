from dataclasses import dataclass
import json
from typing import Any
from urllib import error, parse, request


class APIClientError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass
class APIClient:
    base_url: str
    timeout_seconds: int = 30
    access_token: str | None = None

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = self._build_query(params)
        req = request.Request(
            url=f"{self.base_url}{path}{query}",
            headers=self._build_headers(),
            method="GET",
        )
        return self._send(req)

    def post(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        query = self._build_query(params)
        data = None
        headers = self._build_headers()
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        req = request.Request(
            url=f"{self.base_url}{path}{query}",
            data=data,
            headers=headers,
            method="POST",
        )
        return self._send(req)

    def delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = self._build_query(params)
        req = request.Request(
            url=f"{self.base_url}{path}{query}",
            headers=self._build_headers(),
            method="DELETE",
        )
        return self._send(req)

    @staticmethod
    def _build_query(params: dict[str, Any] | None) -> str:
        if not params:
            return ""
        filtered_params = {key: value for key, value in params.items() if value is not None}
        if not filtered_params:
            return ""
        return "?" + parse.urlencode(filtered_params, doseq=True)

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _send(self, req: request.Request) -> Any:
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(body)
                detail = payload.get("detail", body)
            except json.JSONDecodeError:
                detail = body or str(exc)
            raise APIClientError(exc.code, str(detail)) from exc
        except error.URLError as exc:
            raise APIClientError(0, f"Could not connect to API: {exc.reason}") from exc
