import { useEffect, useMemo, useState } from "react";
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
        title="StoryBloom | Family Reading, Classics, and Story Games"
        description="Explore timeless classics, welcoming story games, and a family reading path that helps children grow with confidence."
      />

      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">StoryBloom by Retold Classics Studios</p>
          <h1>Stories to read together, words to grow on, and gentle games to keep the habit going.</h1>
          <p>
            StoryBloom gives families a warm place to discover beloved classics, practice reading in small wins, and
            step into personalized story adventures over time.
          </p>
          {!account && guestLimits ? (
            <div className="status-card">
              <h3>Free guest pass</h3>
              <p>
                Try a curated shelf before signing up. You have {guestLimits.classics_reads_remaining} classic reads
                and {guestLimits.game_launches_remaining} game launches remaining.
              </p>
            </div>
          ) : null}
          <div className="hero-actions">
            <StoryBloomActionButton to="/classics" shape="sun">
              Read free classics
            </StoryBloomActionButton>
            <StoryBloomActionButton to={account ? "/chooser" : "/register"} variant="ghost" shape="star">
              {account ? "Open family space" : "Start free"}
            </StoryBloomActionButton>
            <StoryBloomActionButton to="/games/guest" variant="ghost" shape="diamond">
              Try a game
            </StoryBloomActionButton>
            <Link to="/how-it-works" className="text-link">
              See how it works
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="planet-ring ring-one" />
          <div className="planet-ring ring-two" />
          <div className="planet-core">Bloom</div>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Why families stay</p>
            <h2>Easy to begin, steady enough to grow with your reader</h2>
          </div>
        </div>

        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Try it before you commit</h3>
            <p>Families can sample classics and word play first, with no credit card required for the free path.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Parent guidance without clutter</h3>
            <p>Once you sign in, StoryBloom keeps parent tools clear while giving children a simple place to read and play.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Child-friendly reading flow</h3>
            <p>Books, words, games, and goals stay close at hand so young readers can keep their momentum.</p>
          </article>
        </div>
      </section>

      <section className="panel growth-trust-strip">
        <div className="growth-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">A simple start</p>
            <h3>No credit card required to begin</h3>
            <p>Guests can explore first, then move into a free family account when they are ready.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Clear roles</p>
            <h3>Separate parent and reader spaces</h3>
            <p>Parents get oversight and settings while readers get a welcoming place built just for them.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">Meaningful progress</p>
            <h3>Stories, words, and games work together</h3>
            <p>Reading practice stays connected to vocabulary, play, and goals so progress feels natural.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">On the shared shelf</p>
            <h2>Timeless favorites are ready whenever your family is</h2>
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
            <h2>Read now, play a little, or open your family space</h2>
          </div>
        </div>

        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Explore classics</h3>
            <p>Open a familiar story and step straight into StoryBloom's read-aloud experience.</p>
            <div className="library-action-row">
              <StoryBloomActionButton to="/classics" shape="moon">
                Browse classics
              </StoryBloomActionButton>
            </div>
          </article>
          <article className="panel inset-panel">
            <h3>Try a story game</h3>
            <p>Build confidence with a quick word activity grounded in a classic story.</p>
            <div className="library-action-row">
              <StoryBloomActionButton to="/games/guest" shape="diamond">
                Open free games
              </StoryBloomActionButton>
            </div>
          </article>
          <article className="panel inset-panel">
            <h3>Start free</h3>
            <p>Create an account to unlock the chooser, parent tools, reader spaces, and saved progress.</p>
            <div className="library-action-row">
              <StoryBloomActionButton to="/register" shape="heart">
                Create account
              </StoryBloomActionButton>
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
