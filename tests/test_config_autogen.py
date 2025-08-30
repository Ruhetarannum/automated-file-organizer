import json

from organizer.file_mover import load_config


def test_config_autogeneration(tmp_path, monkeypatch):
    # Move into a clean directory
    monkeypatch.chdir(tmp_path)

    config_path = tmp_path / ".fileorganizer.json"
    assert not config_path.exists()

    # Call load_config → should create default config
    cfg = load_config()
    assert cfg is not None
    assert config_path.exists()

    data = json.loads(config_path.read_text())
    assert "source_folder" in data
    assert "destination_folders" in data
