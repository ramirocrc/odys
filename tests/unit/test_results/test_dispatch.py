import pytest
import xarray as xr

from odys.results.dispatch import GeneratorDispatch

EXPECTED_GENERATOR_COUNT = 2


@pytest.fixture
def generator_dispatch() -> GeneratorDispatch:
    generators = ["generator_1", "generator_2"]
    timesteps = [0, 1]

    power = xr.DataArray(
        [[10.0, 20.0], [30.0, 40.0]],
        dims=["generator", "time"],
        coords={"generator": generators, "time": timesteps},
    )

    status = xr.DataArray(
        [[1, 1], [1, 0]],
        dims=["generator", "time"],
        coords={"generator": generators, "time": timesteps},
    )

    startup = xr.DataArray(
        [[0, 1], [1, 0]],
        dims=["generator", "time"],
        coords={"generator": generators, "time": timesteps},
    )

    shutdown = xr.DataArray(
        [[0, 0], [0, 1]],
        dims=["generator", "time"],
        coords={"generator": generators, "time": timesteps},
    )

    return GeneratorDispatch(
        power=power,
        status=status,
        startup=startup,
        shutdown=shutdown,
    )

def test_power_property(generator_dispatch: GeneratorDispatch) -> None:
    power = generator_dispatch.power

    assert list(power.values) == [10.0, 20.0, 30.0, 40.0]


def test_status_property(generator_dispatch: GeneratorDispatch) -> None:
    result = generator_dispatch.status

    assert list(result.values) == [1, 1, 1, 0]


def test_startup_property(generator_dispatch: GeneratorDispatch) -> None:
    result = generator_dispatch.startup

    assert list(result.values) == [0, 1, 1, 0]


def test_shutdown_property(generator_dispatch: GeneratorDispatch) -> None:
    result = generator_dispatch.shutdown

    assert list(result.values) == [0, 0, 0, 1]


def test_getitem(generator_dispatch: GeneratorDispatch) -> None:
    result = generator_dispatch["generator_1"]

    assert isinstance(result, GeneratorDispatch)
    assert list(result.power.values) == [10.0, 20.0]


def test_iter(generator_dispatch: GeneratorDispatch) -> None:
    items = list(generator_dispatch)

    assert len(items) == EXPECTED_GENERATOR_COUNT
    assert all(isinstance(item, GeneratorDispatch) for item in items)


def test_len(generator_dispatch: GeneratorDispatch) -> None:
    assert len(generator_dispatch) == EXPECTED_GENERATOR_COUNT


def test_contains(generator_dispatch: GeneratorDispatch) -> None:
    assert "generator_1" in generator_dispatch
    assert "generator_2" in generator_dispatch
    assert "generator_3" not in generator_dispatch


def test_to_dataset(generator_dispatch: GeneratorDispatch) -> None:
    dataset = generator_dispatch.to_dataset()

    assert isinstance(dataset, xr.Dataset)
    assert "power" in dataset.data_vars
    assert "status" in dataset.data_vars
    assert "startup" in dataset.data_vars
    assert "shutdown" in dataset.data_vars


def test_to_dataframe(generator_dispatch: GeneratorDispatch) -> None:
    dataframe = generator_dispatch.to_dataframe()

    assert not dataframe.empty
    assert "power" in dataframe.columns
