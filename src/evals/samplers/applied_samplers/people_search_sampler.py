"""People-search API samplers (structured people[] output, no LLM synthesis).

These samplers depend on the optional sibling package ``people-search-eval``
(Nyne / PDL / Exa people clients). Install with::

    pip install -e /path/to/people-search-eval

Or set ``PEOPLE_SEARCH_EVAL_SRC`` to that package's ``src/`` directory.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from evals.processing.people_search.routing import (
    build_execution_record,
    scorer_payload_from_provider_result,
)
from evals.samplers.base_samplers.base_sampler import BaseSampler

logger = logging.getLogger(__name__)


def _ensure_people_search_eval_importable() -> None:
    try:
        import people_search_eval  # noqa: F401

        return
    except ImportError:
        pass

    candidates: list[Path] = []
    env = os.environ.get("PEOPLE_SEARCH_EVAL_SRC")
    if env:
        candidates.append(Path(env).expanduser())

    # Sibling checkouts relative to this repo
    repo_root = Path(__file__).resolve().parents[4]
    candidates.append(repo_root.parent / "people-search-eval" / "src")
    candidates.append(repo_root / "people-search-eval" / "src")

    for candidate in candidates:
        src = str(candidate)
        if candidate.is_dir() and src not in sys.path:
            sys.path.insert(0, src)
            try:
                import people_search_eval  # noqa: F401

                return
            except ImportError:
                continue

    raise ImportError(
        "people_search_eval package not found. Install it with "
        "`pip install -e /path/to/people-search-eval` or set PEOPLE_SEARCH_EVAL_SRC "
        "to that package's src/ directory."
    )


def _parse_metadata(ground_truth: str) -> dict:
    if not ground_truth:
        return {}
    try:
        data = json.loads(ground_truth)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


class _PeopleSearchSampler(BaseSampler):
    """Shared base for Nyne / PDL / Exa people samplers."""

    provider: str = "unknown"

    def __init__(
        self,
        sampler_name: str,
        api_key: str | None = None,
        timeout: float = 600.0,
        max_retries: int = 2,
        max_concurrency: int = 2,
    ):
        super().__init__(
            sampler_name=sampler_name,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            needs_synthesis=False,
            max_concurrency=max_concurrency,
        )
        self._eval_metadata: dict = {}

    async def __call__(
        self,
        query_input,
        dataset,
        ground_truth: str = "",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        self._eval_metadata = _parse_metadata(ground_truth)
        return await super().__call__(
            query_input, dataset, ground_truth=ground_truth, overwrite=overwrite
        )

    def _build_record(self, query: str) -> dict:
        return build_execution_record(
            query,
            self._eval_metadata,
            for_exa=(self.provider == "exa"),
        )

    def _execute(self, record: dict) -> dict:
        raise NotImplementedError

    async def get_search_results(self, query: str) -> Any:
        _ensure_people_search_eval_importable()
        record = self._build_record(query)
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._execute, record),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            error_msg = f"{self.sampler_name} timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise TimeoutError(error_msg) from None

    def format_results(self, results: Any) -> str:
        if not isinstance(results, dict):
            payload = {
                "provider": self.provider,
                "people": [],
                "person_count": 0,
                "error": "invalid provider result",
            }
        else:
            payload = scorer_payload_from_provider_result(results, self.provider)
        return json.dumps(payload, ensure_ascii=False)


class NynePeopleSampler(_PeopleSearchSampler):
    provider = "nyne"

    def __init__(self, sampler_name: str = "nyne_people", **kwargs):
        api_key = kwargs.pop("api_key", None) or os.getenv("NYNE_API_KEY")
        super().__init__(sampler_name=sampler_name, api_key=api_key, **kwargs)

    async def get_search_results(self, query: str) -> Any:
        if not os.getenv("NYNE_API_SECRET"):
            raise ValueError(
                "NYNE_API_SECRET is required for nyne_people. Set it in .env."
            )
        return await super().get_search_results(query)

    def _execute(self, record: dict) -> dict:
        from people_search_eval.execute_query import execute_query

        return execute_query(record)


class PdlPeopleSampler(_PeopleSearchSampler):
    provider = "pdl"

    def __init__(self, sampler_name: str = "pdl_people", **kwargs):
        api_key = kwargs.pop("api_key", None) or os.getenv("PDL_API_KEY")
        super().__init__(sampler_name=sampler_name, api_key=api_key, **kwargs)

    def _execute(self, record: dict) -> dict:
        from people_search_eval.execute_pdl_query import execute_pdl_query

        return execute_pdl_query(record)


class ExaPeopleSampler(_PeopleSearchSampler):
    """Exa people-category search (via people-search-eval), not web search snippets."""

    provider = "exa"

    def __init__(self, sampler_name: str = "exa_people", **kwargs):
        api_key = kwargs.pop("api_key", None) or os.getenv("EXA_API_KEY")
        super().__init__(sampler_name=sampler_name, api_key=api_key, **kwargs)

    def _execute(self, record: dict) -> dict:
        from people_search_eval.execute_exa_query import execute_exa_query

        return execute_exa_query(record)
