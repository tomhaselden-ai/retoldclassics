import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
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

  const allowedAuthors = useMemo(
    () => {
      if (!account) {
        return [...GUEST_AUTHORS];
      }
      return Array.isArray(account.allowed_classics_authors) && account.allowed_classics_authors.length > 0
        ? account.allowed_classics_authors
        : [...AUTHORS];
    },
    [account],
  );

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
        title="Classics Shelf | Persistent Story Universe"
        description="Browse Andersen, Grimm, Aesop, and more in the Persistent Story Universe classics shelf, with guest-friendly discovery and immersive reading."
      />

      <section className="panel">
        <p className="eyebrow">Global classics shelf</p>
        <h1>Timeless stories for every reader</h1>
        <p>
          Explore Andersen, Grimm, Bible, and Aesop stories in one glowing shelf designed for quick
          discovery and deep reading.
        </p>
        {!account && guestLimits ? (
          <div className="status-card">
            <h3>Guest classics preview</h3>
            <p>
              Guests can open up to {guestLimits.classics_read_limit} classics and launch{" "}
              {guestLimits.game_launch_limit} guest games. You have {guestLimits.classics_reads_remaining} reads and{" "}
              {guestLimits.game_launches_remaining} game launches remaining.
            </p>
            <div className="hero-actions">
              <Link to="/games/guest" className="ghost-button">
                Try a guest game
              </Link>
              <Link to="/register" className="primary-button">
                Create free account
              </Link>
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
          <button type="submit" className="primary-button">
            Search
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="growth-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">Public discovery</p>
            <h3>Start with the stories children already recognize</h3>
            <p>The classics shelf is the simplest way to try the reading experience before setting up a family flow.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Next step</p>
            <h3>Move into a family account when you’re ready</h3>
            <p>Free signup opens chooser, parent analytics, reader routes, and progress-driven goals.</p>
            <div className="library-action-row">
              <Link to="/register" className="primary-button">
                Start free
              </Link>
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
