from property_sms import InfraiClient, InspectionReminder, PropertySmsService


class FakeClient:
    def __init__(self):
        self.calls = []

    def send_sms(self, to, message, request_id):
        self.calls.append((to, message, request_id))
        return {"message_id": "msg-1"}


def test_suppressed_tenant_does_not_receive_inspection_sms():
    client = FakeClient()
    service = PropertySmsService(client, {"+15550001111"})
    reminder = InspectionReminder("inspect-42", "+15550001111", "2026-09-12")

    assert service.notify_inspection(reminder) is None
    assert client.calls == []


def test_active_tenant_receives_sms():
    client = FakeClient()
    service = PropertySmsService(client)
    result = service.notify_inspection(InspectionReminder("inspect-43", "+15550002222", "2026-09-12"))

    assert result == {"message_id": "msg-1"}
    assert client.calls[0][0] == "+15550002222"


def test_sms_uses_body_field_and_retries_error_envelope_on_429(monkeypatch):
    class Response:
        def __init__(self, status_code, envelope, headers=None):
            self.status_code = status_code
            self.envelope = envelope
            self.headers = headers or {}

        def json(self):
            return self.envelope

    class Session:
        def __init__(self):
            self.calls = []
            self.responses = [
                Response(429, {"ok": False, "error": {"code": "RATE_LIMITED"}}, {"Retry-After": "0"}),
                Response(200, {"ok": True, "data": {"message_id": "msg-1"}}),
            ]

        def request(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    session = Session()
    monkeypatch.setattr("property_sms.time.sleep", lambda seconds: None)

    assert InfraiClient(key="test", session=session).send_sms("+15550002222", "Reminder", "inspect-43") == {"message_id": "msg-1"}
    assert len(session.calls) == 2
    assert all(call["json"] == {"to": "+15550002222", "body": "Reminder"} for call in session.calls)
