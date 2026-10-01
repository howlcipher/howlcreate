"""Authored, problem-conditioned fixtures. Not model inference or measured creativity."""

import hashlib
import json
import re
import time

from howl_provider_core import Execution
from howlcreate.providers.base import BaseProvider, ProviderResponse


class DeterministicProvider(BaseProvider):
    def __init__(self, model_name: str = "deterministic-fixture-v2"):
        super().__init__(model_name)
        self.call_history: list[dict] = []

    def generate(self, prompt, system_prompt="", temperature=0.7, json_mode=False):
        # Direct legacy calls have no reliable operator identity; no substring routing.
        return self.generate_for(
            "unspecified",
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=json_mode,
        )

    def generate_for(self, operation, prompt, system_prompt="", temperature=0.7, json_mode=False):
        started = time.monotonic()
        self.call_history.append(
            {
                "prompt": prompt,
                "operation": operation,
                "temperature": temperature,
                "json_mode": json_mode,
            }
        )
        match = re.search(r'(?:Problem Statement|Core Problem|Problem):\s*"([^"\n]*)"', prompt)
        problem = match.group(1) if match else "the supplied objective"
        suffix = hashlib.sha256(prompt.encode()).hexdigest()[:6]
        idea = {
            "title": f"{operation.replace('_', ' ').title()} fixture ({suffix})",
            "description": f"Explore {problem} through {operation.replace('_', ' ')}.",
            "core_mechanism": f"Compare a bounded alternative against the stated objective: {problem}",
            "assumptions": ["The supplied objective omits some operating constraints"],
            "speculations": ["This authored fixture does not establish feasibility or novelty"],
            "evidence_needs": [
                f"Test the proposed alternative against requirements for: {problem}"
            ],
            "changed_assumptions": ["Fixed constraints -> explicit constraint sensitivity"],
        }
        content = {"ideas": [idea]}
        if operation == "assumption_extraction":
            content["assumptions"] = [
                {
                    "statement": f"The stated constraints are sufficient for: {problem}",
                    "is_implicit": True,
                    "inversions": ["An omitted constraint changes the solution"],
                    "vulnerability": "Requires validation with the user",
                },
                {
                    "statement": "A single solution must serve every operating condition",
                    "is_implicit": True,
                    "inversions": ["Use explicit operating profiles"],
                },
            ]
        elif operation == "reframing":
            content["reframings"] = [
                {
                    "perspective": "Resource-constrained user",
                    "reframed_question": f"How would fewer resources change {problem}?",
                    "core_focus": "Constraint sensitivity",
                },
                {
                    "perspective": "Affected stakeholder",
                    "reframed_question": f"Whose unmet needs matter for {problem}?",
                    "core_focus": "Objective relevance",
                },
            ]
        elif operation == "independent_branching":
            content["ideas"].append(
                {
                    **idea,
                    "title": f"Alternative boundary fixture ({suffix})",
                    "description": f"Separate operating boundaries for {problem}",
                    "core_mechanism": "Isolate assumptions and compare boundary cases",
                }
            )
        elif operation == "adversarial_critique":
            content = {
                "hardened_idea": idea,
                "criticism": {
                    "vulnerabilities": ["Undeclared operating assumptions"],
                    "unconsidered_costs": ["Validation and adoption overhead"],
                    "defensive_mutations": ["Make failure assumptions explicit"],
                },
            }
        elif operation in {"evaluation", "evaluation_batch"}:

            def scores(identifier):
                dims = ["novelty", "feasibility", "usefulness", "simplicity", "strategic_fit"]
                if "ecosystem_fit" in prompt:
                    dims.append("ecosystem_fit")
                return {
                    "scores": {
                        dim: {
                            "score": 0.2
                            + int(hashlib.sha256((identifier + dim).encode()).hexdigest()[:4], 16)
                            / 65535
                            * 0.6,
                            "rationale": "Authored hash fixture, not an empirical objective-fit assessment",
                            "uncertainty": 1.0,
                        }
                        for dim in dims
                    },
                    "strengths": [],
                    "weaknesses": [],
                    "critical_risks": [],
                }

            if operation == "evaluation_batch":
                payload = json.loads(prompt.partition("CANDIDATES_JSON:\n")[2])
                content = {"evaluations": {item["id"]: scores(item["id"]) for item in payload}}
            else:
                content = scores(suffix)
        execution = Execution(
            "deterministic",
            "deterministic",
            "deterministic",
            "fixture",
            model=self.model_name,
            deterministic=True,
            mocked=True,
            inference_occurred=False,
            remote=False,
            elapsed_seconds=time.monotonic() - started,
        )
        return ProviderResponse(
            json.dumps(content),
            self.model_name,
            "deterministic",
            structured_data=content,
            metadata={"execution": execution.to_dict()},
        )
