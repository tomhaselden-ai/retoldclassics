import { FormEvent, useState } from "react";

import { ErrorState } from "../components/ErrorState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import { submitContactForm } from "../services/api";

export function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setNotice(null);

    try {
      const result = await submitContactForm({ name, email, subject, message });
      setNotice(
        result.delivery_status === "delivered"
          ? "Thanks for reaching out. Your message has been sent to our team."
          : "Thanks for reaching out. Your message was saved and will be delivered as soon as email is available.",
      );
      setName("");
      setEmail("");
      setSubject("");
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send your message.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-grid">
      <PageSeo
        title="Contact StoryBloom"
        description="Contact Retold Classics Studios with questions, support requests, or partnership notes."
      />

      <section className="hero-panel growth-hero growth-hero-how">
        <div className="hero-copy">
          <p className="eyebrow">Contact StoryBloom</p>
          <h1>Questions, support notes, or partnership ideas are always welcome.</h1>
          <p>
            Use this form to reach Retold Classics Studios. We will send your message to{" "}
            <a href="mailto:info@retoldclassics.com" className="text-link">
              info@retoldclassics.com
            </a>
            .
          </p>
        </div>
        <div className="growth-quote-card">
          <p className="eyebrow">Helpful topics</p>
          <h3>Account questions, reading support, school partnerships, and family feedback.</h3>
        </div>
      </section>

      <form className="panel contact-form-panel" onSubmit={handleSubmit}>
        <div className="goal-form-grid">
          <label className="field">
            <span>Name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="field">
            <span>Email</span>
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="field goal-form-span">
            <span>Subject</span>
            <input value={subject} onChange={(event) => setSubject(event.target.value)} required />
          </label>
          <label className="field goal-form-span">
            <span>Message</span>
            <textarea
              className="tooling-textarea"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              required
            />
          </label>
        </div>
        <div className="library-action-row">
          <StoryBloomActionButton type="submit" family="create" shape="sun" tone="mint" icon="✉" disabled={submitting}>
            {submitting ? "Sending..." : "Send message"}
          </StoryBloomActionButton>
        </div>
        {notice ? <div className="status-card"><p>{notice}</p></div> : null}
        {error ? <ErrorState message={error} /> : null}
      </form>
    </div>
  );
}
