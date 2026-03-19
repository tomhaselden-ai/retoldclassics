import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ReaderAreaNav } from "../components/ReaderAreaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { getReaderGoals, type GoalResponse, type ReaderGoalsResponse } from "../services/api";
import { useAuth } from "../services/auth";

function goalLink(readerId: number, goal: GoalResponse): string {
  if (goal.goal_type === "games_played") {
    return `/reader/${readerId}/games`;
  }
  if (goal.goal_type === "stories_read") {
    return `/reader/${readerId}/books`;
  }
  return `/reader/${readerId}/words`;
}

function goalButtonLabel(goal: GoalResponse): string {
  if (goal.goal_type === "games_played") {
    return "Play a game";
  }
  if (goal.goal_type === "stories_read") {
    return "Read now";
  }
  return "Practice words";
}

function prettyGoalType(value: string): string {
  return value.split("_").join(" ");
}

export function ReaderGoalsPage() {
  const { readerId } = useParams();
  const { token } = useAuth();
  const [summary, setSummary] = useState<ReaderGoalsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    setLoading(true);
    getReaderGoals(Number(readerId), token)
      .then((payload) => {
        setSummary(payload);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to open reader goals."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

  if (loading) {
    return <LoadingState label="Opening the goals board..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!summary) {
    return <ErrorState message="Goals board unavailable." />;
  }

  const activeGoals = summary.goals.filter((goal) => goal.is_active && goal.progress.status !== "completed");
  const completedGoals = summary.goals.filter((goal) => goal.progress.status === "completed");
  const pausedGoals = summary.goals.filter((goal) => !goal.is_active && goal.progress.status !== "completed");

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Goals board</p>
            <h1>{summary.reader.name ?? "Reader"}&apos;s next steps</h1>
            <p>These are the goals your family has set for reading, words, and practice. Pick one and keep going.</p>
          </div>
          <div className="library-action-row">
            <Link to={`/reader/${summary.reader.reader_id}`} className="btn btn--secondary btn-tone-neutral ghost-button">
              Reader Home
            </Link>
          </div>
        </div>

        <ReaderAreaNav readerId={summary.reader.reader_id} />
      </section>

      <section className="panel">
        <div className="dashboard-summary-grid">
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Active goals</p>
            <h3>{activeGoals.length}</h3>
            <p>These are the goals you can work on right now.</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Completed goals</p>
            <h3>{completedGoals.length}</h3>
            <p>Finished goals stay here as a reminder of progress.</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Paused goals</p>
            <h3>{pausedGoals.length}</h3>
            <p>These can come back later when your family is ready.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Do next</p>
            <h2>Active goals</h2>
          </div>
        </div>

        {activeGoals.length > 0 ? (
          <div className="goal-card-grid">
            {activeGoals.map((goal) => (
              <article key={goal.goal_id} className="goal-card">
                <p className="eyebrow">{prettyGoalType(goal.goal_type)}</p>
                <h3>{goal.title}</h3>
                <p>
                  {goal.progress.current_value} of {goal.progress.target_value} done
                </p>
                <div className="goal-progress-bar">
                  <span style={{ width: `${goal.progress.progress_percent}%` }} />
                </div>
                <div className="goal-progress-row">
                  <strong>{goal.progress.progress_percent}%</strong>
                  <span>{goal.progress.status}</span>
                </div>
                <div className="library-action-row">
                  <Link to={goalLink(summary.reader.reader_id, goal)} className="btn btn--primary btn-tone-gold primary-button">
                    {goalButtonLabel(goal)}
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="status-card">
            <h3>No active goals yet</h3>
            <p>Your family can add goals from the parent area when you are ready for a new challenge.</p>
          </div>
        )}
      </section>

      {completedGoals.length > 0 ? (
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Finished</p>
              <h2>Completed goals</h2>
            </div>
          </div>

          <div className="goal-card-grid">
            {completedGoals.map((goal) => (
              <article key={goal.goal_id} className="goal-card goal-card-complete">
                <p className="eyebrow">{prettyGoalType(goal.goal_type)}</p>
                <h3>{goal.title}</h3>
                <p>
                  Great work. You reached {goal.progress.current_value} out of {goal.progress.target_value}.
                </p>
                <div className="goal-progress-bar">
                  <span style={{ width: "100%" }} />
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {pausedGoals.length > 0 ? (
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Resting</p>
              <h2>Paused goals</h2>
            </div>
          </div>

          <div className="goal-card-grid">
            {pausedGoals.map((goal) => (
              <article key={goal.goal_id} className="goal-card">
                <p className="eyebrow">{prettyGoalType(goal.goal_type)}</p>
                <h3>{goal.title}</h3>
                <p>This goal is paused right now. It can come back later from the parent area.</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
