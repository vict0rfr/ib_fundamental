#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Company Fundamental class
"""
# pylint: disable=attribute-defined-outside-init
# pylint: disable=missing-function-docstring

__all__ = [
    "FundamentalData",
]

from datetime import datetime
from typing import Optional

from ib_async import IB, Dividends, FundamentalRatios, Stock, Ticker
from pandas import DataFrame

from ib_fundamental.objects import (
    AnalystForecast,
    BalanceSheetSet,
    CashFlowSet,
    Dividend,
    DividendPerShare,
    EarningsPerShare,
    ForwardYear,
    IncomeSet,
    OwnershipReport,
    RatioSnapshot,
    Revenue,
)
from ib_fundamental.utils import build_statement, to_dataframe

from .ib_client import IBClient
from .xml_parser import XMLParser

fromisoformat = datetime.fromisoformat


class FundamentalData:
    """Company fundamental data"""

    # pylint: disable=too-many-arguments,too-many-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self, ib: IB, symbol: str, exchange: str = "SMART", currency: str = "USD"
    ) -> None:
        """Args:
        ib (ib_async.IB): ib_async.IB instance
        symbol (str): company symbol/ticker
        exchange (str, optional): exchange. Defaults to "SMART".
        currency (str, optional): currency. Defaults to "USD".
        """
        self.client = IBClient(
            symbol=symbol, ib=ib, exchange=exchange, currency=currency
        )
        self.symbol = symbol
        self.contract: Stock = self.client.contract
        self.ticker: Optional[Ticker] = None
        self.parser = XMLParser(ib_client=self.client)

    def __repr__(self):
        cls_name = self.__class__.__qualname__
        return f"{cls_name}(symbol={self.symbol!r},IB={self.client.ib!r})"

    def __enter__(self):
        return self

    @property
    def ownership_report(self) -> OwnershipReport:
        """Ownership Report"""
        try:
            return self.__ownership_report
        except AttributeError:
            self.__ownership_report: OwnershipReport = (
                self.parser.get_ownership_report()
            )
            return self.__ownership_report

    @property
    def dividend(self) -> list[Dividend] | None:
        try:
            return self.__dividend
        except AttributeError:
            self.__dividend: list[Dividend] | None = self.parser.get_dividend()
            return self.__dividend

    @property
    def div_ps_q(self) -> list[DividendPerShare] | None:
        try:
            return self.__div_ps_q
        except AttributeError:
            self.__div_ps_q: list[DividendPerShare] | None = (
                self.parser.get_div_per_share(report_type="R", period="3M")
            )
            return self.__div_ps_q

    @property
    def div_ps_ttm(self) -> list[DividendPerShare] | None:
        try:
            return self.__div_ps_ttm
        except AttributeError:
            self.__div_ps_ttm: list[DividendPerShare] | None = (
                self.parser.get_div_per_share(report_type="TTM")
            )
            return self.__div_ps_ttm

    @property
    def revenue_ttm(self) -> list[Revenue]:
        try:
            return self.__revenue_ttm
        except AttributeError:
            self.__revenue_ttm: list[Revenue] = self.parser.get_revenue(
                report_type="TTM"
            )
            return self.__revenue_ttm

    @property
    def revenue_q(self) -> list[Revenue]:
        try:
            return self.__revenue_q
        except AttributeError:
            self.__revenue_q: list[Revenue] = self.parser.get_revenue(
                report_type="R", period="3M"
            )
            return self.__revenue_q

    @property
    def eps_ttm(self) -> list[EarningsPerShare]:
        try:
            return self.__eps_ttm
        except AttributeError:
            self.__eps_ttm: list[EarningsPerShare] = self.parser.get_eps(
                report_type="TTM"
            )
            return self.__eps_ttm

    @property
    def eps_q(self) -> list[EarningsPerShare]:
        try:
            return self.__eps_q
        except AttributeError:
            self.__eps_q: list[EarningsPerShare] = self.parser.get_eps(
                report_type="R", period="3M"
            )
            return self.__eps_q

    @property
    def analyst_forecast(self) -> AnalystForecast:
        try:
            return self.__analyst_forecast
        except AttributeError:
            self.__analyst_forecast: AnalystForecast = (
                self.parser.get_analyst_forecast()
            )
            return self.__analyst_forecast

    @property
    def ratios(self) -> RatioSnapshot:
        try:
            return self.__ratios
        except AttributeError:
            self.__ratios: RatioSnapshot = self.parser.get_ratios()
            return self.__ratios

    @property
    def fundamental_ratios(self) -> FundamentalRatios | None:
        try:
            return self.__fundamental_ratios
        except AttributeError:
            self.__fundamental_ratios: FundamentalRatios | None = (
                self.client.get_ratios()
            )
            self.ticker = self.client.ib.ticker(self.contract)
            return self.__fundamental_ratios

    @property
    def dividend_summary(self) -> Dividends | None:
        try:
            return self.__dividend_summary
        except AttributeError:
            self.__dividend_summary: Dividends | None = self.client.get_dividends()
            self.ticker = self.client.ib.ticker(self.contract)
            return self.__dividend_summary

    @property
    def fy_estimates(self) -> list[ForwardYear]:
        try:
            return self.__fy_estimates
        except AttributeError:
            self.__fy_estimates: list[ForwardYear] = self.parser.get_fy_estimates()
            return self.__fy_estimates

    @property
    def fy_actuals(self) -> list[ForwardYear]:
        try:
            return self.__fy_actuals
        except AttributeError:
            self.__fy_actuals: list[ForwardYear] = self.parser.get_fy_actuals()
            return self.__fy_actuals


class CompanyFinancials:
    """Company Financials"""

    def __init__(
        self, ib: IB, symbol: str, exchange: str = "SMART", currency: str = "USD"
    ) -> None:
        """
        Args:
            ib (ib_async.IB): ib_async.IB instance
            symbol (str): company symbol/ticker
            exchange (str, optional): exchange. Defaults to "SMART".
            currency (str, optional): currency. Defaults to "USD".
        """
        self.data = FundamentalData(
            symbol=symbol, ib=ib, exchange=exchange, currency=currency
        )

    def __repr__(self):
        cls_name = self.__class__.__qualname__
        return f"{cls_name}(symbol={self.data.symbol!r},IB={self.data.client.ib!r})"

    @property
    def dividends(self) -> DataFrame | None:
        if self.data.dividend:
            return to_dataframe(self.data.dividend, key="ex_date")
        return None

    @property
    def dividends_ps_q(self) -> DataFrame | None:
        if self.data.div_ps_q:
            return to_dataframe(self.data.div_ps_q, key="as_of_date")
        return None

    @property
    def dividends_ps_ttm(self) -> DataFrame | None:
        if self.data.div_ps_ttm:
            return to_dataframe(self.data.div_ps_ttm, key="as_of_date")
        return None

    @property
    def revenue_q(self) -> DataFrame | None:
        if self.data.revenue_q:
            return to_dataframe(self.data.revenue_q, key="as_of_date")
        return None

    @property
    def revenue_ttm(self) -> DataFrame | None:
        if self.data.revenue_ttm:
            return to_dataframe(self.data.revenue_ttm, key="as_of_date")
        return None

    @property
    def eps_q(self) -> DataFrame | None:
        if self.data.eps_q:
            return to_dataframe(self.data.eps_q, key="as_of_date")
        return None

    @property
    def eps_ttm(self) -> DataFrame | None:
        if self.data.eps_ttm:
            return to_dataframe(self.data.eps_ttm, key="as_of_date")
        return None

    @property
    def ownership(self) -> DataFrame | None:
        if self.data.ownership_report:
            return to_dataframe(self.data.ownership_report.ownership_details)
        return None

    @property
    def fy_actuals(self) -> DataFrame | None:
        if self.data.fy_actuals:
            return to_dataframe(self.data.fy_actuals, key="updated")
        return None

    @property
    def fy_estimates(self) -> DataFrame | None:
        if self.data.fy_estimates:
            return to_dataframe(self.data.fy_estimates)
        return None

    @property
    def analyst_forecast(self) -> DataFrame | None:
        if self.data.analyst_forecast:
            return to_dataframe([self.data.analyst_forecast]).T
        return None

    @property
    def ratios(self) -> DataFrame | None:
        if self.data.ratios:
            return to_dataframe([self.data.ratios]).T.dropna()
        return None

    @property
    def fundamental_ratios(self) -> DataFrame | None:
        if self.data.fundamental_ratios:
            return to_dataframe([vars(self.data.fundamental_ratios)]).T
        return None
