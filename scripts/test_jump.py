from src.jump import jump_to_window
from src.window import get_all_windows


def parse_hwnd(raw_value: str) -> int:
    value = raw_value.strip()
    if not value:
        raise ValueError("Empty hwnd")

    return int(value, 0)


def main() -> None:
    windows = sorted(get_all_windows(), key=lambda item: (item["desktop_id"] or "", item["title"].lower()))

    if not windows:
        print("No visible windows found.")
        return

    print("Visible windows:")
    for window in windows:
        print(
            f"hwnd={window['hwnd']} "
            f"desktop={window['desktop_id']} "
            f"pid={window['pid']} "
            f"title={window['title']}"
        )

    raw_hwnd = input("\nEnter hwnd to jump to (decimal or 0xHEX): ")

    try:
        hwnd = parse_hwnd(raw_hwnd)
        result = jump_to_window(hwnd)
    except Exception as exc:
        print(f"Jump failed: {exc}")
        return

    desktop = result["desktop"] or {}
    print("\nJump result:")
    print(f"hwnd={result['hwnd']}")
    print(f"title={result['title']}")
    print(f"pid={result['pid']}")
    print(
        "desktop="
        f"{desktop.get('number')} "
        f"id={desktop.get('id')} "
        f"name={desktop.get('name')}"
    )


if __name__ == "__main__":
    main()
