import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import { StoryCard } from "../components/StoryCard";
import {
  ApiError,
  getClassicsDiscovery,
  getGuestClassicsDiscovery,
  type GuestLimitsResponse,
  type ShelfItem,
} from "../services/api";
import { useAuth } from "../services/auth";
import { ensureGuestSession } from "../services/guest";

const AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"] as const;
const GUEST_AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"] as const;

function buildClassicReadPath(storyId: number, playlistStoryIds?: number[]) {
  if (!playlistStoryIds || playlistStoryIds.length <= 1) {
    return `/classics/${storyId}/read`;
  }

  const params = new URLSearchParams({
    playlist: playlistStoryIds.join(","),
    playlistIndex: String(Math.max(0, playlistStoryIds.indexOf(storyId))),
  });

  return `/classics/${storyId}/read?${params.toString()}`;
}

function buildGuestPlaylistStoryIds(items: ShelfItem[], maximumStories: number) {
  const uniqueStoryIds: number[] = [];
  const seen = new Set<number>();

  for (const item of items) {
    if (seen.has(item.story_id)) {
      continue;
    }
    seen.add(item.story_id);
    uniqueStoryIds.push(item.story_id);
    if (uniqueStoryIds.length >= maximumStories) {
      break;
    }
  }

  return uniqueStoryIds;
}

export function ClassicsShelfPage() {
  const { account } = useAuth();
  const [author, setAuthor] = useState<string>("");
  const [queryDraft, setQueryDraft] = useState("");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ShelfItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [matchMode, setMatchMode] = useState("browse");
  const [promptExamples, setPromptExamples] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guestLimits, setGuestLimits] = useState<GuestLimitsResponse | null>(null);

  const allowedAuthors = useMemo(() => {
    if (!account) {
      return [...GUEST_AUTHORS];
    }
    return Array.isArray(account.allowed_classics_authors) && account.allowed_classics_authors.length > 0
      ? account.allowed_classics_authors
      : [...AUTHORS];
  }, [account]);

  useEffect(() => {
    if (author && !allowedAuthors.includes(author)) {
      setAuthor("");
    }
  }, [allowedAuthors, author]);

  useEffect(() => {
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

          const payload = await getGuestClassicsDiscovery({
            author: author || undefined,
            q: query || undefined,
            limit: 24,
            offset: 0,
          });
          if (cancelled) {
            return;
          }
          setItems(payload.items.filter((item) => item.source_author && allowedAuthors.includes(item.source_author)));
          setTotalCount(payload.total_count);
          setMatchMode(payload.match_mode);
          setPromptExamples(payload.prompt_examples);
          return;
        }

        setGuestLimits(null);
        const payload = await getClassicsDiscovery({
          author: author || undefined,
          q: query || undefined,
          limit: 48,
          offset: 0,
        });
        if (cancelled) {
          return;
        }
        setItems(payload.items.filter((item) => item.source_author && allowedAuthors.includes(item.source_author)));
        setTotalCount(payload.total_count);
        setMatchMode(payload.match_mode);
        setPromptExamples(payload.prompt_examples);
      } catch (err) {
        if (cancelled) {
          return;
        }
        setError(err instanceof ApiError ? err.message : "Unable to load the classics shelf.");
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
  }, [account, allowedAuthors, author, query]);

  const guestPlaylistStoryIds = useMemo(() => {
    if (account) {
      return [];
    }
    const maximumStories = Math.min(3, guestLimits?.classics_reads_remaining ?? 0);
    return buildGuestPlaylistStoryIds(items, maximumStories);
  }, [account, guestLimits, items]);

  const playAllPath =
    !account && guestPlaylistStoryIds.length > 0
      ? buildClassicReadPath(guestPlaylistStoryIds[0], guestPlaylistStoryIds)
      : null;

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(queryDraft.trim());
  }

  return (
    <div className="page-grid">
      <PageSeo
        title="Classics Shelf | StoryBloom"
        description="Browse timeless classics in StoryBloom, with family-friendly discovery and welcoming read-aloud experiences."
      />

      <section className="panel">
        <p className="eyebrow">Shared classics shelf</p>
        <h1>Ask for the kind of classic story you want</h1>
        <p>
          Search naturally for kindness, patience, brave heroes, bedtime pacing, or clever tricksters. StoryBloom will
          surface the closest classic matches and keep the shelf easy to explore.
        </p>
        {!account && guestLimits ? (
          <div className="status-card">
            <h3>Free guest access</h3>
            <p>
              Guests can open up to {guestLimits.classics_read_limit} classics and launch {guestLimits.game_launch_limit}{" "}
              guest games. You have {guestLimits.classics_reads_remaining} reads and{" "}
              {guestLimits.game_launches_remaining} game launches remaining.
            </p>
            <div className="hero-actions">
              <Link to="/games/guest" className="ghost-button">
                Try a guest game
              </Link>
              <StoryBloomActionButton to="/register" shape="sun">
                Create free account
              </StoryBloomActionButton>
              <Link to="/login" className="text-link">
                Sign in
              </Link>
              <Link to="/for-families" className="text-link">
                For families
              </Link>
            </div>
          </div>
        ) : null}
        <div className="filter-row">
          {[...AUTHORS].filter((value) => allowedAuthors.includes(value)).map((value) => (
            <button
              key={value}
              type="button"
              className={author === value ? "filter-chip active" : "filter-chip"}
              onClick={() => setAuthor((current) => (current === value ? "" : value))}
            >
              {value}
            </button>
          ))}
        </div>
        <form className="search-row" onSubmit={handleSearch}>
          <input
            type="search"
            value={queryDraft}
            placeholder="Try: bedtime stories about kindness"
            onChange={(event) => setQueryDraft(event.target.value)}
          />
          <StoryBloomActionButton type="submit" shape="diamond">
            Find stories
          </StoryBloomActionButton>
        </form>
        <div className="filter-row">
          {promptExamples.map((example) => (
            <button
              key={example}
              type="button"
              className="filter-chip"
              onClick={() => {
                setQueryDraft(example);
                setQuery(example);
              }}
            >
              {example}
            </button>
          ))}
        </div>
      </section>

      {loading ? <LoadingState label="Organizing the shelf..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && !error ? (
        items.length > 0 ? (
          <section className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{query ? "Classic story search" : "Browse classics"}</p>
                <h2>
                  {query
                    ? matchMode === "semantic"
                      ? "Stories that fit your search"
                      : "Stories matching your words"
                    : "Stories to begin with"}
                </h2>
                <p>
                  {query
                    ? "Search in natural language and StoryBloom will bring forward classic stories that match the idea you have in mind."
                    : "Start anywhere, then search with a full idea when you want something more specific."}
                </p>
              </div>
              <div className="section-actions">
                <span className="chip">{totalCount} stories</span>
                {!account && query ? (
                  playAllPath ? (
                    <StoryBloomActionButton to={playAllPath} shape="moon">
                      Play all
                    </StoryBloomActionButton>
                  ) : (
                    <StoryBloomActionButton type="button" shape="moon" disabled>
                      Play all
                    </StoryBloomActionButton>
                  )
                ) : null}
              </div>
            </div>
            <div className="story-grid">
              {items.map((item) => (
                <StoryCard
                  key={item.story_id}
                  item={item}
                  infoLabel="Story info"
                  readTo={buildClassicReadPath(item.story_id)}
                />
              ))}
            </div>
          </section>
        ) : (
          <div className="status-card">
            <h3>No classics matched that search</h3>
            <p>Try a broader story idea like kindness, patience, bravery, or clear the author filter and search again.</p>
          </div>
        )
      ) : null}
    </div>
  );
}
