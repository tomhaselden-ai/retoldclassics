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

        <button type="submit" className="primary-button" disabled={submitting}>
          {submitting ? "Opening StoryBloom..." : "Sign in"}
        </button>

        {error ? <ErrorState title="Sign-in failed" message={error} /> : null}

        <p>
          Need an account?{" "}
          <Link to="/register" className="text-link">
            Create one
          </Link>
        </p>
        <p>
          Need a password reset?{" "}
          <Link to="/reset-password" className="text-link">
            Reset password
          </Link>
        </p>
      </form>
    </section>
  );
}
