"""Round 5 1d: inbox accounting. Round 4 ended with 270 prompts and 271 answers for 246 programs: 246 first prompts + 24
preflight-retry prompts = 270, and one answer written under a key with a character missing."""
from __future__ import annotations

from typediff.llm import inbox_status

K1, K2, K3 = "e66738668643ecc8", "0123456789abcdef", "fedcba9876543210"


def _inbox(tmp_path, prompts, answers, retry=()):
    for k in prompts:
        text = "# USER\n\nbody\n" + ("\nYour previous program was rejected by the preflight lint:\nx\n" if k in retry else "")
        (tmp_path / f"{k}.prompt.md").write_text(text)
    for k in answers:
        (tmp_path / f"{k}.answer.json").write_text("{}")
    return inbox_status(tmp_path)


def test_clean_inbox(tmp_path):
    s = _inbox(tmp_path, [K1, K2], [K1, K2])
    assert (s["prompts"], s["answers"], s["answered"]) == (2, 2, 2)
    assert s["pending"] == [] and s["orphan_answers"] == {} and s["malformed_keys"] == []


def test_mistyped_answer_key_is_an_orphan_and_its_prompt_stays_pending(tmp_path):
    bad = "e6673866643ecc8"  # the Round-4 key: one '8' dropped
    s = _inbox(tmp_path, [K1, K2], [bad, K2])
    assert s["prompts"] == 2 and s["answers"] == 2 and s["answered"] == 1
    assert s["pending"] == [K1]
    assert s["orphan_answers"] == {bad: [K1]}
    assert s["malformed_keys"] == [bad]


def test_more_answers_than_prompts_is_visible(tmp_path):
    # Round-4 shape: every prompt answered (the late right-key answer) and the stray wrong-key answer still lying around
    bad = "e6673866643ecc8"
    s = _inbox(tmp_path, [K1, K2, K3], [K1, K2, K3, bad])
    assert (s["prompts"], s["answers"]) == (3, 4)
    assert s["pending"] == [] and s["orphan_answers"] == {bad: [K1]}


def test_retry_prompts_are_counted(tmp_path):
    s = _inbox(tmp_path, [K1, K2, K3], [], retry={K2, K3})
    assert s["retry_prompts"] == 2 and s["pending"] == sorted([K1, K2, K3])
