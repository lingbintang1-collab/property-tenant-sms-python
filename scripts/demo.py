from property_sms import InspectionReminder, build_service


def main() -> None:
    service = build_service()
    reminder = InspectionReminder("inspection-demo", "+15550002222", "2026-09-12")
    print(service.notify_inspection(reminder))


if __name__ == "__main__":
    main()
