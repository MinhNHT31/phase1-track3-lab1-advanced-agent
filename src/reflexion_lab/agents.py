import time
from dataclasses import dataclass
from typing import Literal
from . import mock_runtime
from .mock_runtime import FAILURE_MODE_BY_QID, actor_answer, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        judge = None
        for attempt_id in range(1, self.max_attempts + 1):
            # Measure Actor latency
            start_time = time.perf_counter()
            answer = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            actor_latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Measure Evaluator latency
            start_time = time.perf_counter()
            judge = evaluator(example, answer)
            evaluator_latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            if mock_runtime.MODE == "llm":
                token_estimate = mock_runtime.last_tokens.get("actor", 0) + mock_runtime.last_tokens.get("evaluator", 0)
                latency_ms = actor_latency_ms + evaluator_latency_ms
            else:
                # Mock formulas as given in the template
                token_estimate = 320 + (attempt_id * 65) + (120 if self.agent_type == "reflexion" else 0)
                latency_ms = 160 + (attempt_id * 40) + (90 if self.agent_type == "reflexion" else 0)
            
            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=answer,
                score=judge.score,
                reason=judge.reason,
                token_estimate=token_estimate,
                latency_ms=latency_ms
            )
            final_answer = answer
            final_score = judge.score
            
            if judge.score == 1:
                traces.append(trace)
                break
            
            # Triển khai logic Reflexion tại đây
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                start_time = time.perf_counter()
                reflection = reflector(example, attempt_id, judge)
                reflector_latency_ms = int((time.perf_counter() - start_time) * 1000)
                
                reflections.append(reflection)
                trace.reflection = reflection
                reflection_memory.append(reflection.next_strategy)
                
                if mock_runtime.MODE == "llm":
                    trace.token_estimate += mock_runtime.last_tokens.get("reflector", 0)
                    trace.latency_ms += reflector_latency_ms
            
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        
        if final_score == 1:
            failure_mode = "none"
        else:
            if judge:
                if len(traces) >= 2 and traces[-1].answer == traces[-2].answer:
                    failure_mode = "looping"
                elif judge.missing_evidence:
                    failure_mode = "incomplete_multi_hop"
                elif judge.spurious_claims:
                    failure_mode = "entity_drift"
                else:
                    failure_mode = "wrong_final_answer"
            else:
                failure_mode = "wrong_final_answer"
                
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
