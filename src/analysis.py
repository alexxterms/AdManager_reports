from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.models import ParsedMetrics


@dataclass(frozen=True)
class MetricChange:
    name: str
    current: float
    previous: float

    @property
    def delta(self) -> float:
        return self.current - self.previous

    @property
    def pct_change(self) -> float:
        if self.previous == 0:
            return 0.0
        return (self.delta / self.previous) * 100.0


@dataclass(frozen=True)
class AnalysisResult:
    problems: List[str]
    solutions: List[str]


def _fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def _build_change(current: float, previous: float, name: str) -> MetricChange:
    return MetricChange(name=name, current=current, previous=previous)


def _maybe_add_change_problem(
    problems: list[str],
    solutions: list[str],
    change: MetricChange,
    positive_phrase: str,
    negative_phrase: str,
    solution_text: str,
    min_pct: float,
) -> None:
    if change.pct_change <= -min_pct:
        problems.append(
            f"{change.name} {negative_phrase} by {_fmt_pct(abs(change.pct_change))} week-over-week."
        )
        solutions.append(solution_text)
    elif change.pct_change >= min_pct:
        problems.append(
            f"{change.name} {positive_phrase} by {_fmt_pct(change.pct_change)} week-over-week."
        )
        solutions.append(solution_text)


def analyze_metrics(current: ParsedMetrics, previous: ParsedMetrics | None) -> AnalysisResult:
    if previous is None:
        problems: list[str] = []
        solutions: list[str] = []

        if current.ctr_percent < 1.0:
            problems.append("CTR is below 1.0%, suggesting the creative or targeting could be stronger.")
            solutions.append("Refresh creatives and test new hooks to improve engagement.")

        if current.cpc_cad > 10:
            problems.append("CPC is relatively high, indicating traffic is getting more expensive.")
            solutions.append("Refine targeting and placements to reduce auction pressure and lower CPC.")

        if current.cpm_cad > 100:
            problems.append("CPM is elevated, which usually points to higher auction costs.")
            solutions.append("Expand creative testing and audience segmentation to improve delivery efficiency.")

        if current.cpl_cad > 100:
            problems.append("Cost per lead is high, showing weaker conversion efficiency.")
            solutions.append("Improve the landing page and form flow to reduce friction and lower CPL.")

        if current.leads < 10:
            problems.append("Lead volume is low, so the campaign is not yet producing enough conversion volume.")
            solutions.append("Increase spend gradually after improving efficiency signals and conversion rate.")

        if not problems:
            problems.append("The current snapshot looks stable, but there is no previous period to compare against.")
            solutions.append("Keep monitoring performance and compare against the next weekly data point.")

        return AnalysisResult(problems=problems, solutions=solutions)

    problems = []
    solutions = []

    spend_change = _build_change(current.spend_cad, previous.spend_cad, "Ad spend")
    cpc_change = _build_change(current.cpc_cad, previous.cpc_cad, "CPC")
    cpm_change = _build_change(current.cpm_cad, previous.cpm_cad, "CPM")
    cpl_change = _build_change(current.cpl_cad, previous.cpl_cad, "Cost per lead")
    ctr_change = _build_change(current.ctr_percent, previous.ctr_percent, "CTR")
    leads_change = _build_change(current.leads, previous.leads, "Lead volume")
    impressions_change = _build_change(current.impressions, previous.impressions, "Impressions")

    if spend_change.pct_change <= -5:
        problems.append(
            f"Ad spend decreased week-over-week by {_fmt_pct(abs(spend_change.pct_change))}, slightly limiting overall reach and data volume."
        )
        solutions.append("Stabilize and gradually increase ad spend to regain volume and improve data for optimization.")

    if cpc_change.pct_change >= 5:
        problems.append(
            f"CPC increased by {_fmt_pct(cpc_change.pct_change)}, indicating higher traffic costs."
        )
        solutions.append("Optimize targeting and placements to bring CPC back down.")

    if cpm_change.pct_change >= 5:
        problems.append(
            f"CPM increased by {_fmt_pct(cpm_change.pct_change)}, indicating higher auction costs and reduced cost efficiency."
        )
        solutions.append("Refresh and test new creatives to improve CTR and reduce cost pressure.")

    if cpl_change.pct_change >= 5:
        problems.append(
            f"Cost per form fill rose by {_fmt_pct(cpl_change.pct_change)}, showing reduced efficiency in converting traffic into leads."
        )
        solutions.append("Improve the conversion flow and landing page to lower cost per form fill.")

    if ctr_change.pct_change >= 1 and ctr_change.pct_change < 10:
        problems.append(
            f"CTR improved slightly by {_fmt_pct(ctr_change.pct_change)}, but not enough to offset rising traffic costs."
        )
        solutions.append("Keep iterating on creative angles and messaging to make the CTR lift more meaningful.")

    if abs(leads_change.pct_change) <= 10:
        problems.append(
            "Lead volume remained flat, suggesting the current spend level is not scaling output."
        )
        solutions.append("Monitor performance closely and only scale spend once conversion efficiency improves.")

    if impressions_change.pct_change <= -5:
        solutions.append("Recover reach by restoring spend and checking whether delivery constraints are limiting impressions.")

    if not problems:
        problems.append("No major week-over-week deterioration is visible in the tracked metrics.")
        solutions.append("Continue monitoring trends and iterate based on the next performance cycle.")

    return AnalysisResult(problems=problems, solutions=solutions)
