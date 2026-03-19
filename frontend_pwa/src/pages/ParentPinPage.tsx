import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  clearParentPinSession,
  setParentPin,
  verifyParentPin,
  type ParentPinStatusResponse,
} from "../services/api";
import { useAuth } from "../services/auth";
import {
  clearStoredParentPinSessionToken,
  getStoredParentPinSessionToken,
  loadParentPinStatus,
  storeParentPinSessionToken,
} from "../services/parentPin";


export function ParentPinPage() {
  const { account, token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const returnPath = typeof location.state?.from === "string" ? location.state.from : "/parent";

  const [status, setStatus] = useState<ParentPinStatusResponse | null>(null);
  const [pin, setPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !account) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    loadParentPinStatus(token, account.account_id)
      .then((payload) => {
        if (!cancelled) {
          setStatus(payload);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load parent PIN status.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [account, token]);

  async function refreshStatus() {
    if (!token || !account) {
      return;
    }
    const payload = await loadParentPinStatus(token, account.account_id);
    setStatus(payload);
  }

  async function handleSetPin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !account) {
      return;
    }
    if (pin !== confirmPin) {
      setError("PIN confirmation does not match.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);

    try {
      const existingSessionToken = getStoredParentPinSessionToken(account.account_id);
      const response = await setParentPin(pin, token, existingSessionToken);
      storeParentPinSessionToken(account.account_id, response.session_token);
      setStatus(response);
      setPin("");
      setConfirmPin("");
      setNotice("Parent PIN saved. Parent controls are now unlocked.");
      navigate(returnPath, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save the parent PIN.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyPin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !account) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);

    try {
      const response = await verifyParentPin(pin, token);
      storeParentPinSessionToken(account.account_id, response.session_token);
      setStatus(response);
      setPin("");
      setNotice("Parent area unlocked.");
      navigate(returnPath, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to verify the parent PIN.");
      await refreshStatus();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLockParentArea() {
    if (!token || !account) {
      return;
    }

    const sessionToken = getStoredParentPinSessionToken(account.account_id);
    if (!sessionToken) {
      clearStoredParentPinSessionToken(account.account_id);
      await refreshStatus();
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      await clearParentPinSession(token, sessionToken);
      clearStoredParentPinSessionToken(account.account_id);
      await refreshStatus();
      setNotice("Parent area locked.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to lock the parent area.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <LoadingState label="Checking parent PIN status..." />;
  }

  if (error && !status) {
    return <ErrorState message={error} />;
  }

  const pinEnabled = Boolean(status?.pin_enabled);
  const verified = Boolean(status?.verified);

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Parent PIN</p>
          <h1>{pinEnabled ? "Unlock parent controls" : "Set up a parent PIN"}</h1>
          <p>
            {pinEnabled
              ? "Reader routes stay easy to enter. Parent routes require a separate PIN so children do not wander into account controls."
              : "Add a simple PIN to protect parent analytics, account settings, and reader management."}
          </p>
        </div>
        <div className="hero-actions">
          <Link to="/chooser" className="btn btn--secondary btn-tone-neutral ghost-button">
            Back to chooser
          </Link>
          {verified ? (
            <Link to={returnPath} className="btn btn--admin btn-tone-plum primary-button">
              Continue to parent area
            </Link>
          ) : null}
        </div>
      </div>

      <div className="detail-grid">
        <article className="panel inset-panel">
          <p className="eyebrow">Account</p>
          <h2>{account?.email ?? "Family account"}</h2>
          <p>{pinEnabled ? "PIN protection is enabled." : "PIN protection has not been configured yet."}</p>
          <p>
            {status?.locked_until
              ? `Locked until ${new Date(status.locked_until).toLocaleString()}.`
              : `${status?.attempts_remaining ?? 5} verification attempts remaining before temporary lockout.`}
          </p>
          {status?.session_expires_at ? <p>Current parent session expires at {new Date(status.session_expires_at).toLocaleString()}.</p> : null}
        </article>

        <article className="panel inset-panel">
          {notice ? (
            <div className="status-card">
              <h3>Updated</h3>
              <p>{notice}</p>
            </div>
          ) : null}
          {error ? <ErrorState message={error} /> : null}

          {!pinEnabled ? (
            <form className="world-assignment-form" onSubmit={handleSetPin}>
              <label className="field">
                <span>Choose a 4 to 8 digit PIN</span>
                <input
                  type="password"
                  inputMode="numeric"
                  value={pin}
                  onChange={(event) => setPin(event.target.value)}
                  placeholder="1234"
                />
              </label>

              <label className="field">
                <span>Confirm PIN</span>
                <input
                  type="password"
                  inputMode="numeric"
                  value={confirmPin}
                  onChange={(event) => setConfirmPin(event.target.value)}
                  placeholder="1234"
                />
              </label>

              <button type="submit" className="btn btn--admin btn-tone-mint primary-button" disabled={submitting}>
                {submitting ? "Saving PIN..." : "Save parent PIN"}
              </button>
            </form>
          ) : verified ? (
            <div className="status-card">
              <h3>Parent area unlocked</h3>
              <p>You can continue into the parent area now, or lock it again from this page.</p>
              <div className="hero-actions">
                <Link to={returnPath} className="btn btn--admin btn-tone-plum primary-button">
                  Continue
                </Link>
                <button type="button" className="btn btn--admin btn-tone-neutral ghost-button" onClick={() => void handleLockParentArea()} disabled={submitting}>
                  {submitting ? "Locking..." : "Lock parent area"}
                </button>
              </div>
            </div>
          ) : (
            <form className="world-assignment-form" onSubmit={handleVerifyPin}>
              <label className="field">
                <span>Enter parent PIN</span>
                <input
                  type="password"
                  inputMode="numeric"
                  value={pin}
                  onChange={(event) => setPin(event.target.value)}
                  placeholder="1234"
                />
              </label>

              <button type="submit" className="btn btn--admin btn-tone-plum primary-button" disabled={submitting}>
                {submitting ? "Unlocking..." : "Unlock parent area"}
              </button>
            </form>
          )}
        </article>
      </div>
    </section>
  );
}
