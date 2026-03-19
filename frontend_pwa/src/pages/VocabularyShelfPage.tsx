import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderAreaNav } from "../components/ReaderAreaNav";
import {
  getReaderPracticeVocabulary,
  getReaderVocabulary,
  updateReaderVocabularyProgress,
  type ReaderVocabularyItem,
} from "../services/api";
import { useAuth } from "../services/auth";

const MASTERY_OPTIONS = [
  { value: 0, label: "Needs work" },
  { value: 1, label: "Growing" },
  { value: 2, label: "Comfortable" },
  { value: 3, label: "Mastered" },
];

function formatLastSeen(value: string | null): string {
  if (!value) {
    return "Not seen yet";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Recently";
  }

  return date.toLocaleDateString();
}

export function VocabularyShelfPage() {
  const { readerId } = useParams();
  const { token } = useAuth();
  const [vocabulary, setVocabulary] = useState<ReaderVocabularyItem[]>([]);
  const [practiceWords, setPracticeWords] = useState<ReaderVocabularyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [savingWordId, setSavingWordId] = useState<number | null>(null);

  async function loadVocabulary(activeToken: string, activeReaderId: number) {
    const [allWords, practiceList] = await Promise.all([
      getReaderVocabulary(activeReaderId, activeToken),
      getReaderPracticeVocabulary(activeReaderId, activeToken),
    ]);
    setVocabulary(allWords);
    setPracticeWords(practiceList);
  }

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    setLoading(true);
    loadVocabulary(token, Number(readerId))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to open the vocabulary shelf."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

  const masteredCount = useMemo(
    () => vocabulary.filter((item) => (item.mastery_level ?? 0) >= 3).length,
    [vocabulary],
  );
  const developingCount = useMemo(
    () => vocabulary.filter((item) => (item.mastery_level ?? 0) > 0 && (item.mastery_level ?? 0) < 3).length,
    [vocabulary],
  );
  const needsPracticeCount = useMemo(
    () => vocabulary.filter((item) => (item.mastery_level ?? 0) <= 1).length,
    [vocabulary],
  );

  async function handleUpdateProgress(wordId: number, masteryLevel: number) {
    if (!token || !readerId) {
      return;
    }

    setSavingWordId(wordId);
    setError(null);
    setNotice(null);

    try {
      await updateReaderVocabularyProgress(Number(readerId), wordId, masteryLevel, token);
      await loadVocabulary(token, Number(readerId));
      const selectedLabel = MASTERY_OPTIONS.find((option) => option.value === masteryLevel)?.label.toLowerCase() ?? "updated";
      setNotice(`Vocabulary progress saved as ${selectedLabel}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update vocabulary progress.");
    } finally {
      setSavingWordId(null);
    }
  }

  return (
    <section className="panel">
      {loading ? <LoadingState label="Opening vocabulary shelf..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading ? (
        <>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Vocabulary shelf</p>
              <h1>Reader vocabulary</h1>
              <p>Track developing words, focus on practice words, and keep mastery progress moving without leaving the reader area.</p>
            </div>
            <div className="library-action-row">
              {readerId ? (
                <>
                  <Link to={`/reader/${readerId}/books`} className="btn btn--secondary btn-tone-neutral ghost-button">
                    Back to books
                  </Link>
                  <Link to={`/reader/${readerId}/games`} className="btn btn--secondary btn-tone-sky ghost-button">
                    Open game shelf
                  </Link>
                </>
              ) : null}
              {readerId ? (
                <Link to={`/reader/${readerId}`} className="btn btn--secondary btn-tone-sky ghost-button">
                  Reader Home
                </Link>
              ) : (
                <Link to="/chooser" className="btn btn--secondary btn-tone-plum ghost-button">
                  Family Chooser
                </Link>
              )}
            </div>
          </div>

          {readerId ? <ReaderAreaNav readerId={readerId} /> : null}

          {notice ? (
            <div className="status-card dashboard-notice-card">
              <h3>Saved</h3>
              <p>{notice}</p>
            </div>
          ) : null}

          <div className="detail-grid">
            <article className="panel inset-panel">
              <p className="eyebrow">Tracked words</p>
              <h3>{vocabulary.length}</h3>
              <p>Total vocabulary items currently attached to this reader.</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Mastered</p>
              <h3>{masteredCount}</h3>
              <p>Words already marked as fully learned.</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Developing</p>
              <h3>{developingCount}</h3>
              <p>Words in the middle of the learning curve.</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Needs practice</p>
              <h3>{needsPracticeCount}</h3>
              <p>Words worth revisiting in games and reading sessions.</p>
            </article>
          </div>

          <section className="panel inset-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Practice queue</p>
                <h2>Words to work on next</h2>
                <p>The backend already ranks these as the best current practice targets for this reader.</p>
              </div>
            </div>

            <div className="vocabulary-grid">
              {practiceWords.length > 0 ? (
                practiceWords.map((item) => (
                  <article key={`practice-${item.word_id}`} className="panel inset-panel vocabulary-card">
                    <div className="section-heading">
                      <div>
                        <p className="eyebrow">Practice word</p>
                        <h3>{item.word ?? `Word ${item.word_id}`}</h3>
                      </div>
                      <span className="chip">Difficulty {item.difficulty_level ?? "?"}</span>
                    </div>
                    <p>Current mastery: {MASTERY_OPTIONS.find((option) => option.value === (item.mastery_level ?? 0))?.label ?? "Needs work"}</p>
                    <p>Last seen: {formatLastSeen(item.last_seen)}</p>
                    <div className="filter-row">
                      {MASTERY_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          className={
                            option.value === (item.mastery_level ?? 0)
                              ? "filter-chip btn btn--chip btn-tone-mint active"
                              : "filter-chip btn btn--chip btn-tone-neutral"
                          }
                          onClick={() => handleUpdateProgress(item.word_id, option.value)}
                          disabled={savingWordId === item.word_id}
                        >
                          {savingWordId === item.word_id && option.value === (item.mastery_level ?? 0) ? "Saving..." : option.label}
                        </button>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <div className="status-card">
                  <h3>No practice words queued</h3>
                  <p>As this reader finishes more stories, vocabulary items will show up here automatically.</p>
                </div>
              )}
            </div>
          </section>

          <section className="panel inset-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Full vocabulary shelf</p>
                <h2>All tracked words</h2>
              </div>
            </div>

            <div className="vocabulary-grid">
              {vocabulary.length > 0 ? (
                vocabulary.map((item) => (
                  <article key={item.word_id} className="panel inset-panel vocabulary-card">
                    <div className="section-heading">
                      <div>
                        <p className="eyebrow">Tracked word</p>
                        <h3>{item.word ?? `Word ${item.word_id}`}</h3>
                      </div>
                      <span className="chip">Difficulty {item.difficulty_level ?? "?"}</span>
                    </div>
                    <p>Last seen: {formatLastSeen(item.last_seen)}</p>
                    <div className="vocabulary-status-row">
                      <span className="chip muted">
                        {MASTERY_OPTIONS.find((option) => option.value === (item.mastery_level ?? 0))?.label ?? "Needs work"}
                      </span>
                    </div>
                    <div className="filter-row">
                      {MASTERY_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          className={
                            option.value === (item.mastery_level ?? 0)
                              ? "filter-chip btn btn--chip btn-tone-mint active"
                              : "filter-chip btn btn--chip btn-tone-neutral"
                          }
                          onClick={() => handleUpdateProgress(item.word_id, option.value)}
                          disabled={savingWordId === item.word_id}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <div className="status-card">
                  <h3>No tracked words yet</h3>
                  <p>Generate and read stories for this reader, and the backend vocabulary extractor will populate this shelf.</p>
                </div>
              )}
            </div>
          </section>
        </>
      ) : null}
    </section>
  );
}
