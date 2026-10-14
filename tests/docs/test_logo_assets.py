"""Tests that the committed logo SVGs are what tools/docs/generate_logo.py renders.

The SVGs are committed because the README links them; rerun `just generate-logo` when this fails.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPOSITORY_ROOT / "tools" / "docs" / "generate_logo.py"
ASSETS_DIRECTORY = REPOSITORY_ROOT / "docs" / "assets" / "brand"
LOGO_ASSETS = (
    "odys-wordmark-on-dark.svg",
    "odys-wordmark-on-light.svg",
    "odys-mark-on-dark.svg",
    "odys-mark-on-light.svg",
    "favicon-dark.svg",
    "favicon-light.svg",
)


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("generate_logo", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rendered_assets() -> dict[str, str]:
    assets: dict[str, str] = _load_generator().render_logo_assets()
    return assets


def test_logo_generator_renders_exactly_the_committed_assets(rendered_assets: dict[str, str]) -> None:
    assert sorted(rendered_assets) == sorted(LOGO_ASSETS)


@pytest.mark.parametrize("name", LOGO_ASSETS, ids=LOGO_ASSETS)
def test_logo_asset_matches_generator_output(name: str, rendered_assets: dict[str, str]) -> None:
    assert (ASSETS_DIRECTORY / name).read_text() == rendered_assets[name]
