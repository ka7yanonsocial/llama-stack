# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Union,
    runtime_checkable,
)

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from llama_stack.apis.common.type_system import ParamType
from llama_stack.apis.resource import Resource, ResourceType
from llama_stack.schema_utils import json_schema_type, register_schema, webmethod


# Perhaps more structure can be imposed on these functions. Maybe they could be associated
# with standard metrics so they can be rolled up?
@json_schema_type
class ScoringFnParamsType(Enum):
    """
    A type of scoring function parameters.

    :cvar llm_as_judge: Provide judge model and prompt template.
    :cvar regex_parser: Provide regexes to parse the answer from the generated response.
    :cvar basic: Parameters for basic non-parameterized scoring function.
    """

    custom_llm_as_judge = "custom_llm_as_judge"
    regex_parser = "regex_parser"
    basic = "basic"


@json_schema_type
class ScoringFunctionType(Enum):
    """
    A type of scoring function. Each type is a criteria for evaluating answers.

    :cvar llm_as_judge: Scoring function that uses a judge model to score the answer.
    :cvar regex_parser: Scoring function that parses the answer from the generated response using regexes, and checks against the expected answer.
    """

    custom_llm_as_judge = "custom_llm_as_judge"
    regex_parser = "regex_parser"
    regex_parser_math_response = "regex_parser_math_response"
    equality = "equality"
    subset_of = "subset_of"
    factuality = "factuality"
    faithfulness = "faithfulness"
    answer_correctness = "answer_correctness"
    answer_relevancy = "answer_relevancy"
    answer_similarity = "answer_similarity"
    context_entity_recall = "context_entity_recall"
    context_precision = "context_precision"
    context_recall = "context_recall"
    context_relevancy = "context_relevancy"


@json_schema_type
class AggregationFunctionType(Enum):
    average = "average"
    median = "median"
    categorical_count = "categorical_count"
    accuracy = "accuracy"


@json_schema_type
class LLMAsJudgeScoringFnParams(BaseModel):
    type: Literal["llm_as_judge"] = "llm_as_judge"
    judge_model: str
    prompt_template: Optional[str] = None
    judge_score_regexes: Optional[List[str]] = Field(
        description="Regexes to extract the answer from generated response",
        default_factory=list,
    )
    aggregation_functions: Optional[List[AggregationFunctionType]] = Field(
        description="Aggregation functions to apply to the scores of each row",
        default_factory=list,
    )


@json_schema_type
class RegexParserScoringFnParams(BaseModel):
    type: Literal["regex_parser"] = "regex_parser"
    parsing_regexes: Optional[List[str]] = Field(
        description="Regexes to extract the answer from generated response",
        default_factory=list,
    )
    aggregation_functions: Optional[List[AggregationFunctionType]] = Field(
        description="Aggregation functions to apply to the scores of each row",
        default_factory=list,
    )


@json_schema_type
class BasicScoringFnParams(BaseModel):
    type: Literal["basic"] = "basic"
    aggregation_functions: Optional[List[AggregationFunctionType]] = Field(
        description="Aggregation functions to apply to the scores of each row",
        default_factory=list,
    )


ScoringFnParams = register_schema(
    Annotated[
        Union[
            LLMAsJudgeScoringFnParams,
            RegexParserScoringFnParams,
            BasicScoringFnParams,
        ],
        Field(discriminator="type"),
    ],
    name="ScoringFnParams",
)


class CommonScoringFnFields(BaseModel):
    scoring_fn_type: ScoringFunctionType
    description: Optional[str] = None
    params: Optional[ScoringFnParams] = Field(
        description="The parameters for the scoring function for benchmark eval, these can be overridden for app eval",
        default=None,
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional metadata for this definition",
    )


@json_schema_type
class ScoringFn(CommonScoringFnFields, Resource):
    type: Literal[ResourceType.scoring_function.value] = ResourceType.scoring_function.value

    @property
    def scoring_fn_id(self) -> str:
        return self.identifier

    @property
    def provider_scoring_fn_id(self) -> str:
        return self.provider_resource_id


class ScoringFnInput(CommonScoringFnFields, BaseModel):
    scoring_fn_id: str
    provider_id: Optional[str] = None
    provider_scoring_fn_id: Optional[str] = None


class ListScoringFunctionsResponse(BaseModel):
    data: List[ScoringFn]


@runtime_checkable
class ScoringFunctions(Protocol):
    @webmethod(route="/scoring-functions", method="GET")
    async def list_scoring_functions(self) -> ListScoringFunctionsResponse: ...

    @webmethod(route="/scoring-functions/{scoring_fn_id:path}", method="GET")
    async def get_scoring_function(self, scoring_fn_id: str, /) -> Optional[ScoringFn]: ...

    @webmethod(route="/scoring-functions", method="POST")
    async def register_scoring_function(
        self,
        scoring_fn_type: ScoringFunctionType,
        params: Optional[ScoringFnParams] = None,
        scoring_fn_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Register a new scoring function with given parameters.
        Only valid scoring function type that can be parameterized can be registered.

        :param scoring_fn_type: The type of scoring function to register. A function type can only be registered if it is a valid type.
        :param params: The parameters for the scoring function.
        :param scoring_fn_id: (Optional) The ID of the scoring function to register. If not provided, a random ID will be generated.
        :param description: (Optional) The description of the scoring function.
        :param metadata: (Optional) Any additional metadata to be associated with the scoring function.
        """
        ...
