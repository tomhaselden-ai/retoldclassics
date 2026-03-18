from collections import defaultdict
from typing import Any

from backend.adaptive.adaptive_engine import (
    compute_reader_proficiency,
    recommend_game_difficulty,
    recommend_story_difficulty,
    recommend_vocabulary_difficulty,
)


def _safe_average(values: list[int | float | None]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return round(sum(cleaned) / len(cleaned), 2)


def _build_focus_areas(
    progress,
    vocabulary_progress,
    game_results,
    stories,
) -> list[dict[str, str | int]]:
    focus_areas: list[dict[str, str | int]] = []

    needs_practice = sum(1 for item in vocabulary_progress if (item.mastery_level or 0) < 2)
    mastered = sum(1 for item in vocabulary_progress if (item.mastery_level or 0) >= 3)
    average_score = _safe_average([item.score for item in game_results])

    if needs_practice >= 5:
        focus_areas.append(
            {
                "category": "vocabulary",
                "priority": 1,
                "message": "Several tracked words still need reinforcement through practice and story reuse.",
            }
        )
    elif vocabulary_progress and mastered == 0:
        focus_areas.append(
            {
                "category": "vocabulary",
                "priority": 2,
                "message": "Vocabulary exposure is active, but mastery has not stabilized yet.",
            }
        )

    if average_score is not None and average_score < 60:
        focus_areas.append(
            {
                "category": "games",
                "priority": 1,
                "message": "Recent game results suggest comprehension or recall difficulty at the current level.",
            }
        )
    elif game_results and average_score is not None and average_score < 75:
        focus_areas.append(
            {
                "category": "games",
                "priority": 2,
                "message": "Game performance is steady but could improve with more guided practice.",
            }
        )

    if (progress.stories_read or 0) < 5 or not stories:
        focus_areas.append(
            {
                "category": "story_engagement",
                "priority": 2,
                "message": "More recent story reading would improve continuity and vocabulary growth.",
            }
        )

    if (progress.reading_speed or 0) > 0 and (progress.reading_speed or 0) < 75:
        focus_areas.append(
            {
                "category": "reading_fluency",
                "priority": 3,
                "message": "Reading speed is still developing and may benefit from shorter story sessions.",
            }
        )

    if not focus_areas:
        focus_areas.append(
            {
                "category": "momentum",
                "priority": 3,
                "message": "Current learning signals look balanced. Maintain regular reading and game practice.",
            }
        )

    return sorted(focus_areas, key=lambda item: (int(item["priority"]), str(item["category"])))[:3]


def _build_strengths(progress, vocabulary_progress, game_results) -> list[str]:
    strengths: list[str] = []

    mastered = sum(1 for item in vocabulary_progress if (item.mastery_level or 0) >= 3)
    average_score = _safe_average([item.score for item in game_results])

    if mastered >= 10:
        strengths.append("Strong vocabulary retention across practiced words.")
    elif mastered >= 3:
        strengths.append("Vocabulary mastery is building steadily.")

    if average_score is not None and average_score >= 85:
        strengths.append("Game performance is consistently strong.")

    if (progress.stories_read or 0) >= 10:
        strengths.append("Story engagement is well established.")

    if (progress.reading_speed or 0) >= 130:
        strengths.append("Reading fluency is trending above the expected baseline.")

    if not strengths:
        strengths.append("Learning data is still early; current activity is establishing the baseline.")

    return strengths[:3]


def build_reader_learning_insights(
    reader,
    progress,
    vocabulary_progress,
    game_results,
    stories,
) -> dict[str, Any]:
    proficiency = compute_reader_proficiency(
        progress,
        vocabulary_progress,
        game_results,
        reader.reading_level,
    )
    recommended_story_difficulty = recommend_story_difficulty(progress, reader.reading_level)
    recommended_vocabulary_difficulty = recommend_vocabulary_difficulty(vocabulary_progress)
    recommended_game_difficulty = recommend_game_difficulty(game_results)

    total_tracked_words = len(vocabulary_progress)
    mastered_words = sum(1 for item in vocabulary_progress if (item.mastery_level or 0) >= 3)
    developing_words = sum(1 for item in vocabulary_progress if 1 <= (item.mastery_level or 0) < 3)
    needs_practice_words = sum(1 for item in vocabulary_progress if (item.mastery_level or 0) < 2)

    by_game_type: dict[str, list[int]] = defaultdict(list)
    for item in game_results:
        if item.game_type and item.score is not None:
            by_game_type[item.game_type].append(item.score)

    strongest_game_type = None
    if by_game_type:
        strongest_game_type = max(
            by_game_type.items(),
            key=lambda pair: (_safe_average(pair[1]) or 0, len(pair[1])),
        )[0]

    latest_story = stories[0] if stories else None
    latest_game = game_results[0] if game_results else None

    return {
        "reader_id": reader.reader_id,
        "name": reader.name,
        "age": reader.age,
        "reading_level": reader.reading_level,
        "trait_focus": reader.trait_focus,
        "proficiency": proficiency,
        "reading_summary": {
            "stories_read": progress.stories_read or 0,
            "words_mastered": progress.words_mastered or 0,
            "reading_speed": progress.reading_speed,
            "preferred_themes": progress.preferred_themes,
            "traits_reinforced": progress.traits_reinforced,
        },
        "story_summary": {
            "recent_story_count": len(stories),
            "latest_story_title": latest_story.title if latest_story else None,
            "latest_story_at": latest_story.updated_at if latest_story else None,
        },
        "vocabulary_summary": {
            "tracked_words": total_tracked_words,
            "mastered_words": mastered_words,
            "developing_words": developing_words,
            "needs_practice_words": needs_practice_words,
            "recent_words": [
                {
                    "word_id": item.word_id,
                    "word": item.word,
                    "difficulty_level": item.difficulty_level,
                    "mastery_level": item.mastery_level,
                    "last_seen": item.last_seen,
                }
                for item in vocabulary_progress[:5]
            ],
        },
        "game_summary": {
            "total_games_played": len(game_results),
            "average_score": _safe_average([item.score for item in game_results]),
            "average_duration_seconds": _safe_average([item.duration_seconds for item in game_results]),
            "strongest_game_type": strongest_game_type,
            "most_recent_game_type": latest_game.game_type if latest_game else None,
            "most_recent_game_at": latest_game.played_at if latest_game else None,
        },
        "recommendations": {
            "recommended_story_difficulty": recommended_story_difficulty,
            "recommended_vocabulary_difficulty": recommended_vocabulary_difficulty,
            "recommended_game_difficulty": recommended_game_difficulty,
        },
        "strengths": _build_strengths(progress, vocabulary_progress, game_results),
        "focus_areas": _build_focus_areas(progress, vocabulary_progress, game_results, stories),
    }


def build_account_learning_insights(account_id: int, reader_insights: list[dict[str, Any]]) -> dict[str, Any]:
    average_scores = [
        item["game_summary"]["average_score"]
        for item in reader_insights
        if item["game_summary"]["average_score"] is not None
    ]

    return {
        "account_id": account_id,
        "reader_count": len(reader_insights),
        "aggregate_statistics": {
            "stories_read": sum(item["reading_summary"]["stories_read"] for item in reader_insights),
            "words_mastered": sum(item["reading_summary"]["words_mastered"] for item in reader_insights),
            "tracked_words": sum(item["vocabulary_summary"]["tracked_words"] for item in reader_insights),
            "games_played": sum(item["game_summary"]["total_games_played"] for item in reader_insights),
            "average_game_score": _safe_average(average_scores),
        },
        "readers": [
            {
                "reader_id": item["reader_id"],
                "name": item["name"],
                "reading_level": item["reading_level"],
                "proficiency": item["proficiency"],
                "stories_read": item["reading_summary"]["stories_read"],
                "words_mastered": item["reading_summary"]["words_mastered"],
                "average_game_score": item["game_summary"]["average_score"],
                "strengths": item["strengths"],
                "focus_areas": item["focus_areas"],
                "recommendations": item["recommendations"],
            }
            for item in reader_insights
        ],
    }
