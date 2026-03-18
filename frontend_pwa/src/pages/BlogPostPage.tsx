import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import { getBlogPost, submitBlogComment, type BlogPostDetail } from "../services/api";

function formatDate(value: string | null) {
  if (!value) {
    return "Recently published";
  }
  return new Date(value).toLocaleDateString();
}

export function BlogPostPage() {
  const { slug = "" } = useParams();
  const [post, setPost] = useState<BlogPostDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [authorName, setAuthorName] = useState("");
  const [authorEmail, setAuthorEmail] = useState("");
  const [commentBody, setCommentBody] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setLoading(true);
    getBlogPost(slug)
      .then((payload) => {
        setPost(payload);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load this article."))
      .finally(() => setLoading(false));
  }, [slug]);

  const paragraphs = useMemo(
    () => (post?.body_text ? post.body_text.split("\n\n").filter((block) => block.trim().length > 0) : []),
    [post?.body_text],
  );

  async function handleSubmitComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!post) {
      return;
    }

    setSubmitting(true);
    setNotice(null);
    setError(null);

    try {
      await submitBlogComment(post.post_id, {
        author_name: authorName,
        author_email: authorEmail,
        comment_body: commentBody,
      });
      setNotice("Thanks. Your comment was received and is now waiting for moderation.");
      setAuthorName("");
      setAuthorEmail("");
      setCommentBody("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit your comment.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <LoadingState label="Opening article..." />;
  }

  if (error && !post) {
    return <ErrorState message={error} />;
  }

  if (!post) {
    return <ErrorState message="This article is not available." />;
  }

  return (
    <div className="page-grid">
      <PageSeo title={`${post.title} | StoryBloom Blog`} description={post.summary} />

      <section className="panel blog-post-shell">
        <p className="eyebrow">{post.cover_eyebrow ?? "StoryBloom blog"}</p>
        <h1>{post.title}</h1>
        <p className="blog-post-summary">{post.summary}</p>
        <div className="meta-row blog-meta-row">
          <span>{post.author_name}</span>
          <span>{formatDate(post.published_at)}</span>
          <span>{post.comments.length} approved comments</span>
        </div>
        <div className="library-action-row">
          <Link to="/blog" className="ghost-button">
            Back to blog
          </Link>
          <StoryBloomActionButton to="/contact" variant="ghost" shape="diamond">
            Contact us
          </StoryBloomActionButton>
        </div>
      </section>

      <section className="panel blog-body-panel">
        {paragraphs.map((paragraph) => (
          <p key={paragraph} className="blog-paragraph">
            {paragraph}
          </p>
        ))}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Comments</p>
            <h2>Join the conversation</h2>
            <p>Comments are reviewed before they appear publicly.</p>
          </div>
        </div>

        {post.comments.length > 0 ? (
          <div className="blog-comment-list">
            {post.comments.map((comment) => (
              <article key={comment.comment_id} className="panel inset-panel blog-comment-card">
                <div className="meta-row blog-meta-row">
                  <strong>{comment.author_name}</strong>
                  <span>{formatDate(comment.created_at)}</span>
                </div>
                <p>{comment.comment_body}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="status-card">
            <h3>No comments yet</h3>
            <p>Be the first to leave a thoughtful note. New comments stay pending until they are reviewed.</p>
          </div>
        )}

        <form className="panel inset-panel blog-comment-form" onSubmit={handleSubmitComment}>
          <label className="field">
            <span>Name</span>
            <input value={authorName} onChange={(event) => setAuthorName(event.target.value)} required />
          </label>
          <label className="field">
            <span>Email</span>
            <input type="email" value={authorEmail} onChange={(event) => setAuthorEmail(event.target.value)} required />
          </label>
          <label className="field">
            <span>Comment</span>
            <textarea
              className="tooling-textarea"
              value={commentBody}
              onChange={(event) => setCommentBody(event.target.value)}
              required
            />
          </label>
          <div className="library-action-row">
            <StoryBloomActionButton type="submit" shape="heart" disabled={submitting}>
              {submitting ? "Sending..." : "Send for review"}
            </StoryBloomActionButton>
          </div>
          {notice ? <div className="status-card"><p>{notice}</p></div> : null}
          {error ? <ErrorState message={error} /> : null}
        </form>
      </section>
    </div>
  );
}
