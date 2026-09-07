"""Deterministic and mock provider for hermetic testing and offline execution."""

from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any, Dict, Tuple
from howlcreate.providers.base import BaseProvider, ProviderResponse


class DeterministicProvider(BaseProvider):
    """Predictable, reproducible provider that derives structured outputs from input hashes."""

    def __init__(self, model_name: str = "deterministic-engine-v1"):
        super().__init__(model_name=model_name)
        self.call_history: list[Dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ProviderResponse:
        start_time = time.time()
        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "json_mode": json_mode,
        })

        lower_prompt = prompt.lower()
        has_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:6]

        if "reframing operator" in lower_prompt or "reframing lenses" in lower_prompt:
            content_dict = {
                "reframings": [
                    {
                        "perspective": "Adversary / Opportunist",
                        "reframed_question": "How could an untrusted anonymous entity extract bounties maliciously?",
                        "core_focus": "Trust minimization and adversarial hardening.",
                    },
                    {
                        "perspective": "Resource-Constrained Contributor",
                        "reframed_question": "How can valuable engineering happen with intermittent power and zero cloud credits?",
                        "core_focus": "Offline-first computation and tiny compute footprints.",
                    },
                ],
                "ideas": [
                    {
                        "title": f"Adversary-Hardened Proof Escrow ({has_hash})",
                        "perspective_origin": "Adversary / Opportunist",
                        "description": "Bounties staked behind formal verification barriers that prevent sybil attacks.",
                        "core_mechanism": "Cryptographic slashing for invalid state transitions.",
                        "speculations": ["Adversarial bounties will incentivize white-hat fuzzing"],
                        "evidence_needs": ["Game-theoretic equilibrium analysis"],
                    }
                ],
            }
        elif "adversarial" in lower_prompt or "red-team" in lower_prompt or "attack protocol" in lower_prompt:
            content_dict = {
                "criticism": {
                    "vulnerabilities": [
                        "Vulnerable to sybil attacks if proof complexity is low.",
                        "High cognitive onboarding barrier for non-technical contributors.",
                    ],
                    "unconsidered_costs": [
                        "Arbitration costs for ambiguous task definitions.",
                    ],
                    "defensive_mutations": [
                        "Introduce bilateral stake slashing for frivolous disputes.",
                        "Require reproducible local test environments before task publication.",
                    ],
                },
                "hardened_idea": {
                    "title": f"Hardened Bilateral Stake Mesh ({has_hash})",
                    "description": "Reinforced coordination architecture requiring dual-bonded collateral before task claim.",
                    "core_mechanism": "Automated proof verification backed by bilateral collateral pools.",
                    "safeguards_added": ["Collateral slashing", "Deterministic sandbox containment"],
                    "speculations": ["Collateral requirements will eliminate 99% of spam"],
                    "evidence_needs": ["Capital efficiency metrics under low liquidity"],
                },
            }
        elif "assumption operator" in lower_prompt or "assumption extraction" in lower_prompt or "implicit assumptions" in lower_prompt:
            content_dict = {
                "assumptions": [
                    {
                        "statement": "The problem must be resolved by human coordinators synchronously.",
                        "is_implicit": True,
                        "vulnerability": "Breaks under high latency and timezone fragmentation.",
                        "inversions": [
                            "Coordination happens asynchronously via state-based eventual consistency.",
                            "Autonomous micro-agents negotiate contracts without human mediation.",
                        ],
                    },
                    {
                        "statement": "Centralized authority is required to verify quality of work.",
                        "is_implicit": False,
                        "vulnerability": "Creates an administrative bottleneck and platform extraction rent.",
                        "inversions": [
                            "Quality is verified by automated mathematical proofs and test suites.",
                            "Reputation is bonded in bilateral escrow rather than platform-policed.",
                        ],
                    },
                ],
                "ideas": [
                    {
                        "title": f"Asynchronous State-Settled Work Mesh ({has_hash})",
                        "description": "Workers interact with an immutable state machine that releases escrow upon deterministic proof execution.",
                        "core_mechanism": "Elimination of human dispatchers via reproducible HFIR verification.",
                        "changed_assumptions": ["Assumed human review -> replaced by test proofs"],
                        "speculations": ["Workers will prefer instant settlement over periodic paychecks"],
                        "evidence_needs": ["Latency benchmarks of proof evaluation"],
                    }
                ],
            }
        elif "concept evaluator" in lower_prompt or "evaluate across dimensions" in lower_prompt:
            title_match = re.search(r"Title:\s*([^\n]+)", prompt)
            title_seed = title_match.group(1).strip() if title_match else has_hash

            def _hash_score(dim: str, base: float = 0.50, spread: float = 0.40) -> Tuple[float, float]:
                h = int(hashlib.sha256(f"{title_seed}:{dim}".encode("utf-8")).hexdigest()[:6], 16)
                s = round(base + ((h % 100) / 100.0) * spread, 2)
                u = round(0.05 + (((h >> 8) % 25) / 100.0), 2)
                return s, u

            nov_s, nov_u = _hash_score("novelty", 0.45, 0.50)
            fea_s, fea_u = _hash_score("feasibility", 0.40, 0.50)
            use_s, use_u = _hash_score("usefulness", 0.50, 0.45)
            sim_s, sim_u = _hash_score("simplicity", 0.35, 0.50)
            fit_s, fit_u = _hash_score("strategic_fit", 0.55, 0.40)

            content_dict = {
                "scores": {
                    "novelty": {"score": nov_s, "rationale": f"Novelty evaluation for {title_seed}.", "uncertainty": nov_u},
                    "feasibility": {"score": fea_s, "rationale": "Feasibility assessment based on technical primitives.", "uncertainty": fea_u},
                    "usefulness": {"score": use_s, "rationale": "Targeted value for stated engineering constraints.", "uncertainty": use_u},
                    "simplicity": {"score": sim_s, "rationale": "Mechanistic complexity analysis.", "uncertainty": sim_u},
                    "strategic_fit": {"score": fit_s, "rationale": "Alignment with Howl ecosystem decentralization goals.", "uncertainty": fit_u},
                },
                "strengths": [f"Grounded mechanism for {title_seed}", "Sovereign local-first execution"],
                "weaknesses": ["Requires operational validation under edge cases"],
                "critical_risks": ["Adoption friction if CLI is too complex"],
            }
        elif "synthesis operator" in lower_prompt or "synthesis protocol" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Unified Autonomous Guild Protocol ({has_hash})",
                        "description": "An integrated architecture combining offline test-driven bounties with bilateral reputation staking.",
                        "core_mechanism": "Multi-agent proof settlement mediated by local verifiable runtime nodes.",
                        "integrated_strengths": "Merges cryptographic security with zero-coordination asynchrony.",
                        "speculations": ["Decentralized guilds will organically form specialized niches"],
                        "evidence_needs": ["High-concurrency load testing on peer network"],
                    }
                ]
            }
        elif "constraint mutation operator" in lower_prompt or "altered constraints" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Zero-Bandwidth Sneakernet Ledger ({has_hash})",
                        "constraint_applied": "Completely Offline / Zero Internet",
                        "description": "Work and bounty proofs exchanged physically via QR codes or local Wi-Fi direct.",
                        "core_mechanism": "Delay-tolerant Merkle synchronization.",
                        "underlying_principle": "Consensus does not require simultaneous connectivity.",
                        "speculations": ["Applicable to rural and disconnected communities"],
                        "evidence_needs": ["Sync latency benchmarks"],
                    }
                ]
            }
        elif "analogical reasoning operator" in lower_prompt or "domain sources for analogy" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Mycelial Nutrient Routing Network ({has_hash})",
                        "source_domain": "Biology & Mycology",
                        "analogy_explanation": "Fungal networks route resources dynamically based on local nutrient gradients without central control.",
                        "description": "Tasks flow towards nodes with excess compute capacity like sugar along fungal hyphae.",
                        "core_mechanism": "Gradient-based demand routing.",
                        "speculations": ["Prevents compute bottlenecks organically"],
                        "evidence_needs": ["Simulated network flow equilibrium"],
                    }
                ]
            }
        elif "extreme solutions operator" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"1-Second Micro-Task Auction ({has_hash})",
                        "extreme_dimension": "Task duration reduced to 1 second",
                        "description": "Work broken into sub-second atomic instructions solved by distributed agents.",
                        "core_mechanism": "Ultra-fine-grained task pipelining.",
                        "usable_underlying_principle": "Decomposition reduces review cost to zero.",
                        "speculations": ["Eliminates traditional project management entirely"],
                        "evidence_needs": ["Pipelining latency overhead measurement"],
                    }
                ]
            }
        elif "simplification" in lower_prompt or "dissolv" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Self-Verifying Deliverable Contracts ({has_hash})",
                        "eliminated_need": "Eliminated the need for human managers and milestone negotiations",
                        "description": "The specification itself compiles into an executable test suite; passing it automatically settles the contract.",
                        "core_mechanism": "Specification as execution arbiter.",
                        "speculations": ["Removes 90% of contract dispute friction"],
                        "evidence_needs": ["Coverage of specification language"],
                    }
                ]
            }
        elif "substitution operator" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Reputation Bonds Replacing Traditional Employment ({has_hash})",
                        "conventional_element": "Traditional hourly salary and performance reviews",
                        "substituted_replacement": "Cryptographic reputation escrow bonded to verified software releases",
                        "description": "Workers draw continuous streams based on verifiable test coverage and maintenance proofs.",
                        "core_mechanism": "Automated reputation streaming.",
                        "speculations": ["Outperforms traditional corporate equity vesting"],
                        "evidence_needs": ["Economic simulation of worker cash-flow stability"],
                    }
                ]
            }
        elif "forced combination operator" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Hybrid Sovereign Escrow Guild ({has_hash})",
                        "description": "Emergent integration combining bilateral escrow staking with delay-tolerant synchronization.",
                        "core_mechanism": "Offline-ready verifiable work settlement.",
                        "emergent_advantage": "Allows sovereign remote contributors to work offline while guaranteeing fraud-proof settlement.",
                        "speculations": ["High adoption in emerging markets"],
                        "evidence_needs": ["Field tests in offline environments"],
                    }
                ]
            }
        elif "second-order exploration operator" in lower_prompt:
            content_dict = {
                "ideas": [
                    {
                        "title": f"Second-Order Macro Stabilizer ({has_hash})",
                        "second_order_shift": "Market saturation causes micro-bounty race to the bottom",
                        "description": "Dynamic reserve pool that subsidizes niche, highly technical open-source components.",
                        "core_mechanism": "Quadratic funding reserves.",
                        "speculations": ["Sustains long-term maintainers"],
                        "evidence_needs": ["Quadratic funding simulation"],
                    }
                ]
            }
        else:
            # Independent Branching / General Exploration
            content_dict = {
                "ideas": [
                    {
                        "title": f"Decentralized Task Registry ({has_hash}-A)",
                        "description": "An open distributed registry where engineering tasks are published as reproducible verification fixtures.",
                        "core_mechanism": "Verifiable task execution logs evaluated by sovereign worker nodes.",
                        "unconventional_aspect": "Tasks are executed and proven before any coordination occurs.",
                        "assumptions": ["Tasks can be formally verified"],
                        "speculations": ["Massive talent pool expansion"],
                        "evidence_needs": ["Sandboxing verification overhead"],
                    },
                    {
                        "title": f"Mutual Credit Engineering Guilds ({has_hash}-B)",
                        "description": "Sovereign developer clusters pooling liquidity and trading micro-commitments without corporate intermediaries.",
                        "core_mechanism": "Bilateral credit rings with cryptographic dispute resolution.",
                        "unconventional_aspect": "Eliminates payroll intermediaries completely.",
                        "assumptions": ["Mutual trust can be bootstrapped locally"],
                        "speculations": ["Guilds will outcompete centralized software houses"],
                        "evidence_needs": ["Credit ring default rate simulation"],
                    },
                ]
            }

        content_str = json.dumps(content_dict, indent=2)
        return ProviderResponse(
            content=content_str,
            model=self.model_name,
            provider="deterministic",
            structured_data=content_dict,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(content_str.split()),
            latency_seconds=round(time.time() - start_time, 4),
        )
