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

"""
Created on Fri Apr 30 16:21:58 2021

@author: gonzo
"""
__all__ = [
    "XMLParser",
]

from datetime import datetime
from functools import lru_cache
from typing import Literal

import pandas as pd

from .ib_client import IBClient
from .objects import (
    AnalystForecast,
    Dividend,
    DividendPerShare,
    EarningsPerShare,
    ForwardYear,
    OwnershipCompany,
    OwnershipDetails,
    OwnershipReport,
    RatioSnapshot,
    Revenue,
)
from .utils import camel_to_snake
from .xml_report import XMLReport

fromisoformat = datetime.fromisoformat

SummaryReportType = Literal["A", "TTM", "R", "P", None]
SummaryPeriod = Literal["12M", "3M", None]


class XMLParser:
    """Parser for IBKR xml company fundamental data"""

    def __init__(self, ib_client: IBClient):
        self.xml_report = XMLReport(ib_client=ib_client)

    def __repr__(self):
        cls_name = self.__class__.__qualname__
        return f"{cls_name}(ib_client={self.xml_report.client!r}"

    @lru_cache(maxsize=4)
    def get_ownership_report(self) -> OwnershipReport:
        """Ownership Report"""
        fs = self.xml_report.ownership
        (isin,) = fs.findall("./ISIN")
        (fa,) = fs.findall("./floatShares")
        company = OwnershipCompany(
            ISIN=isin.text,
            float_shares=int(fa.text),
            as_of_date=(
                fromisoformat(fa.attrib["asofDate"])
                if fa.attrib["asofDate"] != "0"
                else None
            ),
        )
        _l = []
        fa = fs.findall("./Owner")

        for i in fa:
            d = {}
            d["owner_id"] = i.attrib["ownerId"]

            for j in i.findall("./"):
                if "as_of_date" not in d and j.attrib:
                    d["as_of_date"] = datetime.fromisoformat(j.attrib["asofDate"])
                d[j.tag] = float(j.text) if j.tag == "quantity" else j.text

            _l.append(OwnershipDetails(**d))

        return OwnershipReport(company=company, ownership_details=_l)

    def get_dividend(self) -> list[Dividend] | None:
        """get dividends"""
        fa = "./Dividends"
        fs = self.xml_report.fin_summary.find(fa)
        if fs is None:
            return None
        curr = fs.attrib["currency"]
        _dividend = [
            Dividend(
                type=i.attrib["type"],
                ex_date=(
                    fromisoformat(i.attrib["exDate"]) if i.attrib["exDate"] else None
                ),
                record_date=(
                    fromisoformat(i.attrib["recordDate"])
                    if i.attrib["recordDate"]
                    else None
                ),
                pay_date=(
                    fromisoformat(i.attrib["payDate"]) if i.attrib["payDate"] else None
                ),
                declaration_date=(
                    fromisoformat(i.attrib["declarationDate"])
                    if i.attrib["declarationDate"]
                    else None
                ),
                currency=curr,
                value=float(i.text) if i.text else None,
            )
            for i in fs
        ]
        return _dividend

    def get_div_per_share(
        self,
        report_type: SummaryReportType = None,
        period: SummaryPeriod = None,
    ) -> list[DividendPerShare] | None:
        """Dividend per share"""
        fa = "./DividendPerShares"
        fs = self.xml_report.fin_summary.find(fa)
        if fs is None:
            return None
        curr = fs.attrib["currency"]

        _div_ps = [
            DividendPerShare(
                as_of_date=fromisoformat(i.attrib["asofDate"]),
                report_type=i.attrib["reportType"],
                period=i.attrib["period"],
                currency=curr,
                value=float(i.text),
            )
            for i in fs
            if (
                report_type is None
                or (report_type is not None and i.attrib["reportType"] == report_type)
            )
            and (
                period is None or (period is not None and i.attrib["period"] == period)
            )
        ]
        return _div_ps

    def get_revenue(
        self,
        report_type: SummaryReportType = None,
        period: SummaryPeriod = None,
    ) -> list[Revenue]:
        """Revenue"""
        fa = "./TotalRevenues"
        fs = self.xml_report.fin_summary.find(fa)
        curr = fs.attrib["currency"]

        _revenue = [
            Revenue(
                as_of_date=fromisoformat(tr.attrib["asofDate"]),
                report_type=tr.attrib["reportType"],
                period=tr.attrib["period"],
                currency=curr,
                revenue=float(tr.text),
            )
            for tr in fs
            if (
                report_type is None
                or (report_type is not None and tr.attrib["reportType"] == report_type)
            )
            and (
                period is None or (period is not None and tr.attrib["period"] == period)
            )
        ]
        return _revenue

    def get_eps(
        self,
        report_type: SummaryReportType = None,
        period: SummaryPeriod = None,
    ) -> list[EarningsPerShare]:
        """Earnings per share"""
        fa = "./EPSs"
        fs = self.xml_report.fin_summary.find(fa)
        curr = fs.attrib["currency"]

        _eps = [
            EarningsPerShare(
                as_of_date=fromisoformat(tr.attrib["asofDate"]),
                report_type=tr.attrib["reportType"],
                period=tr.attrib["period"],
                currency=curr,
                eps=float(tr.text),
            )
            for tr in fs
            if (
                report_type is None
                or (report_type is not None and tr.attrib["reportType"] == report_type)
            )
            and (
                period is None or (period is not None and tr.attrib["period"] == period)
            )
        ]
        return _eps

    def get_analyst_forecast(self) -> AnalystForecast:
        """Analyst forecast"""
        fa = ".//ForecastData/Ratio"
        fs = self.xml_report.snapshot.findall(fa)

        _analyst_forecast = AnalystForecast(
            **{
                camel_to_snake(g.attrib["FieldName"]): float(
                    g.findall("./Value")[0].text
                )
                for g in fs
            }
        )
        return _analyst_forecast

    def get_ratios(self) -> RatioSnapshot:
        """Company ratios snapshot"""
        fa = ".//Ratios/Group/Ratio"
        fs = self.xml_report.snapshot.findall(fa)

        _ratios = RatioSnapshot(
            **{
                r.attrib["FieldName"].lower(): (
                    fromisoformat(r.text) if r.attrib["Type"] == "D" else float(r.text)
                )
                for r in fs
            }
        )
        return _ratios

    def get_fy_estimates(self) -> list[ForwardYear]:
        """Forward Year estimates"""
        fs = self.xml_report.resc
        _fy_estimates = [
            ForwardYear(
                type="Estimate",
                item=a.attrib["type"],
                unit=a.attrib["unit"],
                period_type=p.attrib["periodType"],
                fyear=int(p.attrib["fYear"]),
                end_month=int(p.attrib["endMonth"]),
                end_cal_year=int(p.attrib["endCalYear"]),
                value=float(e[0].text),
                est_type=e.attrib["type"],
            )
            for a in fs.iter("FYEstimate")
            for p in a.iter("FYPeriod")
            for e in p.iter("ConsEstimate")
        ]
        return _fy_estimates

    def get_fy_actuals(self) -> list[ForwardYear]:
        """Forward year actuals"""
        fs = self.xml_report.resc
        _fy_actuals = [
            ForwardYear(
                type="Actual",
                item=a.attrib["type"],
                unit=a.attrib["unit"],
                period_type=p.attrib["periodType"],
                fyear=int(p.attrib["fYear"]),
                end_month=int(p.attrib["endMonth"]),
                end_cal_year=int(p.attrib["endCalYear"]),
                value=float(p[0].text),
                updated=pd.to_datetime(p[0].attrib["updated"]),
            )
            for a in fs.iter("FYActual")
            for p in a.iter("FYPeriod")
        ]
        return _fy_actuals
