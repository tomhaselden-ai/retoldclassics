import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  getClassicStory,
  getGuestClassicStory,
  type ClassicStoryDetail,
  type GuestLimitsResponse,
} from "../services/api";
import { useAuth } from "../services/auth";
import { ensureGuestSession } from "../services/guest";

function formatList(value: unknown): string {
  if (Array.isArray(value)) {
    const parts = value
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          const record = item as Record<string, unknown>;
          const name = typeof record.name === "string" ? record.name : null;
          const description =
            typeof record.description === "string" ? record.description : null;
          const title =
            typeof record.scene_title === "string" ? record.scene_title : null;

          if (name && description) {
            return `${name}: ${description}`;
          }
          if (name) {
            return name;
          }
          if (title && description) {
            return `${title}: ${description}`;
          }
          if (title) {
            return title;
          }
        }
        return null;
      })
      .filter((item): item is string => Boolean(item));
    return parts.length > 0 ? parts.join(", ") : "Not specified";
  }
  if (typeof value === "string") {
    return value;
  }
  return "Not specified";
}

export function ClassicStoryDetailPage() {
  const { account } = useAuth();
  const { storyId } = useParams();
  const [story, setStory] = useState<ClassicStoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guestLimits, setGuestLimits] = useState<GuestLimitsResponse | null>(null);

  useEffect(() => {
    if (!storyId) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        if (!account) {
          const limits = await ensureGuestSession();
          if (cancelled) {
            return;
          }
          setGuestLimits(limits);
          const payload = await getGuestClassicStory(Number(storyId));
          if (cancelled) {
            return;
          }
          setStory(payload);
          return;
        }

        setGuestLimits(null);
        const payload = await getClassicStory(Number(storyId));
        if (cancelled) {
          return;
        }
        setStory(payload);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load the story detail.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [account, storyId]);

  if (loading) {
    return <LoadingState label="Opening story detail..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!story) {
    return <ErrorState message="Story not found." />;
  }

  return (
    <div className="page-grid">
      <section className={`hero-panel detail-hero accent-${story.cover.accent_token ?? "default"}`}>
        <div className="hero-copy">
          <p className="eyebrow">{story.source_author}</p>
          <h1>{story.title ?? "Untitled classic"}</h1>
          <p>{story.summary}</p>
          {!account && guestLimits ? (
            <div className="status-card">
              <h3>Guest story access</h3>
              <p>
                This preview is open to guests. Starting immersive reading uses one of your remaining classic
                reads. You currently have {guestLimits.classics_reads_remaining} reads left.
              </p>
            </div>
          ) : null}
          <div className="meta-row">
            {story.age_range ? <span>{story.age_range}</span> : null}
            {story.reading_level ? <span>{story.reading_level}</span> : null}
          </div>
          <Link to={`/classics/${story.story_id}/read`} className="primary-button">
            Start immersive reading
          </Link>
        </div>
        {story.cover.image_url ? (
          <div className="hero-visual story-detail-visual">
            <img
              src={story.cover.image_url}
              alt={story.title ?? "Classic story illustration"}
              className="story-detail-image"
            />
          </div>
        ) : null}
      </section>

      <section className="panel detail-grid">
        <article>
          <p className="eyebrow">Story world</p>
          <h2>Characters</h2>
          <p>{formatList(story.characters)}</p>
        </article>
        <article>
          <p className="eyebrow">Story world</p>
          <h2>Locations</h2>
          <p>{formatList(story.locations)}</p>
        </article>
        <article>
          <p className="eyebrow">Guiding ideas</p>
          <h2>Themes</h2>
          <p>{formatList(story.themes)}</p>
        </article>
        <article>
          <p className="eyebrow">Moral</p>
          <h2>Takeaway</h2>
          <p>{story.moral ?? "This story invites its own quiet lesson."}</p>
        </article>
      </section>
    </div>
  );
}
