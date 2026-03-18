import { useEffect, useState } from "react";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import {
  getContactSubmissions,
  getModerationComments,
  moderateComment,
  type ContactSubmissionRecord,
  type ModerationComment,
} from "../services/api";
import { useAuth } from "../services/auth";

export function ParentContentPage() {
  const { token } = useAuth();
  const [comments, setComments] = useState<ModerationComment[]>([]);
  const [contacts, setContacts] = useState<ContactSubmissionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingCommentId, setSavingCommentId] = useState<number | null>(null);

  async function loadContentWorkspace(activeToken: string) {
    const [commentPayload, contactPayload] = await Promise.all([
      getModerationComments(activeToken),
      getContactSubmissions(activeToken),
    ]);
    setComments(commentPayload);
    setContacts(contactPayload);
  }

  useEffect(() => {
    if (!token) {
      return;
    }
    setLoading(true);
    loadContentWorkspace(token)
      .then(() => setError(null))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load content moderation."))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleModerate(commentId: number, moderationStatus: "approved" | "rejected") {
    if (!token) {
      return;
    }
    setSavingCommentId(commentId);
    setError(null);
    try {
      await moderateComment(commentId, { moderation_status: moderationStatus }, token);
      await loadContentWorkspace(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update this comment.");
    } finally {
      setSavingCommentId(null);
    }
  }

  if (loading) {
    return <LoadingState label="Opening content moderation..." />;
  }

  return (
    <div className="page-grid">
      <PageSeo
        title="StoryBloom Content Moderation"
        description="Moderate StoryBloom blog comments and review recent contact submissions."
      />

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Content moderation</p>
            <h1>Blog comments and contact inbox</h1>
            <p>This space is for approved studio accounts to review public comment submissions and inbound contact notes.</p>
          </div>
        </div>

        {error ? <ErrorState message={error} /> : null}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Comment queue</p>
            <h2>{comments.filter((comment) => comment.moderation_status === "pending").length} pending comments</h2>
          </div>
        </div>

        {comments.length > 0 ? (
          <div className="tooling-stack">
            {comments.map((comment) => (
              <article key={comment.comment_id} className="panel inset-panel blog-comment-card">
                <div className="meta-row blog-meta-row">
                  <strong>{comment.author_name}</strong>
                  <span>{comment.author_email}</span>
                  <span>{comment.post_title}</span>
                  <span>{comment.moderation_status}</span>
                </div>
                <p>{comment.comment_body}</p>
                <div className="library-action-row">
                  <StoryBloomActionButton
                    type="button"
                    shape="sun"
                    onClick={() => handleModerate(comment.comment_id, "approved")}
                    disabled={savingCommentId === comment.comment_id}
                  >
                    Approve
                  </StoryBloomActionButton>
                  <StoryBloomActionButton
                    type="button"
                    variant="ghost"
                    shape="diamond"
                    onClick={() => handleModerate(comment.comment_id, "rejected")}
                    disabled={savingCommentId === comment.comment_id}
                  >
                    Reject
                  </StoryBloomActionButton>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="status-card">
            <h3>No comments waiting</h3>
            <p>The moderation queue is currently clear.</p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Contact inbox</p>
            <h2>Recent messages</h2>
          </div>
        </div>

        {contacts.length > 0 ? (
          <div className="tooling-stack">
            {contacts.map((submission) => (
              <article key={submission.submission_id} className="panel inset-panel blog-comment-card">
                <div className="meta-row blog-meta-row">
                  <strong>{submission.name}</strong>
                  <span>{submission.email}</span>
                  <span>{submission.delivery_status}</span>
                </div>
                <h3>{submission.subject}</h3>
                <p>{submission.message}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="status-card">
            <h3>No contact submissions yet</h3>
            <p>New contact messages will appear here after they are received.</p>
          </div>
        )}
      </section>
    </div>
  );
}
