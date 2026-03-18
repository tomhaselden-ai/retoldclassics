import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

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

function parsePlaylistStoryIds(value: string | null) {
  if (!value) {
    return [];
  }

  const uniqueIds: number[] = [];
  const seen = new Set<number>();

  for (const part of value.split(",")) {
    const storyId = Number(part.trim());
    if (!Number.isInteger(storyId) || storyId <= 0 || seen.has(storyId)) {
      continue;
    }
    seen.add(storyId);
    uniqueIds.push(storyId);
    if (uniqueIds.length >= 3) {
      break;
    }
  }

  return uniqueIds;
}

function buildPlaylistReadPath(storyId: number, playlistStoryIds: number[], playlistIndex: number) {
  const params = new URLSearchParams({
    autostart: "1",
    focus: "now-reading",
  });

  if (playlistStoryIds.length > 1) {
    params.set("playlist", playlistStoryIds.join(","));
    params.set("playlistIndex", String(playlistIndex));
  }

  return `/classics/${storyId}/read?${params.toString()}`;
}

export function ClassicReaderPage() {
  const { account } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { storyId } = useParams();
  const [story, setStory] = useState<ClassicReadResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guestLimits, setGuestLimits] = useState<GuestLimitsResponse | null>(null);

  const numericStoryId = useMemo(() => {
    const parsedStoryId = Number(storyId);
    return Number.isInteger(parsedStoryId) && parsedStoryId > 0 ? parsedStoryId : null;
  }, [storyId]);

  const playlist = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const storyIds = parsePlaylistStoryIds(params.get("playlist"));
    if (!numericStoryId) {
      return { storyIds: [], currentIndex: 0 };
    }

    if (storyIds.length === 0) {
      return { storyIds: [numericStoryId], currentIndex: 0 };
    }

    const currentIndex = storyIds.indexOf(numericStoryId);
    if (currentIndex >= 0) {
      return { storyIds, currentIndex };
    }

    return { storyIds: [numericStoryId, ...storyIds].slice(0, 3), currentIndex: 0 };
  }, [location.search, numericStoryId]);
  const shouldAutoStart = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("autostart") === "1";
  }, [location.search]);
  const shouldFocusNowReading = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("focus") === "now-reading";
  }, [location.search]);

  const nextStoryId =
    playlist.currentIndex < playlist.storyIds.length - 1 ? playlist.storyIds[playlist.currentIndex + 1] : null;
  const nextStoryPath =
    nextStoryId !== null
      ? buildPlaylistReadPath(nextStoryId, playlist.storyIds, playlist.currentIndex + 1)
      : null;

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

  function handlePlaylistAdvance() {
    if (!nextStoryPath) {
      return;
    }
    navigate(nextStoryPath);
  }

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

      {!account && playlist.storyIds.length > 1 ? (
        <section className="panel">
          <p className="eyebrow">Guest story queue</p>
          <h2>
            Story {playlist.currentIndex + 1} of {playlist.storyIds.length}
          </h2>
          <p>
            StoryBloom will move to the next story automatically when narration finishes. If this story is text-first,
            you can use the next button below to keep going.
          </p>
          {nextStoryPath ? (
            <div className="hero-actions">
              <Link to={nextStoryPath} className="ghost-button">
                Next story
              </Link>
            </div>
          ) : (
            <span className="chip">Final story in this guest queue</span>
          )}
        </section>
      ) : null}

      <ImmersiveReader
        story={story}
        autoPlay={shouldAutoStart}
        focusNowReading={shouldFocusNowReading}
        onFinished={handlePlaylistAdvance}
      />
    </div>
  );
}
