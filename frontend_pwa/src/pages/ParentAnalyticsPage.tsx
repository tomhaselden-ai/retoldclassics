import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { getParentAnalytics, type ParentAnalyticsResponse } from "../services/api";
import { useAuth } from "../services/auth";

function formatGameType(value: string | null): string {
  if (!value) {
    return "Not enough data";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatPracticeTime(totalSeconds: number): string {
  if (totalSeconds < 60) {
    return `${totalSeconds} sec`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds > 0 ? `${minutes} min ${seconds} sec` : `${minutes} min`;
}

function describeTrend(value: string): string {
  if (value === "improving") {
    return "Improving";
  }
  if (value === "needs_support") {
    return "Needs support";
  }
  if (value === "steady") {
    return "Steady";
  }
  return "Building";
}

export function ParentAnalyticsPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<ParentAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    setLoading(true);
    getParentAnalytics(token)
      .then((payload) => {
        setSummary(payload);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load parent analytics."))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent analytics</p>
            <h1>Family analytics and goal progress</h1>
            <p>Keep family totals, reader focus areas, and goal progress together in one clear parent view.</p>
          </div>
          <div className="library-action-row">
            <Link to="/parent" className="btn btn--secondary btn-tone-neutral primary-button">
              Parent area
            </Link>
            <Link to="/parent/goals" className="btn btn--admin btn-tone-plum ghost-button">
              Manage goals
            </Link>
            <Link to="/chooser" className="btn btn--secondary btn-tone-neutral ghost-button">
              Family chooser
            </Link>
          </div>
        </div>

        {loading ? <LoadingState label="Loading family analytics..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && summary ? (
          <>
            <div className="dashboard-summary-grid">
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Stories read</p>
              <h3>{summary.aggregate_statistics.stories_read}</h3>
              <p>Combined reading activity across the family account.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Words mastered</p>
              <h3>{summary.aggregate_statistics.words_mastered}</h3>
              <p>Vocabulary growth visible to the parent layer.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Tracked words</p>
              <h3>{summary.aggregate_statistics.tracked_words}</h3>
              <p>Total vocabulary records currently shaping recommendations.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Games played</p>
              <h3>{summary.aggregate_statistics.games_played}</h3>
              <p>Practice sessions contributing to the family learning picture.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Active goals</p>
              <h3>{summary.goal_summary.active_goal_count}</h3>
              <p>Goals currently shaping family reading and practice.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Completed goals</p>
              <h3>{summary.goal_summary.completed_goal_count}</h3>
              <p>Finished goals already banked as progress wins.</p>
            </article>
            </div>

            <div className="reader-grid">
            <article className="reader-panel">
              <div>
                <p className="eyebrow">Game practice</p>
                <h3>Family practice snapshot</h3>
                <p>
                  {summary.aggregate_game_practice.sessions_this_week} sessions this week |{" "}
                  {summary.aggregate_game_practice.words_practiced} words practiced |{" "}
                  {summary.aggregate_game_practice.average_success_rate ?? "—"}% success
                </p>
                <p>
                  Time spent: {formatPracticeTime(summary.aggregate_game_practice.practice_time_seconds)} | Trend:{" "}
                  {describeTrend(summary.aggregate_game_practice.improvement_trend)}
                </p>
                <p>
                  Strongest game: {formatGameType(summary.aggregate_game_practice.strongest_game_type)} | Needs support:{" "}
                  {formatGameType(summary.aggregate_game_practice.weakest_game_type)}
                </p>
              </div>
            </article>

            <article className="reader-panel">
              <div>
                <p className="eyebrow">Repeated missed words</p>
                <h3>Words worth another look</h3>
              </div>
              <div className="tooling-mini-list">
                {summary.aggregate_game_practice.repeated_missed_words.length > 0 ? (
                  summary.aggregate_game_practice.repeated_missed_words.map((item) => (
                    <div key={item.word_text} className="tooling-mini-card">
                      <strong>{item.word_text}</strong>
                      <p>Missed {item.miss_count} times in saved V1 sessions.</p>
                    </div>
                  ))
                ) : (
                  <p>No repeated misses yet in the new game system.</p>
                )}
              </div>
            </article>
            </div>
          </>
        ) : null}
      </section>

      {!loading && summary ? (
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Reader highlights</p>
              <h2>What to notice next</h2>
            </div>
          </div>

          <div className="reader-grid">
            {summary.readers.map((reader) => (
              <article key={reader.reader_id} className="reader-panel">
                <div>
                  <h3>{reader.name ?? `Reader ${reader.reader_id}`}</h3>
                  <p>
                    {reader.proficiency} | {reader.stories_read} stories | {reader.words_mastered} words mastered
                  </p>
                  <p>
                    Game practice: {reader.game_practice.sessions_this_week} sessions this week |{" "}
                    {reader.game_practice.words_practiced} words | {reader.game_practice.average_success_rate ?? "—"}%
                    {" "}success
                  </p>
                  <p>
                    Strongest: {formatGameType(reader.game_practice.strongest_game_type)} | Support next:{" "}
                    {formatGameType(reader.game_practice.weakest_game_type)}
                  </p>
                  {reader.focus_areas[0] ? <p>Focus next: {reader.focus_areas[0].message}</p> : null}
                  {reader.strengths[0] ? <p>Strength: {reader.strengths[0]}</p> : null}
                  <p>
                    Goals: {reader.goals.filter((goal) => goal.is_active).length} active |{" "}
                    {reader.goals.filter((goal) => goal.progress.status === "completed").length} completed
                  </p>
                </div>
                <div className="tooling-mini-list">
                  {reader.game_practice.repeated_missed_words.length > 0 ? (
                    reader.game_practice.repeated_missed_words.slice(0, 3).map((item) => (
                      <div key={`${reader.reader_id}-${item.word_text}`} className="tooling-mini-card">
                        <strong>{item.word_text}</strong>
                        <p>Missed {item.miss_count} times.</p>
                      </div>
                    ))
                  ) : (
                    <div className="tooling-mini-card">
                      <strong>Missed words</strong>
                      <p>No repeated misses yet in saved V1 sessions.</p>
                    </div>
                  )}
                </div>
                <div className="reader-panel-actions">
                  <Link className="btn btn--admin btn-tone-plum primary-link" to={`/parent/readers/${reader.reader_id}`}>
                    Open reader overview
                  </Link>
                  <Link className="btn btn--admin btn-tone-plum ghost-button" to="/parent/goals">
                    View goals
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
