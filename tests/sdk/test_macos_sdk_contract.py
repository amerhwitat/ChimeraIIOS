import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_macos_sdk_integration_is_license_gated_and_nonbundling(tmp_path):
    helper = ROOT / "tools/build-macos-sdk.sh"
    assert helper.is_file()
    result = subprocess.run(
        ["bash", str(helper), str(tmp_path / "report.json")],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["schema"] == "macos-cross-development-report-v1"
    assert report["status"] in {"blocked", "review-required"}
    assert report["sdk"]["redistribution"] == "prohibited-unless-license-explicitly-permits"
    assert "never copy proprietary" in report["iso_policy"]
    assert (ROOT / "sdk/macos/templates/DarwinCross.cmake").is_file()
    assert (ROOT / "sdk/macos/examples/hello-macos/main.m").is_file()
    assert "darwin_cross_compiler" in result.stdout


def test_sdk_build_script_runs_macos_probe():
    content = (ROOT / "tools/build-sdks.sh").read_text()
    assert "build-macos-sdk.sh" in content
    assert "macos-sdk-report.json" in content
