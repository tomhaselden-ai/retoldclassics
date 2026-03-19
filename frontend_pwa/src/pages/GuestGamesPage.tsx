import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";
import {
  ApiError,
  getGuestGamesCatalog,
  launchGuestGamePreview,
  type GuestGamePreviewResponse,
  type GuestGamesCatalogResponse,
  type GuestLimitsResponse,
} from "../services/api";
import { useAuth } from "../services/auth";
import { ensureGuestSession } from "../services/guest";

interface GuestBuildRound {
  round_id: string;
  word_id: number | null;
  target_word: string;
  normalized_word: string;
  clue: string;
  example_sentence: string | null;
}

interface GuestBuildPayload {
  game_type: "build_the_word";
  figure_steps: string[];
  max_incorrect_guesses: number;
  rounds: GuestBuildRound[];
}

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

function isGuestBuildPayload(payload: unknown): payload is GuestBuildPayload {
  const candidate = payload as Partial<GuestBuildPayload> | null;
  return (
    !!candidate &&
    candidate.game_type === "build_the_word" &&
    Array.isArray(candidate.rounds) &&
    Array.isArray(candidate.figure_steps) &&
    typeof candidate.max_incorrect_guesses === "number"
  );
}

function pickMessage(messages: string[], key: number): string {
  return messages[key % messages.length];
}

const FEEDBACK_MESSAGES = {
  incorrect: ["Good try. Let's keep going.", "Almost there. Try again.", "You're learning as you play."],
  success: ["Nice work!", "You got it!", "Great reading!"],
};

export function GuestGamesPage() {
  const { account } = useAuth();
  const [catalog, setCatalog] = useState<GuestGamesCatalogResponse | null>(null);
  const [guestLimits, setGuestLimits] = useState<GuestLimitsResponse | null>(null);
  const [selectedStoryId, setSelectedStoryId] = useState<number | null>(null);
  const [itemCount, setItemCount] = useState(4);
  const [preview, setPreview] = useState<GuestGamePreviewResponse | null>(null);
  const [guessedLetters, setGuessedLetters] = useState<string[]>([]);
  const [currentRoundIndex, setCurrentRoundIndex] = useState(0);
  const [roundSolved, setRoundSolved] = useState(false);
  const [roundMissed, setRoundMissed] = useState(false);
  const [completedWords, setCompletedWords] = useState<string[]>([]);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        const [limits, guestCatalog] = await Promise.all([ensureGuestSession(), getGuestGamesCatalog()]);
        if (cancelled) {
          return;
        }
        setGuestLimits(limits);
        setCatalog(guestCatalog);
        setSelectedStoryId((current) => current ?? guestCatalog.stories[0]?.story_id ?? null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load guest games.");
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
  }, []);

  const selectedStory = useMemo(
    () => catalog?.stories.find((item) => item.story_id === selectedStoryId) ?? null,
    [catalog, selectedStoryId],
  );

  const payload = useMemo(
    () => (preview && isGuestBuildPayload(preview.payload) ? preview.payload : null),
    [preview],
  );
  const currentRound = payload?.rounds[currentRoundIndex] ?? null;
  const revealedPattern = useMemo(() => {
    if (!currentRound) {
      return [];
    }
    const guessedSet = new Set(guessedLetters);
    return currentRound.normalized_word.split("").map((letter) => (guessedSet.has(letter) ? letter : "_"));
  }, [currentRound, guessedLetters]);
  const incorrectLetters = useMemo(() => {
    if (!currentRound) {
      return [];
    }
    return guessedLetters.filter((letter) => !currentRound.normalized_word.includes(letter));
  }, [currentRound, guessedLetters]);
  const isSessionComplete = payload ? currentRoundIndex >= payload.rounds.length : false;

  async function handleLaunchPreview() {
    if (!selectedStoryId) {
      setError("Choose a classic before launching the game preview.");
      return;
    }

    setLaunching(true);
    setError(null);

    try {
      const limits = await ensureGuestSession();
      const previewPayload = await launchGuestGamePreview(limits.session_token, {
        story_id: selectedStoryId,
        item_count: itemCount,
      });
      setPreview(previewPayload);
      setGuestLimits(previewPayload.guest_limits);
      setGuessedLetters([]);
      setCurrentRoundIndex(0);
      setRoundSolved(false);
      setRoundMissed(false);
      setCompletedWords([]);
      setFeedback(`${previewPayload.story_title ?? "Classic"} is ready to play.`);
    } catch (err) {
      if (err instanceof ApiError && err.code === "guest_game_limit_reached") {
        setError("Your guest game launches are used up. Create a free account to keep playing.");
      } else {
        setError(err instanceof Error ? err.message : "Unable to start the guest game preview.");
      }
    } finally {
      setLaunching(false);
    }
  }

  function clearRoundState() {
    setGuessedLetters([]);
    setRoundSolved(false);
    setRoundMissed(false);
  }

  function handleGuessLetter(letter: string) {
    if (!currentRound || roundSolved || roundMissed || isSessionComplete) {
      return;
    }
    if (guessedLetters.includes(letter)) {
      return;
    }

    const nextLetters = [...guessedLetters, letter];
    setGuessedLetters(nextLetters);

    const solved = currentRound.normalized_word.split("").every((character) => nextLetters.includes(character));
    const missCount = nextLetters.filter((candidate) => !currentRound.normalized_word.includes(candidate)).length;

    if (solved) {
      setRoundSolved(true);
      setCompletedWords((current) => [...current, currentRound.target_word]);
      setFeedback(pickMessage(FEEDBACK_MESSAGES.success, nextLetters.length));
      return;
    }

    if (!currentRound.normalized_word.includes(letter)) {
      if (payload && missCount >= payload.max_incorrect_guesses) {
        setRoundMissed(true);
        setFeedback(`The word was "${currentRound.target_word}".`);
        return;
      }
      setFeedback(pickMessage(FEEDBACK_MESSAGES.incorrect, nextLetters.length));
    }
  }

  function handleContinue() {
    if (!payload) {
      return;
    }
    if (currentRoundIndex >= payload.rounds.length - 1) {
      setCurrentRoundIndex(payload.rounds.length);
      setFeedback("Preview complete. Create a free account to unlock the full reader game hub.");
      return;
    }
    setCurrentRoundIndex((current) => current + 1);
    clearRoundState();
  }

  function handleResetPreview() {
    setPreview(null);
    setGuessedLetters([]);
    setCurrentRoundIndex(0);
    setRoundSolved(false);
    setRoundMissed(false);
    setCompletedWords([]);
    setFeedback(null);
  }

  if (loading) {
    return <LoadingState label="Opening guest games..." />;
  }

  if (error && !catalog) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="page-grid">
      <PageSeo
        title="Free Story Games | StoryBloom"
        description="Try a gentle Build the Word preview from a classic story before opening a free StoryBloom family account."
      />

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Guest games</p>
            <h1>Try a gentle story game from a classic</h1>
            <p>
              Pick a classic and try a quick word-building round designed to feel welcoming, playful, and easy to start.
            </p>
          </div>
          <div className="hero-actions">
            <StoryBloomActionButton to="/classics" family="secondary" shape="moon" tone="sky" icon="🧭">
              Browse Classics
            </StoryBloomActionButton>
            <StoryBloomActionButton to={account ? "/chooser" : "/register"} family="create" shape="sun" tone="mint" icon={account ? "🏠" : "✨"}>
              {account ? "Open Family Space" : "Create Account"}
            </StoryBloomActionButton>
            <Link to="/for-families" className="btn btn--secondary btn-tone-plum ghost-button">
              Why Families Use It
            </Link>
          </div>
        </div>

        {guestLimits ? (
          <div className="status-card">
            <h3>Guest pass status</h3>
            <p>
              You have {guestLimits.game_launches_remaining} game launches and {guestLimits.classics_reads_remaining}{" "}
              classic reads remaining in this guest session.
            </p>
          </div>
        ) : null}

        {error ? <ErrorState message={error} /> : null}
      </section>

      <section className="panel">
        <div className="growth-grid">
          <article className="panel inset-panel">
            <p className="eyebrow">A welcoming first step</p>
            <h3>Start with one classic and one clear challenge</h3>
            <p>The guest preview helps children try the game flow without feeling overloaded.</p>
          </article>
          <article className="panel inset-panel">
            <p className="eyebrow">After signup</p>
            <h3>Unlock the full reader game shelf</h3>
            <p>Free accounts open the full reader game area with more ways to practice words and build confidence.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Launch a preview</p>
            <h2>{catalog?.description ?? "Pick a story and start playing."}</h2>
          </div>
          {selectedStory ? <span className="chip">{selectedStory.source_author}</span> : null}
        </div>

        <div className="filter-row">
          {catalog?.stories.map((story) => (
            <button
              key={story.story_id}
              type="button"
              className={
                selectedStoryId === story.story_id
                  ? "filter-chip btn btn--chip btn-tone-sky active"
                  : "filter-chip btn btn--chip btn-tone-neutral"
              }
              onClick={() => setSelectedStoryId(story.story_id)}
            >
              {story.title ?? "Untitled classic"}
            </button>
          ))}
        </div>

        {selectedStory ? (
          <div className="status-card">
            <h3>{selectedStory.title ?? "Untitled classic"}</h3>
            <p>{selectedStory.preview_text}</p>
            <div className="meta-row">
              {selectedStory.age_range ? <span>{selectedStory.age_range}</span> : null}
              {selectedStory.reading_level ? <span>{selectedStory.reading_level}</span> : null}
            </div>
          </div>
        ) : null}

        <label className="field game-answer-field">
          <span>Preview rounds</span>
          <select value={itemCount} onChange={(event) => setItemCount(Number(event.target.value))}>
            <option value={3}>3 quick words</option>
            <option value={4}>4 quick words</option>
            <option value={5}>5 guided words</option>
          </select>
        </label>

        <div className="hero-actions">
          <StoryBloomActionButton
            type="button"
            family="create"
            shape="star"
            tone="mint"
            icon="🎮"
            onClick={handleLaunchPreview}
            disabled={launching || !selectedStoryId}
          >
            {launching ? "Preparing preview..." : "Start Session"}
          </StoryBloomActionButton>
          {preview ? (
            <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleResetPreview}>
              Choose another story
            </button>
          ) : null}
        </div>
      </section>

      {feedback ? (
        <div className="game-feedback-banner game-feedback-gentle">
          <strong>Guest preview</strong>
          <span>{feedback}</span>
        </div>
      ) : null}

      {preview && payload ? (
        <section className="panel inset-panel">
          <div className="reader-stage-header">
            <div>
              <p className="eyebrow">Guest preview</p>
              <h2>{preview.story_title ?? "Classic preview"}</h2>
              <p className="reader-stage-subtitle">
                {isSessionComplete
                  ? "Preview complete"
                  : `Round ${Math.min(currentRoundIndex + 1, payload.rounds.length)} of ${payload.rounds.length}`}
              </p>
            </div>
          </div>

          {!isSessionComplete && currentRound ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Clue</p>
                <h3>{currentRound.clue}</h3>
                {currentRound.example_sentence ? <p>{currentRound.example_sentence}</p> : null}
              </article>

              <div className="game-pattern-row" aria-label="Current word pattern">
                {revealedPattern.map((letter, index) => (
                  <span key={`${currentRound.round_id}-${index}`} className="game-letter-slot">
                    {letter}
                  </span>
                ))}
              </div>

              <div className="game-figure-row" aria-label="Friendly figure progress">
                {payload.figure_steps.map((step, index) => (
                  <span key={step} className={index < incorrectLetters.length ? "game-figure-piece active" : "game-figure-piece"}>
                    {step.replace("_", " ")}
                  </span>
                ))}
              </div>

              <div className="game-letter-grid">
                {ALPHABET.map((letter) => {
                  const isUsed = guessedLetters.includes(letter);
                  const isHit = isUsed && currentRound.normalized_word.includes(letter);
                  const isMiss = isUsed && !currentRound.normalized_word.includes(letter);
                  return (
                    <button
                      key={letter}
                      type="button"
                      className={["game-letter-button", isHit ? "game-letter-hit" : "", isMiss ? "game-letter-miss" : ""].filter(Boolean).join(" ")}
                      disabled={isUsed || roundSolved || roundMissed}
                      onClick={() => handleGuessLetter(letter)}
                    >
                      {letter}
                    </button>
                  );
                })}
              </div>

              {roundSolved || roundMissed ? (
                <div className={roundSolved ? "status-card game-outcome-card success" : "status-card game-outcome-card"}>
                  <h3>{roundSolved ? "Nice work" : "Let's learn from this one"}</h3>
                  <p>{roundSolved ? `You built "${currentRound.target_word}".` : `The word was "${currentRound.target_word}".`}</p>
                  <button type="button" className="btn btn--primary btn-tone-gold primary-button" onClick={handleContinue}>
                    {currentRoundIndex >= payload.rounds.length - 1 ? "See preview summary" : "Next word"}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}

          {isSessionComplete ? (
            <div className="game-summary-grid">
              <article className="status-card">
                <h3>Preview complete</h3>
                <p>You solved {completedWords.length} of {payload.rounds.length} words in the guest preview.</p>
              </article>
              <article className="status-card">
                <h3>What comes next</h3>
                <p>Create a free account to open the full child game hub and save progress into goals and analytics.</p>
              </article>
              <div className="library-action-row">
                <Link to={account ? "/chooser" : "/register"} className="btn btn--create btn-tone-mint primary-button">
                  {account ? "Open Family Space" : "Create Account"}
                </Link>
                <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleResetPreview}>
                  Try another classic
                </button>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
