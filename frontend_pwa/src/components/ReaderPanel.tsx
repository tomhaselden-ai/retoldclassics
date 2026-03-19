import { Link } from "react-router-dom";

import type {
  AdaptiveProfile,
  AdaptiveRecommendations,
  Reader,
  ReaderDashboardData,
  ReaderLearningInsights,
} from "../services/api";

interface ReaderPanelProps {
  reader: Reader;
  deleting: boolean;
  dashboard?: ReaderDashboardData | null;
  adaptiveProfile?: AdaptiveProfile | null;
  adaptiveRecommendations?: AdaptiveRecommendations | null;
  learningInsights?: ReaderLearningInsights | null;
  onDelete: (reader: Reader) => void;
  onEdit: (reader: Reader) => void;
}

export function ReaderPanel({
  reader,
  deleting,
  dashboard,
  adaptiveProfile,
  adaptiveRecommendations,
  learningInsights,
  onDelete,
  onEdit,
}: ReaderPanelProps) {
  return (
    <article className="reader-panel">
      <div>
        <h3>{reader.name ?? "Young Reader"}</h3>
        <p>
          Age {reader.age ?? "?"} · {reader.reading_level ?? "Emerging reader"}
        </p>
        {adaptiveProfile ? (
          <p>Proficiency: {adaptiveProfile.proficiency} · Story difficulty {adaptiveProfile.recommended_story_difficulty}</p>
        ) : null}
        {dashboard ? (
          <p>
            {dashboard.reading_statistics.stories_read ?? 0} stories · {dashboard.reading_statistics.words_mastered ?? 0} words mastered
          </p>
        ) : null}
        {learningInsights?.focus_areas?.[0] ? <p>Focus next: {learningInsights.focus_areas[0].message}</p> : null}
        {adaptiveRecommendations?.recommended_words?.[0]?.word ? (
          <p>Practice word: {adaptiveRecommendations.recommended_words[0].word}</p>
        ) : null}
      </div>
      <div className="reader-panel-actions">
        <Link className="btn btn--secondary btn-tone-sky primary-link" to={`/reader/${reader.reader_id}`}>
          Open reader home
        </Link>
        <Link className="btn btn--secondary btn-tone-sky btn-size-compact ghost-button" to={`/reader/${reader.reader_id}/books`}>
          Books
        </Link>
        <Link className="btn btn--secondary btn-tone-sky btn-size-compact ghost-button" to={`/reader/${reader.reader_id}/games`}>
          Game shelf
        </Link>
        <Link className="btn btn--secondary btn-tone-sky btn-size-compact ghost-button" to={`/reader/${reader.reader_id}/words`}>
          Vocabulary shelf
        </Link>
        <button type="button" className="btn btn--admin btn-tone-plum btn-size-compact ghost-button" onClick={() => onEdit(reader)}>
          Edit
        </button>
        <button type="button" className="btn btn--danger btn-tone-danger btn-size-compact ghost-button" onClick={() => onDelete(reader)} disabled={deleting}>
          {deleting ? "Removing..." : "Delete"}
        </button>
      </div>
    </article>
  );
}
