import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { useAuth } from "../services/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await login(email, password);
      const destination = (location.state as { from?: string } | null)?.from ?? "/chooser";
      navigate(destination, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="center-shell">
      <form className="panel login-panel" onSubmit={handleSubmit}>
        <p className="eyebrow">Account portal</p>
        <h1>Sign in to StoryBloom</h1>
        <p>Use your family account to open parent tools, reader bookshelves, and your saved stories.</p>

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
            required
          />
        </label>

        <button type="submit" className="btn btn--secondary btn-tone-sky primary-button" disabled={submitting}>
          {submitting ? "Signing In..." : "Sign In"}
        </button>

        {error ? <ErrorState title="Sign-in failed" message={error} /> : null}

        <div className="library-action-row">
          <Link to="/register" className="btn btn--create btn-tone-mint ghost-button">
            Create Account
          </Link>
          <Link to="/reset-password" className="btn btn--secondary btn-tone-plum ghost-button">
            Reset Password
          </Link>
        </div>
      </form>
    </section>
  );
}
