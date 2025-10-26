from functools import cached_property

from linopy import Model, Variable
from pydantic import BaseModel

from optimes._math_model.model_components.parameters import EnergyModelParameters
from optimes._math_model.model_components.sets import (
    BatteryIndex,
    GeneratorIndex,
    LoadIndex,
    MarketIndex,
    ScenarioIndex,
    TimeIndex,
)
from optimes._math_model.model_components.variables import ModelVariable


class EnergyModelIndices(BaseModel, frozen=True, extra="forbid"):
    scenarios: ScenarioIndex
    time: TimeIndex
    generators: GeneratorIndex | None
    batteries: BatteryIndex | None
    loads: LoadIndex | None
    markets: MarketIndex | None


class EnergyMILPModel:
    def __init__(self, parameters: EnergyModelParameters) -> None:
        self._parameters = parameters
        self._linopy_model = Model(force_dim_names=True)

    @cached_property
    def indices(self) -> EnergyModelIndices:
        return EnergyModelIndices(
            scenarios=self._parameters.scenario.scenario_index,
            time=self._parameters.time.time_index,
            generators=self._parameters.generators.index if self._parameters.generators is not None else None,
            batteries=self._parameters.batteries.index if self._parameters.batteries is not None else None,
            loads=self._parameters.loads.index if self._parameters.loads is not None else None,
            markets=self._parameters.markets.index if self._parameters.markets is not None else None,
        )

    @property
    def linopy_model(self) -> Model:
        return self._linopy_model

    @property
    def parameters(self) -> EnergyModelParameters:
        return self._parameters

    @property
    def generator_power(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.GENERATOR_POWER.var_name]

    @property
    def generator_status(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.GENERATOR_STATUS.var_name]

    @property
    def generator_startup(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.GENERATOR_STARTUP.var_name]

    @property
    def generator_shutdown(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.GENERATOR_SHUTDOWN.var_name]

    @property
    def battery_power_in(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.BATTERY_POWER_IN.var_name]

    @property
    def battery_power_net(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.BATTERY_POWER_NET.var_name]

    @property
    def battery_power_out(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.BATTERY_POWER_OUT.var_name]

    @property
    def battery_soc(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.BATTERY_SOC.var_name]

    @property
    def battery_charge_mode(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.BATTERY_CHARGE_MODE.var_name]

    @property
    def market_traded_volume(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.MARKET_TRADED_VOLUME.var_name]
