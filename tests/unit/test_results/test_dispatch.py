import pytest
import xarray as xr

from odys.results.dispatch import GeneratorDispatch, MarketDispatch, StorageDispatch

EXPECTED_GENERATOR_COUNT = 2
EXPECTED_STORAGE_COUNT = 2
EXPECTED_TIMESTEP_COUNT = 2
EXPECTED_MARKET_COUNT = 2
EXPECTED_SERIES_LENGTH = EXPECTED_STORAGE_COUNT * EXPECTED_TIMESTEP_COUNT


@pytest.fixture
def storage_dispatch() -> StorageDispatch:
    storage_names = ["storage_1", "storage_2"]
    timesteps = [0, 1]

    net_power = xr.DataArray(
        [[10.0, 20.0], [30.0, 40.0]],
        dims=["storage", "time"],
        coords={"storage": storage_names, "time": timesteps},
    )

    soc = xr.DataArray(
        [[50.0, 60.0], [70.0, 80.0]],
        dims=["storage", "time"],
        coords={"storage": storage_names, "time": timesteps},
    )

    charge_mode = xr.DataArray(
        [[1, 0], [0, 1]],
        dims=["storage", "time"],
        coords={"storage": storage_names, "time": timesteps},
    )

    return StorageDispatch(
        net_power=net_power,
        soc=soc,
        charge_mode=charge_mode,
    )


def test_getitem(storage_dispatch: StorageDispatch) -> None:
    storage = storage_dispatch["storage_1"]

    assert isinstance(storage, StorageDispatch)
    assert len(storage.net_power) == EXPECTED_TIMESTEP_COUNT


def test_iter(storage_dispatch: StorageDispatch) -> None:
    items = list(storage_dispatch)

    assert len(items) == EXPECTED_STORAGE_COUNT
    assert all(isinstance(item, StorageDispatch) for item in items)


def test_len(storage_dispatch: StorageDispatch) -> None:
    assert len(storage_dispatch) == EXPECTED_STORAGE_COUNT


def test_contains(storage_dispatch: StorageDispatch) -> None:
    assert "storage_1" in storage_dispatch
    assert "storage_2" in storage_dispatch
    assert "storage_3" not in storage_dispatch


def test_net_power(storage_dispatch: StorageDispatch) -> None:
    net_power = storage_dispatch.net_power

    assert len(net_power) == EXPECTED_SERIES_LENGTH


def test_soc(storage_dispatch: StorageDispatch) -> None:
    soc = storage_dispatch.soc

    assert len(soc) == EXPECTED_SERIES_LENGTH


def test_charge_mode(storage_dispatch: StorageDispatch) -> None:
    charge_mode = storage_dispatch.charge_mode

    assert len(charge_mode) == EXPECTED_SERIES_LENGTH


def test_to_dataset(storage_dispatch: StorageDispatch) -> None:
    dataset = storage_dispatch.to_dataset()

    assert isinstance(dataset, xr.Dataset)
    assert "net_power" in dataset.data_vars
    assert "soc" in dataset.data_vars
    assert "charge_mode" in dataset.data_vars


def test_to_dataframe(storage_dispatch: StorageDispatch) -> None:
    dataframe = storage_dispatch.to_dataframe()

    assert not dataframe.empty
    assert "net_power" in dataframe.columns
    assert "soc" in dataframe.columns
    assert "charge_mode" in dataframe.columns


def test_repr(storage_dispatch: StorageDispatch) -> None:
    representation = repr(storage_dispatch)

    assert "StorageDispatch" in representation


@pytest.fixture
def market_dispatch() -> MarketDispatch:
    market_names = ["market_1", "market_2"]
    timesteps = [0, 1]

    sell_volume = xr.DataArray(
        [[10.0, 20.0], [30.0, 40.0]],
        dims=["market", "time"],
        coords={"market": market_names, "time": timesteps},
    )

    buy_volume = xr.DataArray(
        [[1.0, 2.0], [3.0, 4.0]],
        dims=["market", "time"],
        coords={"market": market_names, "time": timesteps},
    )

    return MarketDispatch(
        sell_volume=sell_volume,
        buy_volume=buy_volume,
    )


def test_market_getitem(market_dispatch: MarketDispatch) -> None:
    market = market_dispatch["market_1"]

    assert isinstance(market, MarketDispatch)
    assert len(market.sell_volume) == EXPECTED_TIMESTEP_COUNT


def test_market_iter(market_dispatch: MarketDispatch) -> None:
    items = list(market_dispatch)

    assert len(items) == EXPECTED_MARKET_COUNT
    assert all(isinstance(item, MarketDispatch) for item in items)


def test_market_len(market_dispatch: MarketDispatch) -> None:
    assert len(market_dispatch) == EXPECTED_MARKET_COUNT


def test_market_contains(market_dispatch: MarketDispatch) -> None:
    assert "market_1" in market_dispatch
    assert "market_2" in market_dispatch
    assert "market_3" not in market_dispatch


def test_market_sell_volume(market_dispatch: MarketDispatch) -> None:
    sell_volume = market_dispatch.sell_volume

    assert len(sell_volume) == EXPECTED_SERIES_LENGTH


def test_market_buy_volume(market_dispatch: MarketDispatch) -> None:
    buy_volume = market_dispatch.buy_volume

    assert len(buy_volume) == EXPECTED_SERIES_LENGTH


def test_market_net_volume(market_dispatch: MarketDispatch) -> None:
    net_volume = market_dispatch.net_volume

    assert isinstance(net_volume, xr.DataArray)


def test_market_to_dataset(market_dispatch: MarketDispatch) -> None:
    dataset = market_dispatch.to_dataset()

    assert isinstance(dataset, xr.Dataset)
    assert "sell_volume" in dataset.data_vars
    assert "buy_volume" in dataset.data_vars


def test_market_to_dataframe(market_dispatch: MarketDispatch) -> None:
    dataframe = market_dispatch.to_dataframe()

    assert not dataframe.empty
    assert "sell_volume" in dataframe.columns
    assert "buy_volume" in dataframe.columns


def test_market_repr(market_dispatch: MarketDispatch) -> None:
    representation = repr(market_dispatch)

    assert "MarketDispatch" in representation


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
