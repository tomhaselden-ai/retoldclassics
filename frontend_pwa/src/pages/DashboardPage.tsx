import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderForm } from "../components/ReaderForm";
import { ReaderPanel } from "../components/ReaderPanel";
import {
  createReader,
  deleteReader,
  getAccountDashboard,
  getAccountLearningInsights,
  getAdaptiveProfile,
  getAdaptiveRecommendations,
  getReaderDashboard,
  getReaderLearningInsights,
  getReaders,
  updateMe,
  updateReader,
  type AccountDashboardData,
  type AccountLearningInsights,
  type AdaptiveProfile,
  type AdaptiveRecommendations,
  type Reader,
  type ReaderDashboardData,
  type ReaderInput,
  type ReaderLearningInsights,
} from "../services/api";
import { useAuth } from "../services/auth";

const CLASSICS_AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"] as const;

type ReaderMetricBundle = {
  dashboard: ReaderDashboardData | null;
  adaptiveProfile: AdaptiveProfile | null;
  adaptiveRecommendations: AdaptiveRecommendations | null;
  learningInsights: ReaderLearningInsights | null;
};

function normalizeAllowedAuthors(value: string[] | null | undefined): string[] {
  if (!Array.isArray(value) || value.length === 0) {
    return [...CLASSICS_AUTHORS];
  }
  const allowed = value.filter((author): author is string => CLASSICS_AUTHORS.includes(author as (typeof CLASSICS_AUTHORS)[number]));
  return allowed.length > 0 ? allowed : [...CLASSICS_AUTHORS];
}

export function DashboardPage() {
  const { account, token, refreshAccount } = useAuth();
  const [readers, setReaders] = useState<Reader[]>([]);
  const [accountDashboard, setAccountDashboard] = useState<AccountDashboardData | null>(null);
  const [accountInsights, setAccountInsights] = useState<AccountLearningInsights | null>(null);
  const [readerMetrics, setReaderMetrics] = useState<Record<number, ReaderMetricBundle>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingReader, setEditingReader] = useState<Reader | null>(null);
  const [deletingReaderId, setDeletingReaderId] = useState<number | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);
  const [subscriptionLevel, setSubscriptionLevel] = useState("free");
  const [storySecurity, setStorySecurity] = useState("private");
  const [allowedAuthors, setAllowedAuthors] = useState<string[]>([...CLASSICS_AUTHORS]);

  useEffect(() => {
    if (!account) {
      return;
    }
    setSubscriptionLevel(account.subscription_level ?? "free");
    setStorySecurity(account.story_security ?? "private");
    setAllowedAuthors(normalizeAllowedAuthors(account.allowed_classics_authors));
  }, [account]);

  async function loadDashboardWorkspace(activeToken: string, accountId: number) {
    const readerList = await getReaders(activeToken);
    setReaders(readerList);

    const [dashboardPayload, insightsPayload, metricEntries] = await Promise.all([
      getAccountDashboard(accountId, activeToken),
      getAccountLearningInsights(accountId, activeToken),
      Promise.all(
        readerList.map(async (reader) => {
          const [dashboard, adaptiveProfile, adaptiveRecommendations, learningInsights] = await Promise.all([
            getReaderDashboard(reader.reader_id, activeToken),
            getAdaptiveProfile(reader.reader_id, activeToken),
            getAdaptiveRecommendations(reader.reader_id, activeToken),
            getReaderLearningInsights(reader.reader_id, activeToken),
          ]);
          return [
            reader.reader_id,
            {
              dashboard,
              adaptiveProfile,
              adaptiveRecommendations,
              learningInsights,
            },
          ] as const;
        }),
      ),
    ]);

    setAccountDashboard(dashboardPayload);
    setAccountInsights(insightsPayload);
    setReaderMetrics(Object.fromEntries(metricEntries));
  }

  useEffect(() => {
    if (!token || !account) {
      return;
    }

    setLoading(true);
    loadDashboardWorkspace(token, account.account_id ?? 0)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load dashboard data."))
      .finally(() => setLoading(false));
  }, [account, token]);

  useEffect(() => {
    if (!loading && !error && readers.length === 0) {
      setShowCreateForm(true);
      setEditingReader(null);
    }
  }, [error, loading, readers.length]);

  const accountReaderCount = accountInsights?.reader_count ?? readers.length;
  const storiesRead = accountInsights?.aggregate_statistics.stories_read ?? 0;
  const wordsMastered = accountInsights?.aggregate_statistics.words_mastered ?? 0;

  const allowedAuthorSet = useMemo(() => new Set(allowedAuthors), [allowedAuthors]);

  async function refreshWorkspace() {
    if (!token || !account) {
      return;
    }
    await loadDashboardWorkspace(token, account.account_id);
  }

  async function handleCreateReader(payload: ReaderInput) {
    if (!token) {
      return;
    }
    await createReader(payload, token);
    await refreshWorkspace();
    setShowCreateForm(false);
    setError(null);
    setNotice("Reader profile created.");
  }

  async function handleUpdateReader(payload: ReaderInput) {
    if (!token || !editingReader) {
      return;
    }
    await updateReader(editingReader.reader_id, payload, token);
    await refreshWorkspace();
    setEditingReader(null);
    setError(null);
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
      await refreshWorkspace();
      setError(null);
      setNotice("Reader profile deleted.");
      if (editingReader?.reader_id === reader.reader_id) {
        setEditingReader(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete reader.");
    } finally {
      setDeletingReaderId(null);
    }
  }

  async function handleSaveAccountSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setSavingSettings(true);
    setError(null);
    try {
      await updateMe(
        {
          subscription_level: subscriptionLevel.trim(),
          story_security: storySecurity.trim(),
          allowed_classics_authors: allowedAuthors.length === CLASSICS_AUTHORS.length ? null : allowedAuthors,
        },
        token,
      );
      await refreshAccount();
      setNotice("Account settings updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update account settings.");
    } finally {
      setSavingSettings(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Mission control</p>
            <h1>Welcome back</h1>
            <p>
              Signed in as <strong>{account?.email}</strong>. This dashboard now pulls reader progress and
              recommendations from the backend so each library entrance has real learning context.
            </p>
          </div>
          <div className="dashboard-action-strip">
            <Link to="/chooser" className="btn btn--secondary btn-tone-neutral ghost-button">
              Family chooser
            </Link>
            <Link to="/classics" className="btn btn--secondary btn-tone-sky ghost-button">
              Open classics
            </Link>
            {readers[0] ? (
              <Link to={`/reader/${readers[0].reader_id}`} className="btn btn--secondary btn-tone-sky primary-link">
                Open first reader
              </Link>
            ) : (
              <button
                type="button"
                className="btn btn--create btn-tone-mint primary-button"
                onClick={() => {
                  setShowCreateForm(true);
                  setEditingReader(null);
                }}
              >
                Create first reader
              </button>
            )}
          </div>
        </div>

        <div className="dashboard-summary-grid">
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Account</p>
            <h3>{account?.subscription_level ?? "Standard access"}</h3>
            <p>{accountReaderCount} readers connected to this account.</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Stories read</p>
            <h3>{storiesRead}</h3>
            <p>Combined reading history across the current account.</p>
          </article>
          <article className="status-card dashboard-summary-card">
            <p className="eyebrow">Words mastered</p>
            <h3>{wordsMastered}</h3>
            <p>Vocabulary growth pulled from reader learning insights.</p>
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
            <p className="eyebrow">Account settings</p>
            <h2>Privacy, plan, and classics access</h2>
            <p>Use author availability to decide which classics collections appear to this signed-in account.</p>
          </div>
        </div>

        <form className="world-assignment-form" onSubmit={handleSaveAccountSettings}>
          <label className="field">
            <span>Subscription level</span>
            <input value={subscriptionLevel} onChange={(event) => setSubscriptionLevel(event.target.value)} />
          </label>

          <label className="field">
            <span>Story security</span>
            <input value={storySecurity} onChange={(event) => setStorySecurity(event.target.value)} />
          </label>

          <div className="field">
            <span>Allowed classics authors</span>
            <div className="filter-row">
              {CLASSICS_AUTHORS.map((author) => {
                const selected = allowedAuthorSet.has(author);
                return (
                  <button
                    key={author}
                    type="button"
                    className={selected ? "filter-chip btn btn--chip btn-tone-sky active" : "filter-chip btn btn--chip btn-tone-neutral"}
                    onClick={() =>
                      setAllowedAuthors((current) =>
                        current.includes(author) ? current.filter((value) => value !== author) : [...current, author],
                      )
                    }
                  >
                    {author}
                  </button>
                );
              })}
            </div>
          </div>

          <button type="submit" className="btn btn--admin btn-tone-mint primary-button" disabled={savingSettings || allowedAuthors.length === 0}>
            {savingSettings ? "Saving settings..." : "Save account settings"}
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Reader profiles</p>
            <h2>Your family library entrance points</h2>
            <p>
              Each reader card now combines reader dashboard data, adaptive difficulty signals, and learning insights.
            </p>
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

        {loading ? <LoadingState label="Loading dashboard and reader summaries..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && showCreateForm ? (
          <ReaderForm
            title="Create a reader profile"
            submitLabel="Create reader"
            onSubmit={handleCreateReader}
            onCancel={() => setShowCreateForm(false)}
          />
        ) : null}

        {!loading && editingReader ? (
          <ReaderForm
            initialReader={editingReader}
            title={`Edit ${editingReader.name ?? "reader profile"}`}
            submitLabel="Save changes"
            onSubmit={handleUpdateReader}
            onCancel={() => {
              setEditingReader(null);
              setNotice(null);
            }}
          />
        ) : null}

        {!loading && !error ? (
          <div className="reader-grid">
            {readers.length > 0 ? (
              readers.map((reader) => (
                <ReaderPanel
                  key={reader.reader_id}
                  reader={reader}
                  deleting={deletingReaderId === reader.reader_id}
                  dashboard={readerMetrics[reader.reader_id]?.dashboard ?? null}
                  adaptiveProfile={readerMetrics[reader.reader_id]?.adaptiveProfile ?? null}
                  adaptiveRecommendations={readerMetrics[reader.reader_id]?.adaptiveRecommendations ?? null}
                  learningInsights={readerMetrics[reader.reader_id]?.learningInsights ?? null}
                  onDelete={handleDeleteReader}
                  onEdit={(selectedReader) => {
                    setEditingReader(selectedReader);
                    setShowCreateForm(false);
                    setNotice(null);
                  }}
                />
              ))
            ) : (
              <div className="status-card">
                <h3>No readers yet</h3>
                <p>Create your first reader profile here to open a personal library for stories and progress.</p>
              </div>
            )}
          </div>
        ) : null}

        {accountDashboard?.readers?.length ? (
          <div className="status-card">
            <h3>Backend dashboard feed is active</h3>
            <p>{accountDashboard.readers.length} reader dashboard summaries are currently feeding this page.</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
