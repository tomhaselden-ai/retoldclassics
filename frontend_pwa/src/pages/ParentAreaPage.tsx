import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderForm } from "../components/ReaderForm";
import {
  createReader,
  deleteReader,
  getParentSummary,
  getReaders,
  updateReader,
  type ParentSummaryResponse,
  type Reader,
  type ReaderInput,
} from "../services/api";
import { useAuth } from "../services/auth";

export function ParentAreaPage() {
  const { token, account } = useAuth();
  const isStudioModerator = Boolean(account?.email?.toLowerCase().endsWith("@retoldclassics.com"));
  const [summary, setSummary] = useState<ParentSummaryResponse | null>(null);
  const [readers, setReaders] = useState<Reader[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingReader, setEditingReader] = useState<Reader | null>(null);
  const [deletingReaderId, setDeletingReaderId] = useState<number | null>(null);

  async function loadParentWorkspace(activeToken: string) {
    const [summaryPayload, readerPayload] = await Promise.all([getParentSummary(activeToken), getReaders(activeToken)]);
    setSummary(summaryPayload);
    setReaders(readerPayload);
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    setLoading(true);
    loadParentWorkspace(token)
      .then(() => setError(null))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the parent area."))
      .finally(() => setLoading(false));
  }, [token]);

  async function refreshParentWorkspace() {
    if (!token) {
      return;
    }
    await loadParentWorkspace(token);
  }

  async function handleCreateReader(payload: ReaderInput) {
    if (!token) {
      return;
    }
    await createReader(payload, token);
    await refreshParentWorkspace();
    setShowCreateForm(false);
    setNotice("Reader profile created.");
  }

  async function handleUpdateReader(payload: ReaderInput) {
    if (!token || !editingReader) {
      return;
    }
    await updateReader(editingReader.reader_id, payload, token);
    await refreshParentWorkspace();
    setEditingReader(null);
    setNotice("Reader profile updated.");
  }

  async function handleDeleteReader(reader: Reader) {
    if (!token) {
      return;
    }
    const confirmed = window.confirm(`Delete reader profile "${reader.name ?? "Young Reader"}"?`);
    if (!confirmed) {
      return;
    }

    setDeletingReaderId(reader.reader_id);
    try {
      await deleteReader(reader.reader_id, token);
      await refreshParentWorkspace();
      setEditingReader(null);
      setNotice("Reader profile deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete the reader.");
    } finally {
      setDeletingReaderId(null);
    }
  }

  const readerRecords = summary?.readers ?? [];

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent area</p>
            <h1>Family overview and reader management</h1>
            <p>
              This parent view keeps the important family signals together: reader progress, launch points into books
              and universes, and profile management in one place.
            </p>
          </div>
          <div className="library-action-row">
            <Link to="/chooser" className="btn btn--secondary btn-tone-neutral ghost-button">
              Family chooser
            </Link>
            <Link to="/dashboard" className="btn btn--secondary btn-tone-neutral ghost-button">
              Account dashboard
            </Link>
            <Link to="/parent/analytics" className="btn btn--admin btn-tone-plum primary-button">
              Family analytics
            </Link>
          </div>
        </div>

        {loading ? <LoadingState label="Opening the parent area..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && summary ? (
          <div className="dashboard-summary-grid">
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Readers</p>
              <h3>{summary.reader_count}</h3>
              <p>Profiles currently attached to this family account.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Stories read</p>
              <h3>{summary.aggregate_statistics.stories_read}</h3>
              <p>Combined story history across all readers.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Words mastered</p>
              <h3>{summary.aggregate_statistics.words_mastered}</h3>
              <p>Vocabulary growth pulled from reader learning data.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Games played</p>
              <h3>{summary.aggregate_statistics.games_played}</h3>
              <p>Practice sessions completed across the family account.</p>
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

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent tools</p>
            <h2>Parent tools at a glance</h2>
            <p>Use this area for everyday family management, then open deeper account tools when you need them.</p>
          </div>
        </div>

        <div className="parent-tool-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">Reader management</p>
            <h3>Create, edit, and launch</h3>
            <p>Manage reader profiles here, then jump directly into each child-facing area.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Shelves and universes</p>
            <h3>Per-reader details</h3>
            <p>Open a reader overview to see recent books, universe shelves, and launch points into reader tools.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Settings</p>
            <h3>Account dashboard</h3>
            <p>Account settings, classics controls, and longer-form management still live under the account dashboard.</p>
            <div className="library-action-row">
              <Link to="/dashboard" className="btn btn--secondary btn-tone-sky ghost-button">
                Open account dashboard
              </Link>
            </div>
          </article>
          {isStudioModerator ? (
            <article className="panel inset-panel">
              <p className="eyebrow">Studio tools</p>
              <h3>Content moderation</h3>
              <p>Review pending blog comments and recent contact submissions for StoryBloom.</p>
              <div className="library-action-row">
                <Link to="/parent/content" className="btn btn--admin btn-tone-plum ghost-button">
                  Open content moderation
                </Link>
              </div>
            </article>
          ) : null}
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Readers</p>
            <h2>Family reader management</h2>
            <p>Each reader card combines profile basics with the learning signals that matter most to a parent.</p>
          </div>
          <button
            type="button"
            className="btn btn--create btn-tone-mint primary-button"
            onClick={() => {
              setShowCreateForm((value) => !value);
              setEditingReader(null);
              setNotice(null);
            }}
          >
            {showCreateForm ? "Close reader form" : "Create reader"}
          </button>
        </div>

        {showCreateForm ? (
          <ReaderForm
            title="Create a reader profile"
            submitLabel="Create reader"
            onSubmit={handleCreateReader}
            onCancel={() => setShowCreateForm(false)}
          />
        ) : null}

        {editingReader ? (
          <ReaderForm
            initialReader={editingReader}
            title={`Edit ${editingReader.name ?? "reader profile"}`}
            submitLabel="Save changes"
            onSubmit={handleUpdateReader}
            onCancel={() => setEditingReader(null)}
          />
        ) : null}

        {!loading && !error ? (
          <div className="reader-grid">
            {readerRecords.length > 0 ? (
              readerRecords.map((readerSummary) => {
                const fullReader = readers.find((reader) => reader.reader_id === readerSummary.reader_id) ?? null;
                return (
                  <article key={readerSummary.reader_id} className="reader-panel">
                    <div>
                      <h3>{readerSummary.name ?? `Reader ${readerSummary.reader_id}`}</h3>
                      <p>
                        Age {readerSummary.age ?? "?"} | {readerSummary.reading_level ?? "Emerging reader"}
                      </p>
                      <p>
                        Proficiency: {readerSummary.proficiency} | {readerSummary.stories_read} stories |{" "}
                        {readerSummary.words_mastered} words mastered
                      </p>
                      {readerSummary.focus_message ? <p>Focus next: {readerSummary.focus_message}</p> : null}
                      {readerSummary.strengths[0] ? <p>Strength: {readerSummary.strengths[0]}</p> : null}
                      {readerSummary.trait_focus.length > 0 ? <p>Traits: {readerSummary.trait_focus.join(", ")}</p> : null}
                    </div>
                    <div className="reader-panel-actions">
                      <Link className="btn btn--admin btn-tone-plum primary-link" to={`/parent/readers/${readerSummary.reader_id}`}>
                        Manage reader
                      </Link>
                      <Link className="btn btn--secondary btn-tone-sky ghost-button" to={`/reader/${readerSummary.reader_id}/books`}>
                        Books
                      </Link>
                      <Link className="btn btn--secondary btn-tone-sky ghost-button" to={`/reader/${readerSummary.reader_id}/games`}>
                        Games
                      </Link>
                      <Link className="btn btn--secondary btn-tone-sky ghost-button" to={`/reader/${readerSummary.reader_id}`}>
                        Reader home
                      </Link>
                      {fullReader ? (
                        <button
                          type="button"
                          className="btn btn--admin btn-tone-neutral ghost-button"
                          onClick={() => {
                            setEditingReader(fullReader);
                            setShowCreateForm(false);
                            setNotice(null);
                          }}
                        >
                          Edit
                        </button>
                      ) : null}
                      {fullReader ? (
                        <button
                          type="button"
                          className="btn btn--danger btn-tone-danger ghost-button"
                          onClick={() => handleDeleteReader(fullReader)}
                          disabled={deletingReaderId === readerSummary.reader_id}
                        >
                          {deletingReaderId === readerSummary.reader_id ? "Removing..." : "Delete"}
                        </button>
                      ) : null}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="status-card">
                <h3>No readers yet</h3>
                <p>Create the first reader profile here to open up books, universes, and child-facing routes.</p>
              </div>
            )}
          </div>
        ) : null}
      </section>
    </div>
  );
}
