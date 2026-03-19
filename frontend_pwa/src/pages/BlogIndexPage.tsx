import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import { getBlogPosts, type BlogPostSummary } from "../services/api";

function formatDate(value: string | null) {
  if (!value) {
    return "Recently published";
  }
  return new Date(value).toLocaleDateString();
}

export function BlogIndexPage() {
  const [posts, setPosts] = useState<BlogPostSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBlogPosts()
      .then((payload) => {
        setPosts(payload);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the blog."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-grid">
      <PageSeo
        title="StoryBloom Blog"
        description="Read thoughtful articles from Retold Classics Studios about reading routines, classics, and family literacy."
      />

      <section className="hero-panel growth-hero growth-hero-families">
        <div className="hero-copy">
          <p className="eyebrow">StoryBloom blog</p>
          <h1>Notes for families who want reading to feel steady, warm, and worth returning to.</h1>
          <p>
            The StoryBloom blog shares practical ideas from Retold Classics Studios on reading routines, classics,
            confidence, and family learning at home.
          </p>
          <div className="hero-actions">
            <StoryBloomActionButton to="/contact" family="secondary" shape="sun" tone="sky" icon="✉">
              Contact us
            </StoryBloomActionButton>
            <StoryBloomActionButton to="/classics" family="secondary" shape="diamond" tone="sky" icon="🧭">
              Browse Classics
            </StoryBloomActionButton>
          </div>
        </div>
        <div className="growth-quote-card">
          <p className="eyebrow">What you'll find here</p>
          <h3>Clear, useful ideas for building better reading habits without adding more stress to family life.</h3>
        </div>
      </section>

      {loading ? <LoadingState label="Opening the StoryBloom blog..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && !error ? (
        <section className="blog-grid">
          {posts.map((post) => (
            <article key={post.post_id} className="panel blog-card">
              {post.cover_eyebrow ? <p className="eyebrow">{post.cover_eyebrow}</p> : null}
              <h2>{post.title}</h2>
              <p>{post.summary}</p>
              <div className="meta-row blog-meta-row">
                <span>{post.author_name}</span>
                <span>{formatDate(post.published_at)}</span>
                <span>{post.comment_count} approved comments</span>
              </div>
              <div className="library-action-row">
                <StoryBloomActionButton to={`/blog/${post.slug}`} family="secondary" shape="moon" tone="plum" icon="📝">
                  Read article
                </StoryBloomActionButton>
              </div>
            </article>
          ))}
        </section>
      ) : null}
    </div>
  );
}
