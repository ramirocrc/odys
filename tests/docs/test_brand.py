"""tools/docs/brand/tokens.json is the single source of truth for Odys colours and fonts.

These tests keep it valid and accessible, and keep the landing page from drifting
away from it with hard-coded values.
"""

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]
TOKENS = json.loads((ROOT / "tools" / "docs" / "brand" / "tokens.json").read_text())
COLORS: dict[str, str] = TOKENS["color"]
SCHEMES: dict[str, dict[str, str]] = TOKENS["scheme"]
CHART_ROLES: dict[str, dict[str, str | bool]] = TOKENS["chart"]["roles"]
CHART_CHROME: dict[str, dict[str, str]] = TOKENS["chart"]["chrome"]
CHART_SCHEMES = ("light", "dark")
LANDING_FILES = [
    ROOT / "docs" / "assets" / "stylesheets" / "home.css",
    ROOT / "docs" / "assets" / "javascripts" / "home.js",
    ROOT / "overrides" / "home.html",
]
HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")
WCAG_AA_TEXT = 4.5
WCAG_AA_GRAPHICS = 3.0
SRGB_LINEAR_THRESHOLD = 0.03928

# (text role, background role) pairs that carry readable text in the docs theme.
TEXT_PAIRS = [
    ("foreground", "background"),
    ("foreground-muted", "background"),
    ("link", "background"),
    ("accent", "background"),
    ("header-text", "header"),
    ("code-foreground", "code-background"),
]


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_generator() -> ModuleType:
    return _load_module("generate_brand", ROOT / "tools" / "docs" / "generate_brand.py")


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= SRGB_LINEAR_THRESHOLD else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    lighter, darker = sorted((_relative_luminance(foreground), _relative_luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize(("name", "value"), COLORS.items())
def test_brand_colors_are_lowercase_hex(name: str, value: str) -> None:
    assert HEX_COLOR.match(value), f"{name} = {value!r}"


@pytest.mark.parametrize("scheme", SCHEMES)
def test_scheme_roles_reference_brand_colors(scheme: str) -> None:
    unknown = {role: color for role, color in SCHEMES[scheme].items() if color not in COLORS}

    assert not unknown


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize(("text", "background"), TEXT_PAIRS)
def test_scheme_text_meets_wcag_aa(scheme: str, text: str, background: str) -> None:
    roles = SCHEMES[scheme]

    assert _contrast(COLORS[str(roles[text])], COLORS[str(roles[background])]) >= WCAG_AA_TEXT


@pytest.mark.parametrize("scheme", CHART_SCHEMES)
@pytest.mark.parametrize("role", CHART_ROLES)
def test_chart_roles_are_visible_on_their_scheme_background(role: str, scheme: str) -> None:
    pair = CHART_ROLES[role]
    color = str(pair[scheme])
    background = str(CHART_CHROME["background"][scheme])

    assert HEX_COLOR.match(color)
    if not pair.get("fill"):
        assert _contrast(color, background) >= WCAG_AA_GRAPHICS


@pytest.mark.parametrize("scheme", CHART_SCHEMES)
@pytest.mark.parametrize("name", ["text", "muted"])
def test_chart_text_meets_wcag_aa(name: str, scheme: str) -> None:
    background = str(CHART_CHROME["background"][scheme])

    assert _contrast(str(CHART_CHROME[name][scheme]), background) >= WCAG_AA_TEXT


def test_each_light_chart_colour_has_one_dark_counterpart() -> None:
    dark_by_light: dict[str, set[str]] = {}
    for pair in [*CHART_ROLES.values(), *CHART_CHROME.values()]:
        dark_by_light.setdefault(str(pair["light"]), set()).add(str(pair["dark"]))

    assert {light: darks for light, darks in dark_by_light.items() if len(darks) > 1} == {}


def test_dark_chart_conversion_swaps_every_light_colour() -> None:
    plots = _load_module("generate_example_plots", ROOT / "tools" / "docs" / "generate_example_plots.py")
    light = {str(pair["light"]) for pair in [*CHART_ROLES.values(), *CHART_CHROME.values()]}
    unchanged = {
        str(pair["light"]) for pair in [*CHART_ROLES.values(), *CHART_CHROME.values()] if pair["light"] == pair["dark"]
    }
    alpha = plots.with_alpha(str(CHART_ROLES["check_ok"]["light"]), 0.18)
    figure_json = json.dumps({"colors": sorted(light), "fill": alpha, "none": plots.TRANSPARENT})

    dark = plots.to_dark(figure_json)

    assert set(re.findall(r"#[0-9a-f]{6}", dark)) & (light - unchanged) == set()
    assert plots.with_alpha(str(CHART_ROLES["check_ok"]["dark"]), 0.18) in dark
    assert plots.TRANSPARENT in dark


def test_generated_css_exposes_every_token_and_maps_both_schemes() -> None:
    generator = _load_generator()
    css = generator.render_brand_css(generator.load_brand())

    for name, value in COLORS.items():
        assert f"--odys-{name}: {value};" in css
    for selector in generator.SCHEME_SELECTORS.values():
        block = css.split(f"{selector} {{", 1)[1].split("}", 1)[0]
        assert all(f"{variable}:" in block for variable in generator.THEME_VARIABLES)


def test_generated_css_loads_the_sans_width_axis_for_display_headings() -> None:
    generator = _load_generator()
    css = generator.render_brand_css(generator.load_brand())
    sans = TOKENS["font"]["sans"]
    widths = "..".join(str(width) for width in sans["widths"])
    weights = f"{min(sans['weights'])}..{max(sans['weights'])}"

    assert f"family=Mona+Sans:wdth,wght@{widths},{weights}" in css


@pytest.mark.parametrize("path", LANDING_FILES, ids=lambda p: p.name)
def test_landing_page_has_no_hard_coded_colours(path: Path) -> None:
    source = path.read_text()

    assert not re.findall(r"#[0-9a-fA-F]{6}\b|\brgba?\(", source)


@pytest.mark.parametrize("path", LANDING_FILES, ids=lambda p: p.name)
def test_landing_page_only_uses_defined_brand_variables(path: Path) -> None:
    defined = {f"--odys-{name}" for name in COLORS} | {f"--odys-font-{role}" for role in TOKENS["font"]}
    used = set(re.findall(r"var\((--odys-[a-z0-9-]+)\)", path.read_text()))
    used |= {f"--odys-{name}" for name in re.findall(r'token\("([a-z0-9-]+)"\)', path.read_text())}

    assert used <= defined
