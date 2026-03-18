import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { confirmPasswordReset } from "../services/api";

const PASSWORD_MAX_BYTES = 72;

export function PasswordResetConfirmPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [resetToken, setResetToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      setResetToken(token);
    }
  }, [searchParams]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!resetToken.trim()) {
      setError("A reset token is required.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords must match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (new TextEncoder().encode(password).length > PASSWORD_MAX_BYTES) {
      setError("Password must be 72 bytes or fewer.");
      return;
    }

    setSubmitting(true);

    try {
      await confirmPasswordReset(resetToken.trim(), password);
      setSuccess("Password updated. Redirecting to sign in...");
      window.setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reset password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="center-shell">
      <form className="panel login-panel" onSubmit={handleSubmit}>
        <p className="eyebrow">Set a new password</p>
        <h1>Finish the password reset</h1>
        <p>Open the link from your email, or paste the reset token here to set a new password.</p>

        <label className="field">
          <span>Reset token</span>
          <input
            type="text"
            value={resetToken}
            onChange={(event) => setResetToken(event.target.value)}
            required
          />
        </label>

        <label className="field">
          <span>New password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            maxLength={72}
            required
          />
        </label>

        <label className="field">
          <span>Confirm new password</span>
          <input
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            minLength={8}
            maxLength={72}
            required
          />
        </label>

        <p className="helper-text">Use 8 to 72 characters for the best compatibility with the current auth system.</p>

        <button type="submit" className="primary-button" disabled={submitting}>
          {submitting ? "Updating password..." : "Update password"}
        </button>

        {error ? <ErrorState title="Password reset failed" message={error} /> : null}
        {success ? (
          <div className="status-card">
            <h3>Password updated</h3>
            <p>{success}</p>
          </div>
        ) : null}

        <p>
          Back to{" "}
          <Link to="/login" className="text-link">
            sign in
          </Link>
        </p>
      </form>
    </section>
  );
}
