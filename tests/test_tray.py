def test_placeholder_tray_module_importable():
    import src.tray as tray
    assert hasattr(tray, "create_tray_icon")
