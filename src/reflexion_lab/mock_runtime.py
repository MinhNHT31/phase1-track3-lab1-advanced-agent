from __future__ import annotations
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .utils import normalize_answer
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

load_dotenv()

# Mode: "mock" or "llm"
MODE = os.environ.get("REFLEXION_MODE", "mock").lower()

# Track token counts of the last API calls
last_tokens = {"actor": 0, "evaluator": 0, "reflector": 0}

FIRST_ATTEMPT_WRONG = {"hp2": "London", "hp4": "Atlantic Ocean", "hp6": "Red Sea", "hp8": "Andes"}
FAILURE_MODE_BY_QID = {"hp2": "incomplete_multi_hop", "hp4": "wrong_final_answer", "hp6": "entity_drift", "hp8": "entity_drift"}

_client = None

def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        _client = OpenAI(api_key=api_key)
    return _client

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> str:
    global MODE
    if MODE == "llm":
        c = get_openai_client()
        context_str = "\n\n".join([f"Document: {chunk.title}\n{chunk.text}" for chunk in example.context])
        user_content = f"Question: {example.question}\n\nContext Documents:\n{context_str}"
        
        if reflection_memory:
            user_content += "\n\nYour past attempts failed. Here is the feedback/strategies you generated from past failures. Please review them carefully and adjust your reasoning to avoid repeating those errors:\n"
            for i, ref in enumerate(reflection_memory, 1):
                user_content += f"{i}. {ref}\n"
            user_content += "\nNow, formulate your corrected final short answer."
            
        response = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ACTOR_SYSTEM},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1
        )
        last_tokens["actor"] = response.usage.total_tokens
        return response.choices[0].message.content.strip()
    else:
        # Mock mode
        last_tokens["actor"] = 0
        if example.qid not in FIRST_ATTEMPT_WRONG:
            return example.gold_answer
        if agent_type == "react":
            return FIRST_ATTEMPT_WRONG[example.qid]
        if attempt_id == 1 and not reflection_memory:
            return FIRST_ATTEMPT_WRONG[example.qid]
        return example.gold_answer

def evaluator(example: QAExample, answer: str) -> JudgeResult:
    global MODE
    if MODE == "llm":
        c = get_openai_client()
        user_content = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nPredicted Answer: {answer}"
        
        response = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": EVALUATOR_SYSTEM},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        last_tokens["evaluator"] = response.usage.total_tokens
        res_data = json.loads(response.choices[0].message.content.strip())
        return JudgeResult.model_validate(res_data)
    else:
        # Mock mode
        last_tokens["evaluator"] = 0
        if normalize_answer(example.gold_answer) == normalize_answer(answer):
            return JudgeResult(score=1, reason="Final answer matches the gold answer after normalization.")
        if normalize_answer(answer) == "london":
            return JudgeResult(score=0, reason="The answer stopped at the birthplace city and never completed the second hop to the river.", missing_evidence=["Need to identify the river that flows through London."], spurious_claims=[])
        return JudgeResult(score=0, reason="The final answer selected the wrong second-hop entity.", missing_evidence=["Need to ground the answer in the second paragraph."], spurious_claims=[answer])

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> ReflectionEntry:
    global MODE
    if MODE == "llm":
        c = get_openai_client()
        context_str = "\n\n".join([f"Document: {chunk.title}\n{chunk.text}" for chunk in example.context])
        
        user_content = (
            f"Question: {example.question}\n"
            f"Context Documents:\n{context_str}\n\n"
            f"Attempt ID: {attempt_id}\n"
            f"Evaluator Feedback / Reason for failure: {judge.reason}\n"
            f"Missing evidence: {judge.missing_evidence}\n"
            f"Spurious claims: {judge.spurious_claims}"
        )
        
        response = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": REFLECTOR_SYSTEM},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        last_tokens["reflector"] = response.usage.total_tokens
        res_data = json.loads(response.choices[0].message.content.strip())
        res_data["attempt_id"] = attempt_id
        return ReflectionEntry.model_validate(res_data)
    else:
        # Mock mode
        last_tokens["reflector"] = 0
        strategy = "Do the second hop explicitly: birthplace city -> river through that city." if example.qid == "hp2" else "Verify the final entity against the second paragraph before answering."
        return ReflectionEntry(attempt_id=attempt_id, failure_reason=judge.reason, lesson="A partial first-hop answer is not enough; the final answer must complete all hops.", next_strategy=strategy)
