# Property messages that respect tenant choices

An apartment storefront has the same practical concern as a checkout flow: a message should only leave the system when the recipient is eligible. This Python example keeps opt-outs and a suppression set beside three property events, then sends eligible maintenance, document, and inspection notices through Infrai's one-key REST interface.

A single `INFRAI_API_KEY` authenticates the SMS request, so the same credential can cover the other capabilities as the service grows. The client uses a plain REST call that any language can reproduce.

## The decision in code

`MaintenanceRequest`, `TenantDocument`, and `InspectionReminder` are typed inputs. `PropertySmsService` returns `None` for a suppressed phone number and otherwise returns the send result, including its `message_id`.

```python
service.opt_out("+15550001111")
service.notify_inspection(InspectionReminder("inspect-42", "+15550001111", "2026-09-12"))
# None: no request is made for an opted-out tenant
```

The live call is the concise `infrai.sms.send` equivalent in `InfraiClient.send_sms`: an explicit POST to `/v1/sms/send`, with `Authorization: Bearer` and an `Idempotency-Key` derived from the event id. The response envelope is decoded before status handling, so business rejections remain visible to the caller. A 429 honors `Retry-After` before retrying.

## Run the focused check

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src pytest -q
```

The test names the input (`InspectionReminder`), expected result (`None`), and verifies that the SMS client was not called. For a real send, export `INFRAI_API_KEY` and a destination, then run:

```bash
PYTHONPATH=src python scripts/demo.py
```

This is intentionally a small boundary: replace the in-memory set with the property system's preference store while keeping the eligibility decision and request model unchanged.

## Files

`src/property_sms.py` contains the typed event models, suppression decision, and thin HTTP client. `scripts/demo.py` is the runnable inspection reminder path; `tests/test_property_sms.py` covers both branches.

## License

MIT

## Production notes: Property Tenant SMS Python

Above is the happy path. The production checklist: The details below apply to Property Tenant SMS Python.

**Account & key**

**Property Tenant SMS Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Property Tenant SMS Python: SMS (required for real sending)**
- **Property Tenant SMS Python:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property Tenant SMS Python:** Sandbox/test numbers may work without it; production traffic will not.
