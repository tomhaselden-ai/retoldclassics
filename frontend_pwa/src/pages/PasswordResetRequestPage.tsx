import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { requestPasswordReset } from "../services/api";

export function PasswordResetRequestPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await requestPasswordReset(email);
      setSuccess("Password reset requested. If email delivery is configured, a reset link will be sent.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to request a password reset.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="center-shell">
      <form className="panel login-panel" onSubmit={handleSubmit}>
        <p className="eyebrow">Password reset</p>
        <h1>Request a password reset link</h1>
        <p>Enter the account email address. If reset email delivery is configured, you will receive a link.</p>

        <label className="field">
          <span>Email</span>
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>

        <button type="submit" className="btn btn--admin btn-tone-mint primary-button" disabled={submitting}>
          {submitting ? "Requesting reset..." : "Send reset link"}
        </button>

        {error ? <ErrorState title="Reset request failed" message={error} /> : null}
        {success ? (
          <div className="status-card">
            <h3>Reset requested</h3>
            <p>{success}</p>
          </div>
        ) : null}

        <div className="library-action-row">
          <Link to="/reset-password/confirm" className="btn btn--secondary btn-tone-plum ghost-button">
            Set a New Password
          </Link>
        </div>
      </form>
    </section>
  );
}
