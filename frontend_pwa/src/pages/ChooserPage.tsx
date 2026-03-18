import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { getReaders, type ParentPinStatusResponse, type Reader } from "../services/api";
import { useAuth } from "../services/auth";
import { loadParentPinStatus } from "../services/parentPin";

export function ChooserPage() {
  const { account, token } = useAuth();
  const [readers, setReaders] = useState<Reader[]>([]);
  const [parentPinStatus, setParentPinStatus] = useState<ParentPinStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !account) {
      return;
    }

    setLoading(true);
    Promise.all([getReaders(token), loadParentPinStatus(token, account.account_id)])
      .then(([readerPayload, pinStatus]) => {
        setReaders(readerPayload);
        setParentPinStatus(pinStatus);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to open the family chooser."))
      .finally(() => setLoading(false));
  }, [account, token]);

  const parentActionTo = parentPinStatus?.pin_enabled && parentPinStatus.verified ? "/parent" : "/parent/pin";
  const parentActionLabel = parentPinStatus?.pin_enabled
    ? parentPinStatus.verified
      ? "Open parent area"
      : "Unlock parent area"
    : "Set up parent PIN";
  const showSecondaryParentAction = Boolean(parentPinStatus?.pin_enabled);
  const secondaryParentActionLabel = parentPinStatus?.verified ? "Manage parent PIN" : "Parent PIN help";

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Family chooser</p>
          <h1>Choose who is reading today</h1>
          <p>Start from the parent area or open a reader home in one tap. Parent tools stay protected behind a separate PIN.</p>
        </div>
        <div className="library-action-row">
          <Link to="/classics" className="ghost-button">
            Browse classics
          </Link>
          <Link to="/parent/pin" className="text-link">
            Parent PIN
          </Link>
        </div>
      </div>

      {loading ? <LoadingState label="Opening the family chooser..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && !error ? (
        <div className="detail-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">Parent area</p>
            <h2>{account?.email ?? "Family account"}</h2>
            <p>
              {parentPinStatus?.pin_enabled
                ? parentPinStatus.verified
                  ? "Parent analytics, shelves, goals, and reader management are unlocked for this session."
                  : "Parent controls are protected by PIN. Unlock them before entering the parent area."
                : "Set a parent PIN before entering the parent area so children do not wander into account controls."}
            </p>
            <div className="library-action-row">
              <Link to={parentActionTo} className="primary-button">
                {parentActionLabel}
              </Link>
              {showSecondaryParentAction ? (
                <Link to="/parent/pin" className="ghost-button">
                  {secondaryParentActionLabel}
                </Link>
              ) : null}
            </div>
          </article>

          {readers.map((reader) => (
            <article key={reader.reader_id} className="panel inset-panel">
              <p className="eyebrow">Reader area</p>
              <h2>{reader.name ?? `Reader ${reader.reader_id}`}</h2>
              <p>
                Age {reader.age ?? "?"} - {reader.reading_level ?? "Emerging reader"}
              </p>
              <div className="library-action-row">
                <Link to={`/reader/${reader.reader_id}`} className="primary-button">
                  Open reader home
                </Link>
                <Link to={`/reader/${reader.reader_id}/books`} className="ghost-button">
                  Open books
                </Link>
              </div>
            </article>
          ))}

          {readers.length === 0 ? (
            <article className="panel inset-panel">
              <p className="eyebrow">No readers yet</p>
              <h2>Create your first reader</h2>
              <p>The parent area is where reader creation and family setup live right now.</p>
              <div className="library-action-row">
                <Link to={parentActionTo} className="primary-button">
                  {parentActionLabel}
                </Link>
              </div>
            </article>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
