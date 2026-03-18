import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import { StoryCard } from "../components/StoryCard";
import {
  ApiError,
  getClassicsShelf,
  getGuestClassics,
  type GuestLimitsResponse,
  type ShelfGroup,
} from "../services/api";
import { useAuth } from "../services/auth";
import { ensureGuestSession } from "../services/guest";

const AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"] as const;
const GUEST_AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"] as const;

export function ClassicsShelfPage() {
  const { account } = useAuth();
  const [author, setAuthor] = useState<string>("");
  const [queryDraft, setQueryDraft] = useState("");
  const [query, setQuery] = useState("");
  const [groups, setGroups] = useState<ShelfGroup[]>([]);
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

          const payload = await getGuestClassics({
            author: author || undefined,
            q: query || undefined,
            limit: 24,
            offset: 0,
          });
          if (cancelled) {
            return;
          }
          setGroups(payload.groups.filter((group) => allowedAuthors.includes(group.author)));
          return;
        }

        setGuestLimits(null);
        const payload = await getClassicsShelf({
          author: author || undefined,
          q: query || undefined,
          limit: 80,
          offset: 0,
        });
        if (cancelled) {
          return;
        }
        setGroups(payload.groups.filter((group) => allowedAuthors.includes(group.author)));
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
        <h1>Timeless stories, ready for today's reader</h1>
        <p>
          Explore Andersen, Grimm, Bible, and Aesop stories in one welcoming shelf built for browsing, read-aloud
          moments, and repeat visits.
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
            placeholder="Search classic titles"
            onChange={(event) => setQueryDraft(event.target.value)}
          />
          <StoryBloomActionButton type="submit" shape="diamond">
            Search
          </StoryBloomActionButton>
        </form>
      </section>

      <section className="panel">
        <div className="growth-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">Easy discovery</p>
            <h3>Start with stories families already know and love</h3>
            <p>The classics shelf is an easy way to try the reading experience before moving into a full family account.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">When you're ready</p>
            <h3>Open a family account and keep your place</h3>
            <p>Free signup opens the chooser, parent tools, reader spaces, and saved progress.</p>
            <div className="library-action-row">
              <StoryBloomActionButton to="/register" shape="heart">
                Start free
              </StoryBloomActionButton>
              <Link to="/how-it-works" className="ghost-button">
                How it works
              </Link>
            </div>
          </article>
        </div>
      </section>

      {loading ? <LoadingState label="Organizing the shelf..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && !error ? (
        groups.length > 0 ? (
          groups.map((group) => (
            <section key={group.author} className="panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Author collection</p>
                  <h2>{group.author}</h2>
                </div>
                <span className="chip">{group.items.length} stories</span>
              </div>
              <div className="story-grid">
                {group.items.map((item) => (
                  <StoryCard key={item.story_id} item={item} />
                ))}
              </div>
            </section>
          ))
        ) : (
          <div className="status-card">
            <h3>No classics matched that search</h3>
            <p>Try a broader title search or clear the author filter.</p>
          </div>
        )
      ) : null}
    </div>
  );
}
