"""Run evals using the Exa SDK"""

import json
import time
from typing import Any

from exa_py import Exa

from evals.samplers.base_samplers.base_sdk_sampler import BaseSDKSampler


class ExaSampler(BaseSDKSampler):
    def __init__(
        self,
        sampler_name: str,
        api_key: str = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        needs_synthesis: bool = True,
        text: Any = False,
    ):
        self.text: bool = text
        super().__init__(
            sampler_name=sampler_name,
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
            needs_synthesis=needs_synthesis,
        )

    def _initialize_client(self):
        self.client = Exa(self.api_key)

    def _get_search_results_impl(self, query: str) -> Any:
        return self.client.search(
            query=query, num_results=10, contents={"text": self.text}
        )

    def format_results(self, results: Any) -> list[str]:
        formatted_results = []

        raw_results = getattr(results, "results", None)
        for result in raw_results:
            title = getattr(result, "title", "")
            url = getattr(result, "url", "")
            text = getattr(result, "text", "")
            if text:
                formatted_results.append(f'[{title}]({url})\ntext: "{text}"\n')

        return formatted_results


class ExaResearchSampler(BaseSDKSampler):
    """Exa Research SDK sampler."""

    def __init__(
        self,
        sampler_name: str,
        api_key: str = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        research_model: str = "",
        needs_synthesis: bool = False,
    ):
        self.research_model = research_model
        super().__init__(
            sampler_name=sampler_name,
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
            needs_synthesis=needs_synthesis,
        )

    def _initialize_client(self):
        self.client = Exa(self.api_key)

    def _start_research_task(self, query: str):
        return self.client.research.create(
            instructions=query,
            model=self.research_model,
        )

    def _wait_for_task_to_complete(self, task):
        while (
            self.client.research.get(task.research_id, stream=False).status == "running"
        ):
            time.sleep(10)

    def _get_search_results_impl(self, query: str) -> Any:
        research = self._start_research_task(query)
        self._wait_for_task_to_complete(research)
        response = self.client.research.get(research.research_id, stream=False).json()
        return json.loads(response)

    def format_results(self, results: Any) -> list[str]:
        return [results["output"]["content"]]
