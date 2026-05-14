import json
from typing import Any

from parallel import Parallel

from evals.samplers.base_samplers.base_sdk_sampler import BaseSDKSampler


class ParallelSampler(BaseSDKSampler):
    """Base class for Parallel samplers with shared client initialization."""

    def __init__(
        self,
        sampler_name: str,
        api_key: str = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        needs_synthesis: bool = True,
    ):
        super().__init__(
            sampler_name=sampler_name,
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
            needs_synthesis=needs_synthesis,
        )

    def _initialize_client(self):
        self.client = Parallel(api_key=self.api_key)

    def _get_search_results_impl(self, query: str) -> Any:
        raise NotImplementedError


class ParallelSearchSampler(ParallelSampler):
    """Parallel sampler using the Search API"""

    def __init__(
        self,
        sampler_name: str,
        api_key: str = None,
        timeout: float = 60.0,
        num_results: int = 5,
        max_characters: int | None = None,
        mode: str = "one-shot",
    ):
        self.num_results = num_results
        self.max_characters = max_characters
        self.mode = mode

        super().__init__(
            sampler_name=sampler_name,
            api_key=api_key,
            timeout=timeout,
        )

    def _get_search_results_impl(self, query):
        search_params = {"mode": self.mode}
        if self.max_characters is not None:
            search_params["excerpts"] = {"max_chars_per_result": self.max_characters}

        if isinstance(query, str):
            query = [query]

        response = self.client.search(
            search_queries=query,
            advanced_settings={"max_results": self.num_results},
            **search_params,
        )
        return json.loads(response.json())

    def format_results(self, results: Any) -> list[str]:
        formatted_results = []
        if results and results.get("results"):
            for result in results.get("results"):
                title = result.get("title")
                url = result.get("url")
                content = "\n".join(result.get("excerpts"))
                formatted_results.append(f"[{title}]({url})\n{content}\n")
        return formatted_results


class ParallelTaskSampler(ParallelSampler):
    """Parallel sampler using the Task API.

    Set needs_synthesis=False to use the task output directly as the final
    answer (no downstream LLM synthesis step). In that mode `task_spec` is
    omitted so the API returns a plain text answer.
    """

    def __init__(
        self,
        sampler_name: str,
        api_key: str = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        processor: str = "base",
        needs_synthesis: bool = True,
    ):
        self.processor = processor
        super().__init__(
            sampler_name=sampler_name,
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
            needs_synthesis=needs_synthesis,
        )

    def _get_search_results_impl(self, query: str) -> Any:
        create_kwargs = {"input": query, "processor": self.processor}
        if self.needs_synthesis:
            create_kwargs["task_spec"] = {"output_schema": {"type": "text"}}

        task_run = self.client.task_run.create(**create_kwargs)
        return self.client.task_run.result(
            run_id=task_run.run_id,
            api_timeout=int(self.timeout),
        )

    def format_results(self, results: Any) -> str:
        if results and hasattr(results, "output"):
            output = results.output
            if isinstance(output, str):
                return output
            if hasattr(output, "content"):
                return output.content
            if isinstance(output, dict) and "content" in output:
                return output["content"]
        return ""
