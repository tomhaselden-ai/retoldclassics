import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { ImmersiveReader } from "../components/ImmersiveReader";
import { LoadingState } from "../components/LoadingState";
import {
  ApiError,
  getClassicRead,
  getGuestClassicRead,
  type ClassicReadResponse,
  type GuestLimitsResponse,
} from "../services/api";
import { useAuth } from "../services/auth";
import { ensureGuestSession } from "../services/guest";

export function ClassicReaderPage() {
  const { account } = useAuth();
  const { storyId } = useParams();
  const [story, setStory] = useState<ClassicReadResponse | null>(null);
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

          const payload = await getGuestClassicRead(Number(storyId), limits.session_token);
          if (cancelled) {
            return;
          }
          setStory(payload);
          setGuestLimits(payload.guest_limits ?? limits);
          return;
        }

        setGuestLimits(null);
        const payload = await getClassicRead(Number(storyId));
        if (cancelled) {
          return;
        }
        setStory(payload);
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiError && err.code === "guest_classic_limit_reached") {
          setError("Your guest reading pass is used up. Create a free account to keep reading.");
          return;
        }
        setError(err instanceof Error ? err.message : "Unable to load the immersive reader.");
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
    return <LoadingState label="Building the immersive reading view..." />;
  }

  if (error) {
    return (
      <div className="page-grid">
        <ErrorState message={error} />
        {!account ? (
          <section className="panel">
            <p className="eyebrow">Keep going</p>
            <h2>Save your place with a free account</h2>
            <p>Guest reading is intentionally limited. Signing up unlocks your full family shelf and reader worlds.</p>
            <div className="hero-actions">
              <Link to="/register" className="primary-button">
                Create free account
              </Link>
              <Link to="/login" className="ghost-button">
                Sign in
              </Link>
              <Link to="/classics" className="text-link">
                Back to classics
              </Link>
            </div>
          </section>
        ) : null}
      </div>
    );
  }

  if (!story) {
    return <ErrorState message="No readable story was found." />;
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Classical immersive reader</p>
            <h1>{story.title ?? "Untitled classic"}</h1>
            <p>
              {story.source_author} - {story.units.length} units -{" "}
              {story.has_narration_text ? "Narration notes available" : "Text-first reading"}
            </p>
          </div>
          <Link to={`/classics/${story.story_id}`} className="text-link">
            Back to story detail
          </Link>
        </div>
      </section>

      {!account && guestLimits ? (
        <section className="panel">
          <p className="eyebrow">Guest reading pass</p>
          <h2>You are reading with preview access</h2>
          <p>
            This session has {guestLimits.classics_reads_remaining} classic reads and{" "}
            {guestLimits.game_launches_remaining} guest game launches remaining.
          </p>
          <div className="hero-actions">
            <Link to="/register" className="primary-button">
              Create free account
            </Link>
            <Link to="/games/guest" className="ghost-button">
              Try guest games
            </Link>
            <Link to="/login" className="text-link">
              Sign in
            </Link>
          </div>
        </section>
      ) : null}

      <ImmersiveReader story={story} />
    </div>
  );
}
