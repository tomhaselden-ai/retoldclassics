import { useEffect, useMemo, useState } from "react";
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

const ALL_AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"];
const GUEST_AUTHORS = ["Andersen", "Grimm", "Bible", "Aesop"];

export function HomePage() {
  const { account } = useAuth();
  const [groups, setGroups] = useState<ShelfGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guestLimits, setGuestLimits] = useState<GuestLimitsResponse | null>(null);

  const allowedAuthors = useMemo(() => {
    if (!account) {
      return GUEST_AUTHORS;
    }
    return Array.isArray(account.allowed_classics_authors) && account.allowed_classics_authors.length > 0
      ? account.allowed_classics_authors
      : ALL_AUTHORS;
  }, [account]);

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

          const payload = await getGuestClassics({ limit: 12, offset: 0 });
          if (cancelled) {
            return;
          }
          setGroups(payload.groups.filter((group) => allowedAuthors.includes(group.author)));
          return;
        }

        setGuestLimits(null);
        const payload = await getClassicsShelf({ limit: 40, offset: 0 });
        if (cancelled) {
          return;
        }
        setGroups(payload.groups.filter((group) => allowedAuthors.includes(group.author)));
      } catch (err: unknown) {
        if (cancelled) {
          return;
        }
        const message = err instanceof ApiError ? err.message : "Unable to load story previews.";
        setError(message);
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
  }, [account, allowedAuthors]);

  return (
    <div className="page-grid">
      <PageSeo
        title="Persistent Story Universe | Classics, Reader Growth, and Family Reading"
        description="Browse timeless classics, try guest reading experiences, and move into a family reading system with parent analytics, reader goals, and immersive story tools."
      />

      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">A living story galaxy</p>
          <h1>Read glowing classics. Build personal adventures. Keep every story alive.</h1>
          <p>
            Step into a child-friendly universe with immersive reading, bright story worlds, and a shared
            shelf of timeless tales.
          </p>
          {!account && guestLimits ? (
            <div className="status-card">
              <h3>Guest pass active</h3>
              <p>
                Browse a curated shelf and try the classics before signing up. You have{" "}
                {guestLimits.classics_reads_remaining} classic reads and {guestLimits.game_launches_remaining} game
                launches remaining.
              </p>
            </div>
          ) : null}
          <div className="hero-actions">
            <Link to="/classics" className="primary-button">
              Browse classics
            </Link>
            <Link to={account ? "/chooser" : "/login"} className="ghost-button">
              {account ? "Open family chooser" : "Sign in"}
            </Link>
            <Link to="/register" className="ghost-button">
              Create account
            </Link>
            <Link to="/games/guest" className="text-link">
              Try guest games
            </Link>
            <Link to="/how-it-works" className="text-link">
              How it works
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="planet-ring ring-one" />
          <div className="planet-ring ring-two" />
          <div className="planet-core">Story</div>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Why families use it</p>
            <h2>Discovery first, then a real reading system</h2>
          </div>
        </div>

        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Try before signing up</h3>
            <p>Guests can browse selected classics and launch a bounded story quiz before creating an account.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Parent visibility without chaos</h3>
            <p>Families get a chooser, a parent layer, and clearer analytics and goals once they’re inside.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Reader routes built for children</h3>
            <p>Books, words, games, and goals are organized into a calmer child-facing reading path.</p>
          </article>
        </div>
      </section>

      <section className="panel growth-trust-strip">
        <div className="growth-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">Trust</p>
            <h3>No credit card required to start</h3>
            <p>Guest discovery and free signup keep the first step low-friction for families.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Structure</p>
            <h3>Separate parent and reader experiences</h3>
            <p>The platform is built to keep grown-up control and child flow distinct.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Growth</p>
            <h3>Goals and analytics stay connected to reading</h3>
            <p>Progress features are tied to stories, words, and games instead of floating separately.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Shared classics bookshelf</p>
            <h2>{allowedAuthors.join(", ")} are ready now</h2>
          </div>
          <Link to="/classics" className="text-link">
            See all stories
          </Link>
        </div>

        {loading ? <LoadingState label="Gathering classic stories..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && !error ? (
          <div className="story-grid">
            {groups.flatMap((group) => group.items.slice(0, 2)).map((item) => (
              <StoryCard key={item.story_id} item={item} />
            ))}
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Choose your next step</p>
            <h2>Explore, try, or start the family flow</h2>
          </div>
        </div>

        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Explore classics</h3>
            <p>Open a timeless story shelf and test the reading experience right away.</p>
            <div className="library-action-row">
              <Link to="/classics" className="primary-button">
                Browse classics
              </Link>
            </div>
          </article>
          <article className="panel inset-panel">
            <h3>Try a guest game</h3>
            <p>Build confidence fast with a quick classic word quiz and bounded guest access.</p>
            <div className="library-action-row">
              <Link to="/games/guest" className="primary-button">
                Open guest games
              </Link>
            </div>
          </article>
          <article className="panel inset-panel">
            <h3>Start free</h3>
            <p>Create an account to open the chooser, parent controls, reader routes, and personalized growth tools.</p>
            <div className="library-action-row">
              <Link to="/register" className="primary-button">
                Create account
              </Link>
              <Link to="/for-families" className="ghost-button">
                For families
              </Link>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
