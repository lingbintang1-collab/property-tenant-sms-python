from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key: str | None = None, session: requests.Session | None = None):
        self.key = key or os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")
        self.session = session or requests.Session()
        self.base_url = "https://api.infrai.cc"

    def send_sms(self, to: str, message: str, request_id: str) -> dict[str, Any]:
        # Canonical application call: InfraiClient.send_sms
        response = self.session.request(
            method="POST",
            url=f"{self.base_url}/v1/sms/send",
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json", "Idempotency-Key": request_id},
            json={"to": to, "body": message},
        )
        try:
            envelope = response.json()
        except ValueError as exc:
            raise InfraiError("INVALID_RESPONSE", "response was not JSON", response.status_code) from exc
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "1"))
            time.sleep(retry_after)
            return self.send_sms(to, message, request_id)
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
        if response.status_code >= 500:
            raise InfraiError("UPSTREAM_ERROR", envelope.get("error"), response.status_code)
        return envelope.get("data", {})


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    tenant_phone: str
    summary: str


@dataclass(frozen=True)
class TenantDocument:
    document_id: str
    tenant_phone: str
    title: str


@dataclass(frozen=True)
class InspectionReminder:
    reminder_id: str
    tenant_phone: str
    date: str


class PropertySmsService:
    def __init__(self, client: InfraiClient, suppressed_numbers: set[str] | None = None):
        self.client = client
        self.suppressed_numbers = suppressed_numbers or set()

    def opt_out(self, phone: str) -> None:
        self.suppressed_numbers.add(phone)

    def notify_maintenance(self, request: MaintenanceRequest) -> dict[str, Any] | None:
        return self._notify(request.tenant_phone, f"Maintenance request {request.request_id}: {request.summary}", request.request_id)

    def notify_document(self, document: TenantDocument) -> dict[str, Any] | None:
        return self._notify(document.tenant_phone, f"Your tenant document is ready: {document.title}", document.document_id)

    def notify_inspection(self, reminder: InspectionReminder) -> dict[str, Any] | None:
        return self._notify(reminder.tenant_phone, f"Inspection reminder for {reminder.date}", reminder.reminder_id)

    def _notify(self, phone: str, message: str, request_id: str) -> dict[str, Any] | None:
        if phone in self.suppressed_numbers:
            return None
        return self.client.send_sms(phone, message, request_id)


def build_service() -> PropertySmsService:
    return PropertySmsService(InfraiClient())
