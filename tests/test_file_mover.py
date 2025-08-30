import json

from organizer.file_mover import FileMover


def test_categorize_file_config_file_extensions(tmp_path, monkeypatch):
    # Create custom config
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {"source_folder": str(tmp_path), "destination_folders": {"custom": str(tmp_path / "Custom")}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "test.custom"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "custom"


def test_categorize_file_built_in_without_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "image.jpg"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "images"


def test_categorize_file_custom_config_mapping(tmp_path, monkeypatch):
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {"source_folder": str(tmp_path), "destination_folders": {"docs": str(tmp_path / "Docs")}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "report.docs"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "docs"


def test_categorize_file_config_fallback_to_builtin(tmp_path, monkeypatch):
    # Config without the extension
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {"source_folder": str(tmp_path), "destination_folders": {}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "note.txt"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "documents"


def test_categorize_file_config_unknown_extensions_return_others(tmp_path, monkeypatch):
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {"source_folder": str(tmp_path), "destination_folders": {}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "weirdfile.unknownext"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "others"


def test_categorize_file_config_case_insensitive_matching(tmp_path, monkeypatch):
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {"source_folder": str(tmp_path), "destination_folders": {"images": str(tmp_path / "Images")}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "photo.JPG"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "images"


def test_categorize_file_config_priority_over_builtin(tmp_path, monkeypatch):
    # Custom config that overrides .jpg handling
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {
        "source_folder": str(tmp_path),
        "destination_folders": {"custom_images": str(tmp_path / "CustomImages")},
    }
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "override.jpg"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "custom_images"


def test_categorize_file_empty_config_uses_builtin(tmp_path, monkeypatch):
    config_path = tmp_path / ".fileorganizer.json"
    config_data = {"source_folder": str(tmp_path), "destination_folders": {}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "presentation.pptx"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "documents"


def test_categorize_file_invalid_config_uses_builtin(tmp_path, monkeypatch):
    config_path = tmp_path / ".fileorganizer.json"
    config_path.write_text("INVALID JSON")

    monkeypatch.chdir(tmp_path)
    mover = FileMover(str(tmp_path), {})

    test_file = tmp_path / "song.mp3"
    test_file.write_text("dummy")

    category = mover.categorize_file(test_file)
    assert category == "music"
