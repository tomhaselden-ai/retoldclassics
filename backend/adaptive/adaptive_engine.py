from typing import Any


def _clamp_difficulty(value: int) -> int:
    return max(1, min(3, value))


def _reading_level_rank(reading_level: str | None) -> int:
    if not reading_level:
        return 1
    lowered = reading_level.lower()
    if "grade 5" in lowered or "grade 6" in lowered or "advanced" in lowered:
        return 3
    if "grade 3" in lowered or "grade 4" in lowered or "intermediate" in lowered:
        return 2
    return 1


def compute_reader_proficiency(progress, vocabulary_progress, game_results, reading_level: str | None) -> str:
    score = _reading_level_rank(reading_level)

    if (progress.reading_speed or 0) >= 140:
        score += 1
    elif (progress.reading_speed or 0) <= 70:
        score -= 1

    if (progress.words_mastered or 0) >= 40:
        score += 1
    elif (progress.words_mastered or 0) <= 10:
        score -= 1

    mastered_words = sum(1 for item in vocabulary_progress if (item.mastery_level or 0) >= 2)
    if mastered_words >= max(3, len(vocabulary_progress) // 2):
        score += 1

    if game_results:
        average_score = sum((item.score or 0) for item in game_results) / len(game_results)
        if average_score >= 85:
            score += 1
        elif average_score <= 50:
            score -= 1

    if (progress.stories_read or 0) >= 20:
        score += 1

    if score <= 1:
        return "Beginner"
    if score <= 3:
        return "Intermediate"
    return "Advanced"


def recommend_story_difficulty(progress, reading_level: str | None) -> int:
    recommendation = _reading_level_rank(reading_level)
    if (progress.reading_speed or 0) >= 130 and (progress.words_mastered or 0) >= 25:
        recommendation += 1
    if (progress.reading_speed or 0) <= 70 or (progress.words_mastered or 0) <= 8:
        recommendation -= 1
    return _clamp_difficulty(recommendation)


def recommend_vocabulary_difficulty(vocabulary_progress) -> int:
    low_mastery_words = [item for item in vocabulary_progress if (item.mastery_level or 0) < 2]
    if not low_mastery_words:
        return 3

    average_difficulty = sum((item.difficulty_level or 1) for item in low_mastery_words) / len(low_mastery_words)
    if average_difficulty >= 2.5:
        return 3
    if average_difficulty >= 1.5:
        return 2
    return 1


def recommend_game_difficulty(game_results) -> int:
    if not game_results:
        return 1

    average_score = sum((item.score or 0) for item in game_results) / len(game_results)
    average_difficulty = sum((item.difficulty_level or 1) for item in game_results) / len(game_results)

    recommended = round(average_difficulty)
    if average_score >= 85:
        recommended += 1
    elif average_score <= 50:
        recommended -= 1
    return _clamp_difficulty(recommended)


def build_story_parameters(progress, recommended_story_difficulty: int) -> dict[str, Any]:
    return {
        "recommended_story_difficulty": recommended_story_difficulty,
        "stories_read": progress.stories_read,
        "words_mastered": progress.words_mastered,
        "reading_speed": progress.reading_speed,
    }
