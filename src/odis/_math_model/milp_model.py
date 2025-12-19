from functools import cached_property

from linopy import Model, Variable
from pydantic import BaseModel, ConfigDict

from odis._math_model.model_components.parameters.battery_parameters import BatteryIndex
from odis._math_model.model_components.parameters.generator_parameters import GeneratorIndex
from odis._math_model.model_components.parameters.load_parameters import LoadIndex
from odis._math_model.model_components.parameters.market_parameters import MarketIndex
from odis._math_model.model_components.parameters.parameters import EnergySystemParameters
from odis._math_model.model_components.parameters.scenario_parameters import ScenarioIndex, TimeIndex
from odis._math_model.model_components.variables import ModelVariable


class EnergyModelIndices(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scenarios: ScenarioIndex
    time: TimeIndex
    generators: GeneratorIndex | None
    batteries: BatteryIndex | None
    loads: LoadIndex | None
    markets: MarketIndex | None


class EnergyMILPModel:
    def __init__(self, parameters: EnergySystemParameters) -> None:
        self._parameters = parameters
        self._linopy_model = Model(force_dim_names=True)

    @cached_property
    def indices(self) -> EnergyModelIndices:
        return EnergyModelIndices(
            scenarios=self._parameters.scenarios.scenario_index,
            time=self._parameters.scenarios.time_index,
            generators=self._parameters.generators.index if self._parameters.generators is not None else None,
            batteries=self._parameters.batteries.index if self._parameters.batteries is not None else None,
            loads=self._parameters.loads.index if self._parameters.loads is not None else None,
            markets=self._parameters.markets.index if self._parameters.markets is not None else None,
        )

    @property
    def linopy_model(self) -> Model:
        return self._linopy_model

    @property
    def parameters(self) -> EnergySystemParameters:
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
    def market_sell_volume(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.MARKET_SELL.var_name]

    @property
    def market_buy_volume(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.MARKET_BUY.var_name]

    @property
    def market_trade_mode(self) -> Variable:
        return self._linopy_model.variables[ModelVariable.MARKET_TRADE_MODE.var_name]
