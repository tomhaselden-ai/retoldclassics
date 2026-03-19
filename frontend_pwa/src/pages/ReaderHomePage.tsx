import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ReaderAreaNav } from "../components/ReaderAreaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { getReaderHomeSummary, type ReaderHomeSummaryResponse } from "../services/api";
import { useAuth } from "../services/auth";

function normalizeTraitFocus(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  }
  if (typeof value === "string" && value.trim()) {
    return [value.trim()];
  }
  return [];
}

function formatGameType(value: string | null): string {
  if (!value) {
    return "Game";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function ReaderHomePage() {
  const { readerId } = useParams();
  const { token } = useAuth();
  const [summary, setSummary] = useState<ReaderHomeSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    setLoading(true);
    getReaderHomeSummary(Number(readerId), token)
      .then((payload) => {
        setSummary(payload);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to open the reader home."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

  if (loading) {
    return <LoadingState label="Opening the reader home..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!summary) {
    return <ErrorState message="Reader home unavailable." />;
  }

  const traits = normalizeTraitFocus(summary.reader.trait_focus);

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Reader home</p>
            <h1>Welcome back, {summary.reader.name ?? "reader"}</h1>
            <p>
              A calm place to keep reading, practice words, play quick games, and follow the next step in this
              reader&apos;s path.
            </p>
          </div>
          <div className="library-action-row">
            <Link to="/chooser" className="btn btn--secondary btn-tone-neutral ghost-button">
              Family chooser
            </Link>
            <Link to="/classics" className="btn btn--secondary btn-tone-sky ghost-button">
              Browse Classics
            </Link>
          </div>
        </div>

        <ReaderAreaNav readerId={summary.reader.reader_id} />

        <div className="reader-home-hero">
          <article className="reader-home-story">
            <p className="eyebrow">Continue reading</p>
            <h2>{summary.continue_reading?.title ?? "Your next story will appear here"}</h2>
            <p>
              {summary.continue_reading
                ? `Jump back into ${summary.continue_reading.custom_world_name || summary.continue_reading.world_name || "your story shelf"}.`
                : "Open Books to make or choose the next adventure."}
            </p>
            <div className="library-action-row">
              {summary.continue_reading ? (
                <>
                  <Link className="btn btn--primary btn-tone-gold primary-button" to={`/reader/${summary.reader.reader_id}/books/${summary.continue_reading.story_id}/read`}>
                    Continue Story
                  </Link>
                  <Link className="btn btn--secondary btn-tone-sky ghost-button" to={`/reader/${summary.reader.reader_id}/books/${summary.continue_reading.story_id}`}>
                    Story Info
                  </Link>
                </>
              ) : (
                <Link className="btn btn--secondary btn-tone-sky primary-button" to={`/reader/${summary.reader.reader_id}/books`}>
                  Open Books
                </Link>
              )}
            </div>
          </article>

          <article className="reader-home-path">
            <p className="eyebrow">Reader path</p>
            <h3>{summary.reader_path.proficiency}</h3>
            <p>Story difficulty {summary.reader_path.recommended_story_difficulty}</p>
            <p>{summary.reader_path.goal_message}</p>
            {traits.length > 0 ? <p>Traits: {traits.join(", ")}</p> : null}
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="reader-home-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">Books</p>
            <h3>{summary.library_summary.story_count}</h3>
            <p>{summary.library_summary.world_count} universe shelves waiting for adventures.</p>
            <div className="library-action-row">
              <Link to={`/reader/${summary.reader.reader_id}/books`} className="btn btn--secondary btn-tone-sky primary-button">
                Open Books
              </Link>
            </div>
          </article>

          <article className="panel inset-panel">
            <p className="eyebrow">Words</p>
            <h3>{summary.vocabulary_summary.practice_words}</h3>
            <p>
              {summary.vocabulary_summary.recommended_word?.word
                ? `Try the word "${summary.vocabulary_summary.recommended_word.word}" next.`
                : "New practice words will appear as reading grows."}
            </p>
            <div className="library-action-row">
              <Link to={`/reader/${summary.reader.reader_id}/words`} className="btn btn--secondary btn-tone-sky primary-button">
                Open Words
              </Link>
            </div>
          </article>

          <article className="panel inset-panel">
            <p className="eyebrow">Play</p>
            <h3>Level {summary.game_summary.recommended_game_difficulty}</h3>
            <p>
              {summary.game_summary.recent_game
                ? `Last game: ${formatGameType(summary.game_summary.recent_game.game_type)}`
                : "Start with a quick game to practice story and word skills."}
            </p>
            <div className="library-action-row">
              <Link to={`/reader/${summary.reader.reader_id}/games`} className="btn btn--create btn-tone-mint primary-button">
                Play Games
              </Link>
            </div>
          </article>

          <article className="panel inset-panel">
            <p className="eyebrow">Goals</p>
            <h3>Keep going</h3>
            <p>{summary.reader_path.goal_message}</p>
            <div className="library-action-row">
              <Link to={`/reader/${summary.reader.reader_id}/goals`} className="btn btn--secondary btn-tone-sky primary-button">
                View Goals
              </Link>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
