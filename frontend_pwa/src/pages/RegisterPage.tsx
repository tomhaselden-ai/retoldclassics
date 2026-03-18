import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { registerAccount } from "../services/api";

const PASSWORD_MAX_BYTES = 72;

export function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

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
      await registerAccount(email, password);
      setSuccess("Account created. You can sign in now.");
      window.setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="center-shell">
      <form className="panel login-panel" onSubmit={handleSubmit}>
        <p className="eyebrow">New account</p>
        <h1>Create your StoryBloom account</h1>
        <p>Set up your family account for parent tools, reader profiles, and your home bookshelf.</p>

        <label className="field">
          <span>Email</span>
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>

        <label className="field">
          <span>Password</span>
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
          <span>Confirm password</span>
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
          {submitting ? "Creating account..." : "Create account"}
        </button>

        {error ? <ErrorState title="Account creation failed" message={error} /> : null}
        {success ? (
          <div className="status-card">
            <h3>Account created</h3>
            <p>{success}</p>
          </div>
        ) : null}

        <p>
          Already have an account?{" "}
          <Link to="/login" className="text-link">
            Sign in
          </Link>
        </p>
      </form>
    </section>
  );
}
