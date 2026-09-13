import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "python"))
from chimera_ui_controls import UICommandRegistry, UIControl


def test_control_schema_has_required_command_binding():
    schema = json.loads((ROOT / "desktop" / "ui_control_contract.json").read_text())
    assert schema["schema_version"] == "CHM-UI-CONTROL-1"
    assert "command" in schema["required"]


def test_command_registry_dispatches_to_application_logic():
    seen = []
    registry = UICommandRegistry()
    registry.register("file.save", lambda args: seen.append(args) or "saved")
    result = registry.dispatch(UIControl("save", "button", "file.save", {"path": "demo.txt"}))
    assert result == "saved"
    assert seen == [{"path": "demo.txt"}]


def test_unknown_command_is_not_silent():
    registry = UICommandRegistry()
    try:
        registry.dispatch(UIControl("broken", "button", "missing.command"))
    except KeyError as exc:
        assert "missing.command" in str(exc)
    else:
        raise AssertionError("unbound UI control must fail loudly")
