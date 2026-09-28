"""
Lab 11 — Main Entry Point

Chạy từ **gốc repo** (không cần ``cd src``):

    python src/main.py              # Core: Checkpoint 2 → 3 → 4
    python src/main.py --part 2     # Checkpoint 2 — guardrails
    python src/main.py --part 3     # Checkpoint 3 — pipeline / results.json
    python src/main.py --part 4     # Checkpoint 4 — Red / Red Advance

File JSON luôn ghi vào ``<repo>/outputs/`` (không phụ thuộc thư mục hiện tại).

Tham khảo (không chấm, không có CLI): ``src/testing/``, ``src/hitl/``.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Cho phép chạy ``python src/main.py`` từ gốc repo
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from core.config import setup_api_key


async def part2_guardrails():
    """Checkpoint 2: input + output guardrails."""
    print("\n" + "=" * 60)
    print("CHECKPOINT 2: Guardrails")
    print("=" * 60)

    print("\n--- Input Guardrails ---")
    from guardrails.input_guardrails import (
        test_injection_detection,
        test_topic_filter,
        test_input_plugin,
    )
    test_injection_detection()
    print()
    test_topic_filter()
    print()
    await test_input_plugin()

    print("\n--- Output Guardrails ---")
    from guardrails.output_guardrails import test_content_filter
    test_content_filter()
    print("(LLM-as-Judge / NeMo — optional, skipped)")


async def part3_assignment_suite():
    """Checkpoint 3: defense suite → outputs/results.json."""
    print("\n" + "=" * 60)
    print("CHECKPOINT 3: Assignment suite → outputs/*.json")
    print("=" * 60)

    from assignment.pipeline import (
        build_production_plugins,
        build_observability,
        run_assignment_suite,
    )

    try:
        plugins = build_production_plugins(use_llm_judge=False)
        audit, monitor = build_observability()
        pipeline = {"plugins": plugins, "audit": audit, "monitor": monitor}
        result = await run_assignment_suite(pipeline)
        print("Suite finished.")
        print("Wrote outputs under repo outputs/")
        return result
    except NotImplementedError as e:
        print(
            "Chưa xong Checkpoint 3 (src/assignment/pipeline.py). "
            "Hoàn thành rồi chạy lại từ gốc repo:\n"
            "  python src/main.py --part 3"
        )
        print(f"Detail: {e}")
        return None


async def part4_attacks():
    """Checkpoint 4: attack Red, then Red Advance (bonus)."""
    print("\n" + "=" * 60)
    print("CHECKPOINT 4: Red + Red Advance")
    print("=" * 60)

    from agents.agent import create_red_agent_default
    from agents.guards_agent import create_red_agent_advance
    from attacks.attacks import run_attacks, save_attack_results

    red_default, red_default_runner = create_red_agent_default()

    print("\n--- Attacks on Red ---")
    unsafe_results = await run_attacks(
        red_default, red_default_runner, target_name="red_default"
    )

    print("\n--- Attacks on Red Advance (bonus B2 tối đa +10 nếu LEAKED; chọn 1) ---")
    red_advance, red_advance_runner = create_red_agent_advance()
    guards_results = await run_attacks(
        red_advance, red_advance_runner, target_name="red_advance"
    )

    save_attack_results(
        unsafe_results=unsafe_results,
        guards_results=guards_results,
        ai_attacks=None,
    )

    red_leaks = sum(1 for r in unsafe_results if r.get("leaked"))
    bonus_leaks = sum(1 for r in guards_results if r.get("leaked"))
    print("\n" + "=" * 60)
    print(
        f"Red leaks (B1 tối đa +5): {red_leaks}  |  "
        f"Red Advance leaks (B2 tối đa +10): {bonus_leaks}  "
        "→ chọn MỘT bonus (B1 hoặc B2); grader replay"
    )
    from core.config import is_harder_model, provider_label

    if is_harder_model():
        print(f"Đang dùng model khó ({provider_label()}) — tuỳ chọn khi săn bonus.")
    print("=" * 60)

    return {
        "red_default": unsafe_results,
        "red_advance": guards_results,
        "unsafe": unsafe_results,
        "guards": guards_results,
    }


async def main(parts=None):
    setup_api_key()

    if parts is None:
        parts = [2, 3, 4]  # Core: CP2 → CP3 → CP4

    for part in parts:
        if part == 2:
            await part2_guardrails()
        elif part == 3:
            await part3_assignment_suite()
        elif part == 4:
            await part4_attacks()
        else:
            print(f"Unknown part: {part}. Dùng --part 2, 3, hoặc 4.")

    print("\n" + "=" * 60)
    print("Lab 11 complete! Check your results above.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Lab 11: Guardrails / HITL / Red Team — "
            "--part khớp Checkpoint (2, 3, 4)"
        )
    )
    parser.add_argument(
        "--part",
        type=int,
        choices=[2, 3, 4],
        help="2=CP2 guardrails · 3=CP3 suite · 4=CP4 red-team",
    )
    args = parser.parse_args()

    if args.part:
        asyncio.run(main(parts=[args.part]))
    else:
        asyncio.run(main())
