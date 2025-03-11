# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
from typing import Any, Dict, Optional

from llama_stack.apis.inference.inference import Inference, UserMessage
from llama_stack.apis.scoring import ScoringResultRow
from llama_stack.apis.scoring_functions import ScoringFnParams
from llama_stack.providers.utils.scoring.base_scoring_fn import RegisteredBaseScoringFn

from .fn_defs.llm_as_judge_405b_math_match import llm_as_judge_405b_math_match
from .fn_defs.llm_as_judge_base import llm_as_judge_base


class LlmAsJudgeScoringFn(RegisteredBaseScoringFn):
    """
    A scoring_fn that assigns
    """

    def __init__(self, inference_api: Inference, *arg, **kwargs) -> None:
        super().__init__(*arg, **kwargs)
        self.inference_api = inference_api
        self.supported_fn_defs_registry = {
            llm_as_judge_base.identifier: llm_as_judge_base,
            llm_as_judge_405b_math_match.identifier: llm_as_judge_405b_math_match,
        }

    async def score_row(
        self,
        input_row: Dict[str, Any],
        scoring_fn_identifier: Optional[str] = None,
        scoring_params: Optional[ScoringFnParams] = None,
    ) -> ScoringResultRow:
        assert scoring_fn_identifier is not None, "Scoring function identifier not found."
        fn_def = self.supported_fn_defs_registry[scoring_fn_identifier]

        # override params if scoring_params is provided
        if scoring_params is not None:
            fn_def.params = scoring_params

        assert fn_def.params is not None, f"LLMAsJudgeparams not found for {fn_def}."
        assert fn_def.params.prompt_template is not None, "LLM Judge prompt_template not found."

        expected_answer = input_row["expected_answer"]
        generated_answer = input_row["generated_answer"]

        judge_input_msg = fn_def.params.prompt_template.format(
            expected_answer=expected_answer,
            generated_answer=generated_answer,
        )

        print("judge_input_msg", judge_input_msg)

        judge_response = await self.inference_api.chat_completion(
            model_id=fn_def.params.judge_model,
            messages=[
                UserMessage(
                    content=judge_input_msg,
                ),
            ],
        )

        score = 1.0 if judge_response.lower().strip() == "yes" else 0.0

        return {
            "score": score,
            "judge_feedback": judge_response,
        }
