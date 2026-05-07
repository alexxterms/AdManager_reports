from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from src.analysis import AnalysisResult
from src.models import ParsedMetrics


@dataclass(frozen=True)
class GroqInsightService:
    api_key: str
    model: str = "llama-3.1-8b-instant"
    timeout_seconds: int = 20

    def generate(self, current: ParsedMetrics, previous: ParsedMetrics | None) -> AnalysisResult | None:
        prompt = self._build_prompt(current, previous)
        response_text = self._chat(prompt)
        if not response_text:
            return None
        return self._parse_result(response_text)

    def _chat(self, prompt: str) -> str:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a senior paid media analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()

    def _build_prompt(self, current: ParsedMetrics, previous: ParsedMetrics | None) -> str:
        current_block = (
            f"Current metrics:\n"
            f"date={current.report_date.isoformat()}\n"
            f"spend_cad={current.spend_cad}\n"
            f"impressions={current.impressions}\n"
            f"ctr_percent={current.ctr_percent}\n"
            f"link_clicks={current.link_clicks}\n"
            f"leads={current.leads}\n"
            f"cpc_cad={current.cpc_cad}\n"
            f"cpm_cad={current.cpm_cad}\n"
            f"cpl_cad={current.cpl_cad}"
        )
        previous_block = "No previous period is available." if previous is None else (
            f"Previous metrics:\n"
            f"date={previous.report_date.isoformat()}\n"
            f"spend_cad={previous.spend_cad}\n"
            f"impressions={previous.impressions}\n"
            f"ctr_percent={previous.ctr_percent}\n"
            f"link_clicks={previous.link_clicks}\n"
            f"leads={previous.leads}\n"
            f"cpc_cad={previous.cpc_cad}\n"
            f"cpm_cad={previous.cpm_cad}\n"
            f"cpl_cad={previous.cpl_cad}"
        )
        return (
            f"{current_block}\n\n{previous_block}\n\n"
            "Write 3 to 5 concise problems and 3 to 5 concise solutions. "
            "Focus on week-over-week performance trends and business actionability. "
            "Respond only with JSON in this shape: {\"problems\": [\"...\"], \"solutions\": [\"...\"]}. "
            "Do not include markdown, code fences, or commentary."
        )

    def _parse_result(self, response_text: str) -> AnalysisResult | None:
        try:
            payload: Any = json.loads(response_text)
        except json.JSONDecodeError:
            return None

        problems = payload.get("problems")
        solutions = payload.get("solutions")
        if not isinstance(problems, list) or not isinstance(solutions, list):
            return None

        problems_text = [str(item).strip() for item in problems if str(item).strip()]
        solutions_text = [str(item).strip() for item in solutions if str(item).strip()]
        if not problems_text or not solutions_text:
            return None

        return AnalysisResult(problems=problems_text[:5], solutions=solutions_text[:5])
