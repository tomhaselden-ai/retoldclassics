import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  createReaderGoal,
  getParentGoals,
  updateParentGoal,
  type GoalResponse,
  type ParentGoalsResponse,
} from "../services/api";
import { useAuth } from "../services/auth";

const GOAL_OPTIONS = [
  { value: "stories_read", label: "Stories read" },
  { value: "words_mastered", label: "Words mastered" },
  { value: "tracked_words", label: "Tracked words" },
  { value: "games_played", label: "Games played" },
];

function formatGoalType(value: string): string {
  const match = GOAL_OPTIONS.find((option) => option.value === value);
  return match?.label ?? value;
}

export function ParentGoalsPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<ParentGoalsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [creatingReaderId, setCreatingReaderId] = useState<number | null>(null);
  const [createDraft, setCreateDraft] = useState({ goal_type: "stories_read", target_value: "5", title: "" });
  const [editingGoalId, setEditingGoalId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState({ title: "", target_value: "1", is_active: true });

  async function loadGoals(activeToken: string) {
    const payload = await getParentGoals(activeToken);
    setSummary(payload);
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    setLoading(true);
    loadGoals(token)
      .then(() => setError(null))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load family goals."))
      .finally(() => setLoading(false));
  }, [token]);

  const readers = useMemo(() => summary?.readers ?? [], [summary]);

  async function refreshGoals() {
    if (!token) {
      return;
    }
    await loadGoals(token);
  }

  async function handleCreateGoal(readerId: number) {
    if (!token) {
      return;
    }

    try {
      await createReaderGoal(
        readerId,
        {
          goal_type: createDraft.goal_type,
          target_value: Number(createDraft.target_value),
          title: createDraft.title.trim() || null,
        },
        token,
      );
      await refreshGoals();
      setNotice("Goal created.");
      setCreatingReaderId(null);
      setCreateDraft({ goal_type: "stories_read", target_value: "5", title: "" });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create goal.");
    }
  }

  function startEditingGoal(goal: GoalResponse) {
    setEditingGoalId(goal.goal_id);
    setEditDraft({
      title: goal.title,
      target_value: String(goal.target_value),
      is_active: goal.is_active,
    });
    setNotice(null);
  }

  async function handleUpdateGoal(goalId: number) {
    if (!token) {
      return;
    }

    try {
      await updateParentGoal(
        goalId,
        {
          title: editDraft.title.trim() || null,
          target_value: Number(editDraft.target_value),
          is_active: editDraft.is_active,
        },
        token,
      );
      await refreshGoals();
      setEditingGoalId(null);
      setNotice("Goal updated.");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update goal.");
    }
  }

  async function handleToggleGoal(goal: GoalResponse) {
    if (!token) {
      return;
    }

    try {
      await updateParentGoal(
        goal.goal_id,
        {
          title: goal.title,
          target_value: goal.target_value,
          is_active: !goal.is_active,
        },
        token,
      );
      await refreshGoals();
      setNotice(goal.is_active ? "Goal paused." : "Goal reactivated.");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update goal status.");
    }
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent goals</p>
            <h1>Guide reading progress with family goals</h1>
            <p>
              Set simple goals for each reader, keep progress visible, and pause or reactivate goals without leaving
              the parent area.
            </p>
          </div>
          <div className="library-action-row">
            <Link to="/parent" className="ghost-button">
              Parent area
            </Link>
            <Link to="/parent/analytics" className="primary-button">
              Analytics
            </Link>
            <Link to="/chooser" className="ghost-button">
              Family chooser
            </Link>
          </div>
        </div>

        {loading ? <LoadingState label="Loading family goals..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && summary ? (
          <div className="dashboard-summary-grid">
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Active goals</p>
              <h3>{summary.active_goal_count}</h3>
              <p>Goals currently shaping what each reader should do next.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Completed goals</p>
              <h3>{summary.completed_goal_count}</h3>
              <p>Goals already completed across the family account.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Readers with goals</p>
              <h3>{summary.readers.filter((reader) => reader.goals.length > 0).length}</h3>
              <p>Readers currently using the live Phase 6 goals system.</p>
            </article>
          </div>
        ) : null}

        {notice ? (
          <div className="status-card dashboard-notice-card">
            <h3>Saved</h3>
            <p>{notice}</p>
          </div>
        ) : null}
      </section>

      {!loading && summary ? (
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Reader goals</p>
              <h2>Manage goals by reader</h2>
              <p>Each reader keeps their own goal list so parents can set age-appropriate next steps.</p>
            </div>
          </div>

          <div className="reader-grid">
            {readers.map((reader) => (
              <article key={reader.reader_id} className="reader-panel">
                <div className="section-heading">
                  <div>
                    <h3>{reader.name ?? `Reader ${reader.reader_id}`}</h3>
                    <p>
                      {reader.proficiency} | {reader.reading_level ?? "Reader path still growing"}
                    </p>
                  </div>
                  <div className="reader-panel-actions">
                    <Link className="ghost-button" to={`/parent/readers/${reader.reader_id}`}>
                      Reader workspace
                    </Link>
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => {
                        setCreatingReaderId((current) => (current === reader.reader_id ? null : reader.reader_id));
                        setEditingGoalId(null);
                        setNotice(null);
                      }}
                    >
                      {creatingReaderId === reader.reader_id ? "Close new goal" : "Add goal"}
                    </button>
                  </div>
                </div>

                {creatingReaderId === reader.reader_id ? (
                  <div className="goal-form-grid">
                    <label className="field">
                      <span>Goal type</span>
                      <select
                        value={createDraft.goal_type}
                        onChange={(event) => setCreateDraft((draft) => ({ ...draft, goal_type: event.target.value }))}
                      >
                        {GOAL_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Target</span>
                      <input
                        type="number"
                        min="1"
                        value={createDraft.target_value}
                        onChange={(event) => setCreateDraft((draft) => ({ ...draft, target_value: event.target.value }))}
                      />
                    </label>
                    <label className="field goal-form-span">
                      <span>Title</span>
                      <input
                        value={createDraft.title}
                        onChange={(event) => setCreateDraft((draft) => ({ ...draft, title: event.target.value }))}
                        placeholder="Optional custom title"
                      />
                    </label>
                    <div className="reader-form-actions">
                      <button type="button" className="primary-button" onClick={() => handleCreateGoal(reader.reader_id)}>
                        Save goal
                      </button>
                      <button type="button" className="ghost-button" onClick={() => setCreatingReaderId(null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : null}

                {reader.goals.length > 0 ? (
                  <div className="goal-card-grid">
                    {reader.goals.map((goal) => {
                      const isEditing = editingGoalId === goal.goal_id;
                      return (
                        <article key={goal.goal_id} className="goal-card">
                          <div className="section-heading">
                            <div>
                              <p className="eyebrow">{formatGoalType(goal.goal_type)}</p>
                              <h3>{goal.title}</h3>
                            </div>
                            <span className={`chip ${goal.is_active ? "" : "muted"}`}>
                              {goal.progress.status === "completed"
                                ? "Completed"
                                : goal.is_active
                                  ? "Active"
                                  : "Paused"}
                            </span>
                          </div>

                          <div className="goal-progress-row">
                            <strong>
                              {goal.progress.current_value}/{goal.progress.target_value}
                            </strong>
                            <span>{goal.progress.progress_percent}%</span>
                          </div>
                          <div className="goal-progress-bar">
                            <span style={{ width: `${goal.progress.progress_percent}%` }} />
                          </div>

                          {isEditing ? (
                            <div className="goal-form-grid">
                              <label className="field goal-form-span">
                                <span>Title</span>
                                <input
                                  value={editDraft.title}
                                  onChange={(event) => setEditDraft((draft) => ({ ...draft, title: event.target.value }))}
                                />
                              </label>
                              <label className="field">
                                <span>Target</span>
                                <input
                                  type="number"
                                  min="1"
                                  value={editDraft.target_value}
                                  onChange={(event) =>
                                    setEditDraft((draft) => ({ ...draft, target_value: event.target.value }))
                                  }
                                />
                              </label>
                              <label className="field field-checkbox">
                                <span>Goal status</span>
                                <input
                                  type="checkbox"
                                  checked={editDraft.is_active}
                                  onChange={(event) =>
                                    setEditDraft((draft) => ({ ...draft, is_active: event.target.checked }))
                                  }
                                />
                              </label>
                              <div className="reader-form-actions">
                                <button type="button" className="primary-button" onClick={() => handleUpdateGoal(goal.goal_id)}>
                                  Save changes
                                </button>
                                <button type="button" className="ghost-button" onClick={() => setEditingGoalId(null)}>
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="reader-panel-actions">
                              <button type="button" className="ghost-button" onClick={() => startEditingGoal(goal)}>
                                Edit
                              </button>
                              <button type="button" className="ghost-button" onClick={() => handleToggleGoal(goal)}>
                                {goal.is_active ? "Pause" : "Reactivate"}
                              </button>
                            </div>
                          )}
                        </article>
                      );
                    })}
                  </div>
                ) : (
                  <div className="status-card">
                    <h3>No goals yet</h3>
                    <p>Create the first goal for this reader to turn the child-facing goals board into a live experience.</p>
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
