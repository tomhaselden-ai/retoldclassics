import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderForm } from "../components/ReaderForm";
import {
  deleteReader,
  getParentReaderSummary,
  updateReader,
  type ParentReaderWorkspaceResponse,
  type ReaderInput,
} from "../services/api";
import { useAuth } from "../services/auth";

export function ParentReaderPage() {
  const { readerId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [workspace, setWorkspace] = useState<ParentReaderWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function loadWorkspace(activeToken: string, activeReaderId: number) {
    const payload = await getParentReaderSummary(activeReaderId, activeToken);
    setWorkspace(payload);
  }

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    setLoading(true);
    loadWorkspace(token, Number(readerId))
      .then(() => setError(null))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the parent reader workspace."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

  async function handleUpdateReader(payload: ReaderInput) {
    if (!token || !workspace) {
      return;
    }
    await updateReader(workspace.reader.reader_id, payload, token);
    await loadWorkspace(token, workspace.reader.reader_id);
    setEditing(false);
    setNotice("Reader profile updated.");
  }

  async function handleDeleteReader() {
    if (!token || !workspace) {
      return;
    }

    const confirmed = window.confirm(`Delete reader profile "${workspace.reader.name ?? "Young Reader"}"?`);
    if (!confirmed) {
      return;
    }

    setDeleting(true);
    try {
      await deleteReader(workspace.reader.reader_id, token);
      navigate("/parent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete the reader.");
      setDeleting(false);
    }
  }

  if (loading) {
    return <LoadingState label="Opening the parent reader workspace..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!workspace) {
    return <ErrorState message="Reader workspace unavailable." />;
  }

  const { reader, dashboard, learning_insights, library_summary, world_summary } = workspace;

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent reader workspace</p>
            <h1>{reader.name ?? `Reader ${reader.reader_id}`}</h1>
            <p>
              Parent-facing view for this reader&apos;s profile, current shelves, and launch points into the
              child-facing experiences that already exist.
            </p>
          </div>
          <div className="library-action-row">
            <Link to="/parent" className="ghost-button">
              Parent area
            </Link>
            <Link to={`/reader/${reader.reader_id}`} className="ghost-button">
              Reader home
            </Link>
            <Link to={`/reader/${reader.reader_id}/books`} className="primary-button">
              Open books
            </Link>
          </div>
        </div>

        <div className="dashboard-summary-grid">
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Reading level</p>
            <h3>{reader.reading_level ?? "Emerging reader"}</h3>
            <p>Age {reader.age ?? "?"} | Proficiency {learning_insights.proficiency}</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Stories read</p>
            <h3>{dashboard.reading_statistics.stories_read ?? 0}</h3>
            <p>Reader progress tracked through the dashboard service.</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Words mastered</p>
            <h3>{dashboard.reading_statistics.words_mastered ?? 0}</h3>
            <p>Vocabulary progress available for parent review.</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">World shelves</p>
            <h3>{world_summary.world_count}</h3>
            <p>{library_summary.story_count} generated books currently visible in this reader&apos;s library.</p>
          </article>
        </div>

        {notice ? (
          <div className="status-card dashboard-notice-card">
            <h3>Saved</h3>
            <p>{notice}</p>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Profile</p>
            <h2>Reader profile and parent controls</h2>
            <p>Use this space for profile maintenance, then launch into books, words, games, and worlds as needed.</p>
          </div>
          <div className="library-action-row">
            <button type="button" className="ghost-button" onClick={() => setEditing((value) => !value)}>
              {editing ? "Close edit form" : "Edit reader"}
            </button>
            <button type="button" className="ghost-button" onClick={handleDeleteReader} disabled={deleting}>
              {deleting ? "Removing..." : "Delete reader"}
            </button>
          </div>
        </div>

        {editing ? (
          <ReaderForm
            initialReader={reader}
            title={`Edit ${reader.name ?? "reader profile"}`}
            submitLabel="Save changes"
            onSubmit={handleUpdateReader}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <div className="parent-detail-grid">
            <article className="panel inset-panel">
              <p className="eyebrow">Traits</p>
              <h3>{Array.isArray(reader.trait_focus) && reader.trait_focus.length > 0 ? reader.trait_focus.join(", ") : "No trait focus set yet"}</h3>
              <p>Gender preference: {reader.gender_preference ?? "Not set"}</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Strengths</p>
              <h3>{learning_insights.strengths[0] ?? "Strengths will appear as data builds"}</h3>
              <p>{learning_insights.focus_areas[0]?.message ?? "No immediate focus message is available yet."}</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Recommended next step</p>
              <h3>Story difficulty {learning_insights.recommendations.recommended_story_difficulty}</h3>
              <p>
                Vocabulary difficulty {learning_insights.recommendations.recommended_vocabulary_difficulty} | Game
                difficulty {learning_insights.recommendations.recommended_game_difficulty}
              </p>
            </article>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Books</p>
            <h2>Recent library activity</h2>
            <p>
              The parent workspace summarizes recent generated books and gives you a quick jump back into the live
              reader library.
            </p>
          </div>
          <Link to={`/reader/${reader.reader_id}/books`} className="ghost-button">
            Open full library
          </Link>
        </div>

        <div className="library-grid">
          {library_summary.recent_stories.length > 0 ? (
            library_summary.recent_stories.map((story) => (
              <article key={story.story_id} className="panel inset-panel">
                <p className="eyebrow">Generated book</p>
                <h3>{story.title ?? "Untitled story"}</h3>
                <p>{story.custom_world_name || story.world_name || "Ungrouped world shelf"}</p>
                <div className="library-action-row">
                  <Link className="primary-button" to={`/reader/${reader.reader_id}/books/${story.story_id}`}>
                    View story
                  </Link>
                  <Link className="ghost-button" to={`/reader/${reader.reader_id}/books/${story.story_id}/read`}>
                    Read
                  </Link>
                </div>
              </article>
            ))
          ) : (
            <div className="status-card">
              <h3>No generated books yet</h3>
              <p>Use the reader library to assign worlds and generate the first book for this reader.</p>
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">World shelves</p>
            <h2>Reader universes and launch points</h2>
            <p>
              World editing and new-book creation still happen through the existing reader library tools. This page
              keeps the overview and links in one place.
            </p>
          </div>
        </div>

        <div className="library-grid">
          {world_summary.worlds.length > 0 ? (
            world_summary.worlds.map((world) => (
              <article key={world.reader_world_id} className="panel inset-panel">
                <p className="eyebrow">World shelf</p>
                <h3>{world.custom_name || world.name || "Unnamed world shelf"}</h3>
                <p>{world.description ?? "No world description available yet."}</p>
                <div className="library-action-row">
                  <Link className="ghost-button" to={`/reader/${reader.reader_id}/books`}>
                    Open library tools
                  </Link>
                  {typeof world.world_id === "number" ? (
                    <>
                      <Link className="ghost-button" to={`/reader/${reader.reader_id}/worlds/${world.world_id}`}>
                        World info
                      </Link>
                      <Link className="ghost-button" to={`/parent/readers/${reader.reader_id}/worlds/${world.world_id}/canon`}>
                        Character canon
                      </Link>
                    </>
                  ) : null}
                </div>
              </article>
            ))
          ) : (
            <div className="status-card">
              <h3>No world shelves yet</h3>
              <p>Assign a world through the reader library to start organizing books by universe.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
