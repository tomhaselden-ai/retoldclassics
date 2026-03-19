import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderAreaNav } from "../components/ReaderAreaNav";
import {
  completeReaderGameSession,
  createReaderGameSession,
  getReaderGameCatalog,
  getReaderGameHistory,
  getReaderGamePracticeSummary,
  getReaderLibrary,
  type GameHistoryItem,
  type ReaderGamePracticeSummaryResponse,
  type ReaderLibraryResponse,
  type V1GameCatalogResponse,
  type V1GameCompletionAttemptInput,
  type V1GameSessionResponse,
} from "../services/api";
import { useAuth } from "../services/auth";

type LiveGameType = "build_the_word" | "guess_the_word" | "word_match" | "word_scramble" | "flash_cards" | "crossword";
type FeedbackKind = "success" | "gentle" | "complete";

interface FeedbackState {
  kind: FeedbackKind;
  message: string;
  key: number;
}

interface RoundOutcomeState {
  correct: boolean;
  skipped: boolean;
  message: string;
}

interface BuildTheWordRound {
  round_id: string;
  word_id: number | null;
  target_word: string;
  normalized_word: string;
  clue: string;
  example_sentence: string | null;
  letter_count: number;
  starting_pattern: string[];
}

interface GuessTheWordRound {
  round_id: string;
  word_id: number | null;
  target_word: string;
  normalized_word: string;
  clue: string;
  letter_boxes: number;
  example_sentence: string | null;
}

interface BuildTheWordPayload {
  game_type: "build_the_word";
  difficulty_level: number;
  item_count: number;
  max_incorrect_guesses: number;
  figure_steps: string[];
  rounds: BuildTheWordRound[];
}

interface GuessTheWordPayload {
  game_type: "guess_the_word";
  difficulty_level: number;
  item_count: number;
  rounds: GuessTheWordRound[];
}

interface WordMatchCard {
  card_id: string;
  pair_id: string;
  card_type: "word" | "meaning";
  value: string;
  word_id: number | null;
}

interface WordMatchPayload {
  game_type: "word_match";
  difficulty_level: number;
  item_count: number;
  grid: {
    columns: number;
    rows: number;
    cards: WordMatchCard[];
  };
}

interface WordScrambleRound {
  round_id: string;
  word_id: number | null;
  target_word: string;
  normalized_word: string;
  scrambled_letters: string[];
  clue: string;
}

interface WordScramblePayload {
  game_type: "word_scramble";
  difficulty_level: number;
  item_count: number;
  rounds: WordScrambleRound[];
}

interface FlashCardItem {
  card_id: string;
  word_id: number | null;
  front_text: string;
  back_text: string;
  example_sentence: string | null;
}

interface FlashCardsPayload {
  game_type: "flash_cards";
  difficulty_level: number;
  item_count: number;
  cards: FlashCardItem[];
}

interface CrosswordCell {
  row: number;
  column: number;
  solution: string;
  clue_number: number | null;
  across_entry_id: string | null;
  down_entry_id: string | null;
}

interface CrosswordEntry {
  entry_id: string;
  word_id: number | null;
  display_word: string;
  answer: string;
  clue: string;
  example_sentence: string | null;
  direction: "across" | "down";
  row: number;
  column: number;
  clue_number: number;
  length: number;
}

interface CrosswordPayload {
  game_type: "crossword";
  difficulty_level: number;
  item_count: number;
  crossword: {
    rows: number;
    columns: number;
    cells: CrosswordCell[];
    entries: CrosswordEntry[];
    across_clues: CrosswordEntry[];
    down_clues: CrosswordEntry[];
  };
  launch_config?: {
    hint_mode?: string;
    session_size?: number;
    source_reason?: string;
    launch_mode?: string;
    auto_selected_story?: number | null;
  };
}

const LIVE_GAME_OPTIONS: Array<{
  gameType: LiveGameType;
  label: string;
  description: string;
  encouragement: string;
}> = [
  {
    gameType: "build_the_word",
    label: "Build the Word",
    description: "Guess letters to reveal each hidden word with a friendly growing figure.",
    encouragement: "Great for playful spelling and noticing letter patterns.",
  },
  {
    gameType: "guess_the_word",
    label: "Guess the Word",
    description: "Read the clue and type the matching word into the letter boxes.",
    encouragement: "Great for connecting new words to their meanings.",
  },
  {
    gameType: "word_match",
    label: "Word Match",
    description: "Flip cards and match each word to its meaning on a memory board.",
    encouragement: "Great for memory, focus, and meaning building.",
  },
  {
    gameType: "word_scramble",
    label: "Word Scramble",
    description: "Tap the mixed-up letters into the right order.",
    encouragement: "Great for seeing how word parts fit together.",
  },
  {
    gameType: "flash_cards",
    label: "Flash Cards",
    description: "Flip word cards and mark what feels known or needs more practice.",
    encouragement: "Great for fast review without pressure.",
  },
  {
    gameType: "crossword",
    label: "Crossword",
    description: "Fill a connected word grid using gentle clues from reading and vocabulary practice.",
    encouragement: "Great for spelling, clue reading, and noticing how words connect.",
  },
];

const FEEDBACK_MESSAGES = {
  incorrect: ["Good try. Let's keep going.", "Almost there. Try again.", "You're learning as you play."],
  complete: ["Practice complete!", "You finished strong!", "That session is ready to save!"],
};

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

function normalizeWord(value: string): string {
  return value.replace(/[^A-Za-z]/g, "").toUpperCase();
}

function formatGameType(gameType: string | null): string {
  if (!gameType) {
    return "Game";
  }
  return gameType
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatPracticeTime(totalSeconds: number): string {
  if (totalSeconds < 60) {
    return `${totalSeconds} sec`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds > 0 ? `${minutes} min ${seconds} sec` : `${minutes} min`;
}

function describeTrend(value: string): string {
  if (value === "improving") {
    return "Improving";
  }
  if (value === "needs_support") {
    return "Needs support";
  }
  if (value === "steady") {
    return "Steady";
  }
  return "Building";
}

function pickMessage(messages: string[], key: number): string {
  return messages[key % messages.length];
}

function getAudioContextConstructor(): typeof AudioContext | null {
  if (typeof window === "undefined") {
    return null;
  }
  const audioWindow = window as Window & { webkitAudioContext?: typeof AudioContext };
  return (typeof AudioContext !== "undefined" ? AudioContext : audioWindow.webkitAudioContext) ?? null;
}

function isBuildTheWordPayload(payload: unknown): payload is BuildTheWordPayload {
  const candidate = payload as Partial<BuildTheWordPayload> | null;
  return (
    !!candidate &&
    candidate.game_type === "build_the_word" &&
    Array.isArray(candidate.rounds) &&
    Array.isArray(candidate.figure_steps) &&
    typeof candidate.max_incorrect_guesses === "number"
  );
}

function isGuessTheWordPayload(payload: unknown): payload is GuessTheWordPayload {
  const candidate = payload as Partial<GuessTheWordPayload> | null;
  return !!candidate && candidate.game_type === "guess_the_word" && Array.isArray(candidate.rounds);
}

function isWordMatchPayload(payload: unknown): payload is WordMatchPayload {
  const candidate = payload as Partial<WordMatchPayload> | null;
  return !!candidate && candidate.game_type === "word_match" && !!candidate.grid && Array.isArray(candidate.grid.cards);
}

function isWordScramblePayload(payload: unknown): payload is WordScramblePayload {
  const candidate = payload as Partial<WordScramblePayload> | null;
  return !!candidate && candidate.game_type === "word_scramble" && Array.isArray(candidate.rounds);
}

function isFlashCardsPayload(payload: unknown): payload is FlashCardsPayload {
  const candidate = payload as Partial<FlashCardsPayload> | null;
  return !!candidate && candidate.game_type === "flash_cards" && Array.isArray(candidate.cards);
}

function isCrosswordPayload(payload: unknown): payload is CrosswordPayload {
  const candidate = payload as Partial<CrosswordPayload> | null;
  return !!candidate && candidate.game_type === "crossword" && !!candidate.crossword && Array.isArray(candidate.crossword.entries);
}

export function GameShelfPage() {
  const { readerId } = useParams();
  const { token } = useAuth();
  const audioContextRef = useRef<AudioContext | null>(null);
  const liveSessionRef = useRef<HTMLElement | null>(null);

  const [catalog, setCatalog] = useState<V1GameCatalogResponse | null>(null);
  const [library, setLibrary] = useState<ReaderLibraryResponse | null>(null);
  const [history, setHistory] = useState<GameHistoryItem[]>([]);
  const [practiceSummary, setPracticeSummary] = useState<ReaderGamePracticeSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [selectedGameType, setSelectedGameType] = useState<LiveGameType>("build_the_word");
  const [startingSession, setStartingSession] = useState(false);
  const [savingSession, setSavingSession] = useState(false);

  const [activeSession, setActiveSession] = useState<V1GameSessionResponse | null>(null);
  const [sessionStartedAtMs, setSessionStartedAtMs] = useState<number | null>(null);
  const [currentRoundIndex, setCurrentRoundIndex] = useState(0);
  const [roundStartedAtMs, setRoundStartedAtMs] = useState<number | null>(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [roundOutcome, setRoundOutcome] = useState<RoundOutcomeState | null>(null);
  const [roundResults, setRoundResults] = useState<V1GameCompletionAttemptInput[]>([]);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);

  const [guessedLetters, setGuessedLetters] = useState<string[]>([]);
  const [guessInput, setGuessInput] = useState("");
  const [guessAttemptCount, setGuessAttemptCount] = useState(0);
  const [wordMatchSelectedCardIds, setWordMatchSelectedCardIds] = useState<string[]>([]);
  const [wordMatchMatchedPairIds, setWordMatchMatchedPairIds] = useState<string[]>([]);
  const [wordMatchPairAttempts, setWordMatchPairAttempts] = useState<Record<string, number>>({});
  const [wordMatchLocked, setWordMatchLocked] = useState(false);
  const [scrambleSelection, setScrambleSelection] = useState<number[]>([]);
  const [scrambleAttemptCount, setScrambleAttemptCount] = useState(0);
  const [flashCardFlipped, setFlashCardFlipped] = useState(false);
  const [crosswordInput, setCrosswordInput] = useState("");
  const [crosswordAttemptCount, setCrosswordAttemptCount] = useState(0);
  const [crosswordSolvedEntryIds, setCrosswordSolvedEntryIds] = useState<string[]>([]);
  const [crosswordSolvedAnswers, setCrosswordSolvedAnswers] = useState<Record<string, string>>({});

  async function loadShelf(activeToken: string, activeReaderId: number) {
    const [catalogPayload, libraryPayload, historyPayload, practiceSummaryPayload] = await Promise.all([
      getReaderGameCatalog(activeReaderId, activeToken),
      getReaderLibrary(activeReaderId, activeToken),
      getReaderGameHistory(activeReaderId, activeToken),
      getReaderGamePracticeSummary(activeReaderId, activeToken),
    ]);
    setCatalog(catalogPayload);
    setLibrary(libraryPayload);
    setHistory(historyPayload);
    setPracticeSummary(practiceSummaryPayload);
  }

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    setLoading(true);
    loadShelf(token, Number(readerId))
      .then(() => {
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to open the game shelf."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

  useEffect(() => {
    if (!feedback) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setFeedback((current) => (current?.key === feedback.key ? null : current));
    }, feedback.kind === "complete" ? 3200 : 1800);
    return () => window.clearTimeout(timeoutId);
  }, [feedback]);

  const buildPayload = useMemo(() => {
    if (!activeSession || activeSession.game_type !== "build_the_word") {
      return null;
    }
    const payload = activeSession.payload as Record<string, unknown> | null;
    return isBuildTheWordPayload(payload) ? payload : null;
  }, [activeSession]);

  const guessPayload = useMemo(() => {
    if (!activeSession || activeSession.game_type !== "guess_the_word") {
      return null;
    }
    const payload = activeSession.payload as Record<string, unknown> | null;
    return isGuessTheWordPayload(payload) ? payload : null;
  }, [activeSession]);

  const wordMatchPayload = useMemo(() => {
    if (!activeSession || activeSession.game_type !== "word_match") {
      return null;
    }
    const payload = activeSession.payload as Record<string, unknown> | null;
    return isWordMatchPayload(payload) ? payload : null;
  }, [activeSession]);

  const wordScramblePayload = useMemo(() => {
    if (!activeSession || activeSession.game_type !== "word_scramble") {
      return null;
    }
    const payload = activeSession.payload as Record<string, unknown> | null;
    return isWordScramblePayload(payload) ? payload : null;
  }, [activeSession]);

  const flashCardsPayload = useMemo(() => {
    if (!activeSession || activeSession.game_type !== "flash_cards") {
      return null;
    }
    const payload = activeSession.payload as Record<string, unknown> | null;
    return isFlashCardsPayload(payload) ? payload : null;
  }, [activeSession]);

  const crosswordPayload = useMemo(() => {
    if (!activeSession || activeSession.game_type !== "crossword") {
      return null;
    }
    const payload = activeSession.payload as Record<string, unknown> | null;
    return isCrosswordPayload(payload) ? payload : null;
  }, [activeSession]);

  const buildRound = buildPayload?.rounds[currentRoundIndex] ?? null;
  const guessRound = guessPayload?.rounds[currentRoundIndex] ?? null;
  const scrambleRound = wordScramblePayload?.rounds[currentRoundIndex] ?? null;
  const flashCard = flashCardsPayload?.cards[currentRoundIndex] ?? null;
  const crosswordEntry = crosswordPayload?.crossword.entries[currentRoundIndex] ?? null;

  const totalRounds =
    buildPayload?.rounds.length ??
    guessPayload?.rounds.length ??
    wordScramblePayload?.rounds.length ??
    flashCardsPayload?.cards.length ??
    crosswordPayload?.crossword.entries.length ??
    (wordMatchPayload ? wordMatchPayload.grid.cards.length / 2 : 0);
  const elapsedSeconds = sessionStartedAtMs ? Math.max(1, Math.round((Date.now() - sessionStartedAtMs) / 1000)) : 0;
  const currentRoundElapsedSeconds = roundStartedAtMs
    ? Math.max(1, Math.round((Date.now() - roundStartedAtMs) / 1000))
    : 1;

  const incorrectBuildLetters = useMemo(() => {
    if (!buildRound) {
      return [];
    }
    return guessedLetters.filter((letter) => !buildRound.normalized_word.includes(letter));
  }, [buildRound, guessedLetters]);

  const revealedBuildPattern = useMemo(() => {
    if (!buildRound) {
      return [];
    }
    const guessedSet = new Set(guessedLetters);
    return buildRound.normalized_word.split("").map((letter) => (guessedSet.has(letter) ? letter : "_"));
  }, [buildRound, guessedLetters]);

  const scrambleAnswer = useMemo(() => {
    if (!scrambleRound) {
      return "";
    }
    return scrambleSelection.map((index) => scrambleRound.scrambled_letters[index]).join("");
  }, [scrambleRound, scrambleSelection]);

  const wordMatchCards = wordMatchPayload?.grid.cards ?? [];
  const launchConfig = (activeSession?.payload as { launch_config?: CrosswordPayload["launch_config"] } | undefined)?.launch_config;
  const visibleWordMatchCardIds = useMemo(() => {
    const visible = new Set(wordMatchSelectedCardIds);
    wordMatchMatchedPairIds.forEach((pairId) => {
      wordMatchCards
        .filter((card) => card.pair_id === pairId)
        .forEach((card) => visible.add(card.card_id));
    });
    return visible;
  }, [wordMatchCards, wordMatchMatchedPairIds, wordMatchSelectedCardIds]);

  const crosswordCellMap = useMemo(() => {
    return new Map((crosswordPayload?.crossword.cells ?? []).map((cell) => [`${cell.row}-${cell.column}`, cell]));
  }, [crosswordPayload]);

  const crosswordVisibleLetters = useMemo(() => {
    const visible = new Map<string, string>();
    Object.entries(crosswordSolvedAnswers).forEach(([entryId, answer]) => {
      const entry = crosswordPayload?.crossword.entries.find((candidate) => candidate.entry_id === entryId);
      if (!entry) {
        return;
      }
      answer.split("").forEach((letter, index) => {
        const row = entry.direction === "down" ? entry.row + index : entry.row;
        const column = entry.direction === "across" ? entry.column + index : entry.column;
        visible.set(`${row}-${column}`, letter);
      });
    });
    if (crosswordEntry) {
      normalizeWord(crosswordInput)
        .slice(0, crosswordEntry.length)
        .split("")
        .forEach((letter, index) => {
          const row = crosswordEntry.direction === "down" ? crosswordEntry.row + index : crosswordEntry.row;
          const column = crosswordEntry.direction === "across" ? crosswordEntry.column + index : crosswordEntry.column;
          visible.set(`${row}-${column}`, letter);
        });
      if (launchConfig?.hint_mode === "guided" && crosswordEntry.answer.length > 0) {
        visible.set(`${crosswordEntry.row}-${crosswordEntry.column}`, crosswordEntry.answer[0]);
      }
    }
    return visible;
  }, [crosswordEntry, crosswordInput, crosswordPayload, crosswordSolvedAnswers, launchConfig?.hint_mode]);

  function playFeedbackTone(kind: FeedbackKind) {
    const constructor = getAudioContextConstructor();
    if (!constructor) {
      return;
    }

    if (!audioContextRef.current) {
      audioContextRef.current = new constructor();
    }

    const context = audioContextRef.current;
    if (!context) {
      return;
    }

    void context.resume();

    const frequencies =
      kind === "success" ? [440, 554.37] : kind === "complete" ? [440, 554.37, 659.25] : [330, 261.63];

    const startAt = context.currentTime + 0.01;
    frequencies.forEach((frequency, index) => {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      const noteStart = startAt + index * 0.08;

      oscillator.type = kind === "gentle" ? "triangle" : "sine";
      oscillator.frequency.setValueAtTime(frequency, noteStart);
      gain.gain.setValueAtTime(0.0001, noteStart);
      gain.gain.linearRampToValueAtTime(kind === "complete" ? 0.075 : 0.06, noteStart + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.18);

      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(noteStart);
      oscillator.stop(noteStart + 0.2);
    });
  }

  function pushFeedback(kind: FeedbackKind, message: string) {
    setFeedback({ kind, message, key: Date.now() });
    playFeedbackTone(kind);
  }

  function resetRoundState() {
    setGuessedLetters([]);
    setGuessInput("");
    setGuessAttemptCount(0);
    setWordMatchSelectedCardIds([]);
    setWordMatchLocked(false);
    setScrambleSelection([]);
    setScrambleAttemptCount(0);
    setFlashCardFlipped(false);
    setCrosswordInput("");
    setCrosswordAttemptCount(0);
    setRoundOutcome(null);
    setRoundStartedAtMs(Date.now());
  }

  function clearActiveSession(message?: string) {
    setActiveSession(null);
    setSessionStartedAtMs(null);
    setCurrentRoundIndex(0);
    setRoundStartedAtMs(null);
    setSessionComplete(false);
    setRoundOutcome(null);
    setRoundResults([]);
    setGuessedLetters([]);
    setGuessInput("");
    setGuessAttemptCount(0);
    setWordMatchSelectedCardIds([]);
    setWordMatchMatchedPairIds([]);
    setWordMatchPairAttempts({});
    setWordMatchLocked(false);
    setScrambleSelection([]);
    setScrambleAttemptCount(0);
    setFlashCardFlipped(false);
    setCrosswordInput("");
    setCrosswordAttemptCount(0);
    setCrosswordSolvedEntryIds([]);
    setCrosswordSolvedAnswers({});
    if (message) {
      setNotice(message);
    }
  }

  async function handleStartSession(gameType: LiveGameType) {
    if (!token || !readerId) {
      return;
    }

    if (activeSession) {
      clearActiveSession("Previous practice session closed without saving.");
    }

    setStartingSession(true);
    setError(null);
    setSelectedGameType(gameType);
    const selectedGame = LIVE_GAME_OPTIONS.find((option) => option.gameType === gameType) ?? LIVE_GAME_OPTIONS[0];

    try {
      const session = await createReaderGameSession(
        Number(readerId),
        {
          game_type: gameType,
        },
        token,
      );

      setActiveSession(session);
      setSessionStartedAtMs(Date.now());
      setCurrentRoundIndex(0);
      setRoundResults([]);
      setSessionComplete(false);
      setWordMatchMatchedPairIds([]);
      setWordMatchPairAttempts({});
      setCrosswordSolvedEntryIds([]);
      setCrosswordSolvedAnswers({});
      resetRoundState();
      setNotice(`${selectedGame.label} is ready to play.`);
      await loadShelf(token, Number(readerId));
      window.requestAnimationFrame(() => {
        liveSessionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start this practice session.");
    } finally {
      setStartingSession(false);
    }
  }

  function finishRound(result: V1GameCompletionAttemptInput, message: string, kind: FeedbackKind) {
    setRoundResults((current) => [...current, result]);
    setRoundOutcome({
      correct: result.correct,
      skipped: Boolean(result.skipped),
      message,
    });
    pushFeedback(kind, message);
  }

  function handleBuildLetter(letter: string) {
    if (!buildRound || roundOutcome || sessionComplete) {
      return;
    }
    if (guessedLetters.includes(letter)) {
      return;
    }

    const nextLetters = [...guessedLetters, letter];
    setGuessedLetters(nextLetters);

    const normalizedWord = buildRound.normalized_word;
    const solved = normalizedWord.split("").every((character) => nextLetters.includes(character));
    const missCount = nextLetters.filter((candidate) => !normalizedWord.includes(candidate)).length;

    if (solved) {
      finishRound(
        {
          word_id: buildRound.word_id ?? undefined,
          word_text: buildRound.target_word,
          attempt_count: nextLetters.length,
          correct: true,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: false,
          skipped: false,
        },
        `You built "${buildRound.target_word}".`,
        "success",
      );
      return;
    }

    if (!normalizedWord.includes(letter)) {
      if (missCount >= buildPayload!.max_incorrect_guesses) {
        finishRound(
          {
            word_id: buildRound.word_id ?? undefined,
            word_text: buildRound.target_word,
            attempt_count: nextLetters.length,
            correct: false,
            time_spent_seconds: currentRoundElapsedSeconds,
            hint_used: false,
            skipped: false,
          },
          `The word was "${buildRound.target_word}".`,
          "gentle",
        );
        return;
      }

      pushFeedback("gentle", pickMessage(FEEDBACK_MESSAGES.incorrect, nextLetters.length));
    }
  }

  function handleSkipCurrentRound() {
    if (sessionComplete || roundOutcome) {
      return;
    }

    const activeRound =
      buildRound ??
      guessRound ??
      scrambleRound ??
      (crosswordEntry
        ? {
            word_id: crosswordEntry.word_id,
            target_word: crosswordEntry.display_word,
          }
        : null) ??
      (flashCard
        ? {
            word_id: flashCard.word_id,
            target_word: flashCard.front_text,
          }
        : null);
    if (!activeRound || activeSession?.game_type === "word_match") {
      return;
    }

    finishRound(
      {
        word_id: activeRound.word_id ?? undefined,
        word_text: activeRound.target_word,
        attempt_count:
          activeSession?.game_type === "guess_the_word"
            ? guessAttemptCount
            : activeSession?.game_type === "word_scramble"
              ? scrambleAttemptCount
              : activeSession?.game_type === "crossword"
                ? crosswordAttemptCount
              : activeSession?.game_type === "flash_cards"
                ? 1
                : guessedLetters.length,
        correct: false,
        time_spent_seconds: currentRoundElapsedSeconds,
        hint_used: activeSession?.game_type === "crossword" && launchConfig?.hint_mode === "guided",
        skipped: true,
      },
      `We'll come back to "${activeRound.target_word}" another time.`,
      "gentle",
    );
  }

  function handleGuessSubmit() {
    if (!guessRound || roundOutcome || sessionComplete) {
      return;
    }

    const normalizedGuess = normalizeWord(guessInput);
    if (!normalizedGuess) {
      return;
    }

    const nextAttemptCount = guessAttemptCount + 1;
    setGuessAttemptCount(nextAttemptCount);

    if (normalizedGuess === guessRound.normalized_word) {
      finishRound(
        {
          word_id: guessRound.word_id ?? undefined,
          word_text: guessRound.target_word,
          attempt_count: nextAttemptCount,
          correct: true,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: false,
          skipped: false,
        },
        `You guessed "${guessRound.target_word}".`,
        "success",
      );
      return;
    }

    if (nextAttemptCount >= 3) {
      finishRound(
        {
          word_id: guessRound.word_id ?? undefined,
          word_text: guessRound.target_word,
          attempt_count: nextAttemptCount,
          correct: false,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: false,
          skipped: false,
        },
        `The answer was "${guessRound.target_word}".`,
        "gentle",
      );
      return;
    }

    pushFeedback("gentle", pickMessage(FEEDBACK_MESSAGES.incorrect, nextAttemptCount));
  }

  function handleWordMatchCard(cardId: string) {
    if (!wordMatchPayload || roundOutcome || sessionComplete || wordMatchLocked) {
      return;
    }

    const card = wordMatchCards.find((candidate) => candidate.card_id === cardId);
    if (!card || wordMatchMatchedPairIds.includes(card.pair_id) || wordMatchSelectedCardIds.includes(cardId)) {
      return;
    }

    const nextSelected = [...wordMatchSelectedCardIds, cardId];
    setWordMatchSelectedCardIds(nextSelected);

    if (nextSelected.length < 2) {
      return;
    }

    const firstCard = wordMatchCards.find((candidate) => candidate.card_id === nextSelected[0]);
    const secondCard = wordMatchCards.find((candidate) => candidate.card_id === nextSelected[1]);
    if (!firstCard || !secondCard) {
      setWordMatchSelectedCardIds([]);
      return;
    }

    setWordMatchLocked(true);

    const nextAttemptCount = (wordMatchPairAttempts[firstCard.pair_id] ?? 0) + 1;

    setWordMatchPairAttempts((current) => ({
      ...current,
      [firstCard.pair_id]: nextAttemptCount,
      [secondCard.pair_id]:
        firstCard.pair_id === secondCard.pair_id ? nextAttemptCount : (current[secondCard.pair_id] ?? 0) + 1,
    }));

    if (firstCard.pair_id === secondCard.pair_id) {
      window.setTimeout(() => {
        setWordMatchMatchedPairIds((current) => [...current, firstCard.pair_id]);
        setWordMatchSelectedCardIds([]);
        setWordMatchLocked(false);
        finishRound(
          {
            word_id: firstCard.word_id ?? undefined,
            word_text: firstCard.card_type === "word" ? firstCard.value : secondCard.value,
            attempt_count: nextAttemptCount,
            correct: true,
            time_spent_seconds: currentRoundElapsedSeconds,
            hint_used: false,
            skipped: false,
          },
          `You matched "${firstCard.card_type === "word" ? firstCard.value : secondCard.value}".`,
          "success",
        );
      }, 220);
      return;
    }

    window.setTimeout(() => {
      setWordMatchSelectedCardIds([]);
      setWordMatchLocked(false);
      pushFeedback("gentle", pickMessage(FEEDBACK_MESSAGES.incorrect, nextSelected.length));
    }, 650);
  }

  function handleScrambleTile(index: number) {
    if (!scrambleRound || roundOutcome || sessionComplete || scrambleSelection.includes(index)) {
      return;
    }
    setScrambleSelection((current) => [...current, index]);
  }

  function handleScrambleBackspace() {
    if (roundOutcome || sessionComplete) {
      return;
    }
    setScrambleSelection((current) => current.slice(0, -1));
  }

  function handleScrambleClear() {
    if (roundOutcome || sessionComplete) {
      return;
    }
    setScrambleSelection([]);
  }

  function handleScrambleSubmit() {
    if (!scrambleRound || roundOutcome || sessionComplete || scrambleAnswer.length === 0) {
      return;
    }

    const nextAttemptCount = scrambleAttemptCount + 1;
    setScrambleAttemptCount(nextAttemptCount);

    if (scrambleAnswer === scrambleRound.normalized_word) {
      finishRound(
        {
          word_id: scrambleRound.word_id ?? undefined,
          word_text: scrambleRound.target_word,
          attempt_count: nextAttemptCount,
          correct: true,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: false,
          skipped: false,
        },
        `You unscrambled "${scrambleRound.target_word}".`,
        "success",
      );
      return;
    }

    if (nextAttemptCount >= 3) {
      finishRound(
        {
          word_id: scrambleRound.word_id ?? undefined,
          word_text: scrambleRound.target_word,
          attempt_count: nextAttemptCount,
          correct: false,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: false,
          skipped: false,
        },
        `The word was "${scrambleRound.target_word}".`,
        "gentle",
      );
      return;
    }

    pushFeedback("gentle", pickMessage(FEEDBACK_MESSAGES.incorrect, nextAttemptCount));
  }

  function handleFlashCardDecision(correct: boolean) {
    if (!flashCard || roundOutcome || sessionComplete) {
      return;
    }

    finishRound(
      {
        word_id: flashCard.word_id ?? undefined,
        word_text: flashCard.front_text,
        attempt_count: 1,
        correct,
        time_spent_seconds: currentRoundElapsedSeconds,
        hint_used: false,
        skipped: false,
      },
      correct ? `You felt strong about "${flashCard.front_text}".` : `We'll practice "${flashCard.front_text}" again soon.`,
      correct ? "success" : "gentle",
    );
  }

  function handleCrosswordSubmit() {
    if (!crosswordEntry || roundOutcome || sessionComplete) {
      return;
    }

    const normalizedGuess = normalizeWord(crosswordInput);
    if (!normalizedGuess) {
      return;
    }

    const nextAttemptCount = crosswordAttemptCount + 1;
    setCrosswordAttemptCount(nextAttemptCount);

    if (normalizedGuess === crosswordEntry.answer) {
      setCrosswordSolvedEntryIds((current) => [...current, crosswordEntry.entry_id]);
      setCrosswordSolvedAnswers((current) => ({
        ...current,
        [crosswordEntry.entry_id]: crosswordEntry.answer,
      }));
      finishRound(
        {
          word_id: crosswordEntry.word_id ?? undefined,
          word_text: crosswordEntry.display_word,
          attempt_count: nextAttemptCount,
          correct: true,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: launchConfig?.hint_mode === "guided",
          skipped: false,
        },
        `You filled "${crosswordEntry.display_word}" into the crossword.`,
        "success",
      );
      return;
    }

    if (nextAttemptCount >= 3) {
      setCrosswordSolvedAnswers((current) => ({
        ...current,
        [crosswordEntry.entry_id]: crosswordEntry.answer,
      }));
      finishRound(
        {
          word_id: crosswordEntry.word_id ?? undefined,
          word_text: crosswordEntry.display_word,
          attempt_count: nextAttemptCount,
          correct: false,
          time_spent_seconds: currentRoundElapsedSeconds,
          hint_used: launchConfig?.hint_mode === "guided",
          skipped: false,
        },
        `The answer was "${crosswordEntry.display_word}".`,
        "gentle",
      );
      return;
    }

    pushFeedback("gentle", pickMessage(FEEDBACK_MESSAGES.incorrect, nextAttemptCount));
  }

  function handleContinue() {
    if (!activeSession) {
      return;
    }

    if (currentRoundIndex >= totalRounds - 1) {
      setSessionComplete(true);
      setRoundOutcome(null);
      pushFeedback("complete", pickMessage(FEEDBACK_MESSAGES.complete, roundResults.length));
      return;
    }

    setCurrentRoundIndex((current) => current + 1);
    resetRoundState();
  }

  async function handleSaveSession() {
    if (!token || !readerId || !activeSession || !sessionComplete || roundResults.length === 0) {
      return;
    }

    setSavingSession(true);
    setError(null);
    setNotice(null);

    try {
      const result = await completeReaderGameSession(
        Number(readerId),
        activeSession.session_id,
        {
          completion_status: "completed",
          duration_seconds: Math.max(1, elapsedSeconds),
          attempts: roundResults,
        },
        token,
      );
      await loadShelf(token, Number(readerId));
      clearActiveSession(
        `Saved ${formatGameType(result.game_type)} with ${result.words_correct} correct out of ${result.words_attempted}.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save the practice session.");
    } finally {
      setSavingSession(false);
    }
  }

  if (loading) {
    return <LoadingState label="Opening the game hub..." />;
  }

  if (error && !library) {
    return <ErrorState message={error} />;
  }

  if (!library || !catalog) {
    return <ErrorState message="Game hub unavailable." />;
  }

  return (
    <section className="panel">
      {error ? <ErrorState message={error} /> : null}

      <div className="section-heading">
        <div>
          <p className="eyebrow">Reader games</p>
          <h1>{library.reader_name ?? "Reader"}'s game hub</h1>
          <p>Simple word play tied to reading practice, with clear steps and gentle feedback built for mobile use.</p>
        </div>
        <div className="library-action-row">
          <Link to={`/reader/${library.reader_id}/words`} className="btn btn--secondary btn-tone-sky ghost-button">
            Open words
          </Link>
          <Link to={`/reader/${library.reader_id}/books`} className="btn btn--secondary btn-tone-sky ghost-button">
            Open books
          </Link>
          <Link to={`/reader/${library.reader_id}`} className="btn btn--secondary btn-tone-sky ghost-button">
            Reader Home
          </Link>
        </div>
      </div>

      <ReaderAreaNav readerId={library.reader_id} />

      {notice ? (
        <div className="status-card dashboard-notice-card">
          <h3>Ready</h3>
          <p>{notice}</p>
        </div>
      ) : null}

      {feedback ? (
        <div className={`game-feedback-banner game-feedback-${feedback.kind}`}>
          <strong>{feedback.kind === "complete" ? "Celebration" : feedback.kind === "success" ? "Nice work" : "Keep going"}</strong>
          <span>{feedback.message}</span>
        </div>
      ) : null}

      <section className="game-hub-grid">
        {LIVE_GAME_OPTIONS.map((option) => (
          <article
            key={option.gameType}
            className={selectedGameType === option.gameType ? "game-hub-card game-hub-card-active" : "game-hub-card"}
          >
            <p className="eyebrow">Available now</p>
            <h2>{option.label}</h2>
            <p>{option.description}</p>
            <p className="helper-text">{option.encouragement}</p>
            <div className="library-action-row">
              <button
                type="button"
                className="btn btn--create btn-tone-mint primary-button"
                onClick={() => void handleStartSession(option.gameType)}
                disabled={startingSession}
              >
                {startingSession && selectedGameType === option.gameType ? "Preparing..." : `Play ${option.label}`}
              </button>
            </div>
          </article>
        ))}
      </section>

      <section className="panel inset-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Instant launch</p>
            <h2>Tap a game and StoryBloom starts the session</h2>
            <p>
              Each launch now auto-selects the difficulty, source, hint style, and session size from this reader&apos;s
              recent practice and reading history.
            </p>
          </div>
          <span className="chip">{catalog.recent_sessions.length} recent sessions</span>
        </div>

        <div className="game-launch-form">
          <div className="game-launch-summary">
            <p className="eyebrow">Adaptive launch</p>
            <h3>Recommended difficulty: level {catalog.recommended_difficulty}</h3>
            <p>
              StoryBloom prefers recent story words first, falls back to the word shelf when needed, and keeps sessions
              short enough for repeat play.
            </p>
          </div>

          <div className="game-launch-summary">
            <p className="eyebrow">Official game set</p>
            <h3>Six live games</h3>
            <p>
              Build the Word, Guess the Word, Word Match, Word Scramble, Flash Cards, and Crossword all launch from the
              same saved-session system.
            </p>
          </div>
        </div>
      </section>

      {activeSession ? (
        <section
          ref={(element) => {
            liveSessionRef.current = element;
          }}
          className="panel inset-panel"
        >
          <div className="reader-stage-header">
            <div>
              <p className="eyebrow">Live session</p>
              <h2>{formatGameType(activeSession.game_type)}</h2>
              <p className="reader-stage-subtitle">
                Round {Math.min(currentRoundIndex + 1, totalRounds)} of {totalRounds} · {elapsedSeconds} seconds so far
              </p>
              {launchConfig ? (
                <p className="helper-text">
                  Auto launch: {(launchConfig.source_reason ?? "adaptive source").replace(/_/g, " ")} | hints{" "}
                  {launchConfig.hint_mode ?? "balanced"} | {launchConfig.session_size ?? totalRounds} prompts
                </p>
              ) : null}
            </div>
            <div className="library-action-row">
              {!sessionComplete ? (
                <button type="button" className="btn btn--danger btn-tone-danger ghost-button" onClick={() => clearActiveSession("Practice session closed without saving.")}>
                  Leave session
                </button>
              ) : null}
            </div>
          </div>

          {!sessionComplete && buildRound && buildPayload ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Clue</p>
                <h3>{buildRound.clue}</h3>
                {launchConfig?.hint_mode !== "light" && buildRound.example_sentence ? <p>{buildRound.example_sentence}</p> : null}
              </article>

              <div className="game-pattern-row" aria-label="Current word pattern">
                {revealedBuildPattern.map((letter, index) => (
                  <span key={`${buildRound.round_id}-${index}`} className="game-letter-slot">
                    {letter}
                  </span>
                ))}
              </div>

              <div className="game-figure-row" aria-label="Friendly figure progress">
                {buildPayload.figure_steps.map((step, index) => (
                  <span key={step} className={index < incorrectBuildLetters.length ? "game-figure-piece active" : "game-figure-piece"}>
                    {step.replace("_", " ")}
                  </span>
                ))}
              </div>

              <div className="game-letter-grid">
                {ALPHABET.map((letter) => {
                  const isUsed = guessedLetters.includes(letter);
                  const isHit = isUsed && buildRound.normalized_word.includes(letter);
                  const isMiss = isUsed && !buildRound.normalized_word.includes(letter);
                  return (
                    <button
                      key={letter}
                      type="button"
                      className={["game-letter-button", isHit ? "game-letter-hit" : "", isMiss ? "game-letter-miss" : ""].filter(Boolean).join(" ")}
                      disabled={isUsed || !!roundOutcome}
                      onClick={() => handleBuildLetter(letter)}
                    >
                      {letter}
                    </button>
                  );
                })}
              </div>

              <div className="library-action-row">
                <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleSkipCurrentRound} disabled={!!roundOutcome}>
                  Skip this word
                </button>
              </div>
            </div>
          ) : null}

          {!sessionComplete && guessRound ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Clue</p>
                <h3>{guessRound.clue}</h3>
                {launchConfig?.hint_mode !== "light" && guessRound.example_sentence ? <p>{guessRound.example_sentence}</p> : null}
              </article>

              <div className="game-pattern-row" aria-label="Letter boxes">
                {Array.from({ length: guessRound.letter_boxes }).map((_, index) => (
                  <span key={`${guessRound.round_id}-${index}`} className="game-letter-slot">
                    {normalizeWord(guessInput)[index] ?? ""}
                  </span>
                ))}
              </div>

              <label className="field game-answer-field">
                <span>Your guess</span>
                <input
                  type="text"
                  value={guessInput}
                  onChange={(event) => setGuessInput(event.target.value)}
                  disabled={!!roundOutcome}
                  autoCapitalize="characters"
                  autoCorrect="off"
                  spellCheck={false}
                  placeholder="Type the word"
                />
              </label>

              <div className="library-action-row">
                <button
                  type="button"
                  className="btn btn--create btn-tone-mint primary-button"
                  onClick={handleGuessSubmit}
                  disabled={!!roundOutcome || normalizeWord(guessInput).length === 0}
                >
                  Check answer
                </button>
                <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleSkipCurrentRound} disabled={!!roundOutcome}>
                  Skip this word
                </button>
              </div>
              <p className="helper-text">You have up to three tries before this round moves on.</p>
            </div>
          ) : null}

          {!sessionComplete && wordMatchPayload ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Memory match</p>
                <h3>Find each word and its meaning.</h3>
                <p>
                  Match all {wordMatchPayload.grid.cards.length / 2} pairs. Each correct match stays open and saves one
                  vocabulary win.
                </p>
              </article>

              <div className="game-match-progress">
                <span>{wordMatchMatchedPairIds.length} pairs matched</span>
                <span>{wordMatchPayload.grid.cards.length / 2 - wordMatchMatchedPairIds.length} left to find</span>
              </div>

              <div
                className="game-match-grid"
                style={{ gridTemplateColumns: `repeat(${wordMatchPayload.grid.columns}, minmax(0, 1fr))` }}
              >
                {wordMatchCards.map((card) => {
                  const isVisible = visibleWordMatchCardIds.has(card.card_id);
                  const isMatched = wordMatchMatchedPairIds.includes(card.pair_id);
                  return (
                    <button
                      key={card.card_id}
                      type="button"
                      className={[
                        "game-match-card",
                        isVisible ? "game-match-card-visible" : "",
                        isMatched ? "game-match-card-matched" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() => handleWordMatchCard(card.card_id)}
                      disabled={!!roundOutcome || isMatched || wordMatchLocked}
                    >
                      {isVisible ? (
                        <>
                          <span className="eyebrow">{card.card_type === "word" ? "Word" : "Meaning"}</span>
                          <strong>{card.value}</strong>
                        </>
                      ) : (
                        <>
                          <span className="eyebrow">Flip</span>
                          <strong>?</strong>
                        </>
                      )}
                    </button>
                  );
                })}
              </div>

              <p className="helper-text">Tap two cards. If they belong together, they stay open and the next match begins.</p>
            </div>
          ) : null}

          {!sessionComplete && scrambleRound ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Word scramble</p>
                <h3>{scrambleRound.clue}</h3>
                <p>Put the letters back into the right order.</p>
              </article>

              <div className="game-pattern-row" aria-label="Your answer">
                {Array.from({ length: scrambleRound.normalized_word.length }).map((_, index) => (
                  <span key={`${scrambleRound.round_id}-${index}`} className="game-letter-slot">
                    {scrambleAnswer[index] ?? ""}
                  </span>
                ))}
              </div>

              <div className="game-scramble-bank">
                {scrambleRound.scrambled_letters.map((letter, index) => {
                  const isUsed = scrambleSelection.includes(index);
                  return (
                    <button
                      key={`${scrambleRound.round_id}-${index}`}
                      type="button"
                      className={["game-scramble-tile", isUsed ? "game-scramble-tile-used" : ""].filter(Boolean).join(" ")}
                      disabled={!!roundOutcome || isUsed}
                      onClick={() => handleScrambleTile(index)}
                    >
                      {letter}
                    </button>
                  );
                })}
              </div>

              <div className="library-action-row">
                <button
                  type="button"
                  className="btn btn--create btn-tone-mint primary-button"
                  onClick={handleScrambleSubmit}
                  disabled={!!roundOutcome || scrambleAnswer.length === 0}
                >
                  Check answer
                </button>
                <button type="button" className="btn btn--control btn-tone-neutral ghost-button" onClick={handleScrambleBackspace} disabled={!!roundOutcome || scrambleSelection.length === 0}>
                  Backspace
                </button>
                <button type="button" className="btn btn--control btn-tone-neutral ghost-button" onClick={handleScrambleClear} disabled={!!roundOutcome || scrambleSelection.length === 0}>
                  Clear
                </button>
                <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleSkipCurrentRound} disabled={!!roundOutcome}>
                  Skip this word
                </button>
              </div>

              <p className="helper-text">You have up to three tries before this word moves on.</p>
            </div>
          ) : null}

          {!sessionComplete && crosswordPayload && crosswordEntry ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Crossword clue</p>
                <h3>
                  {crosswordEntry.clue_number}. {crosswordEntry.clue}
                </h3>
                <p>
                  {crosswordEntry.direction === "across" ? "Across" : "Down"} · {crosswordEntry.length} letters ·{" "}
                  {crosswordSolvedEntryIds.length} solved so far
                </p>
                {launchConfig?.hint_mode !== "light" && crosswordEntry.example_sentence ? <p>{crosswordEntry.example_sentence}</p> : null}
                {launchConfig?.hint_mode === "guided" ? <p className="helper-text">The first letter is revealed for this clue.</p> : null}
              </article>

              <div className="game-crossword-grid" style={{ gridTemplateColumns: `repeat(${crosswordPayload.crossword.columns}, minmax(0, 1fr))` }}>
                {Array.from({ length: crosswordPayload.crossword.rows }).flatMap((_, row) =>
                  Array.from({ length: crosswordPayload.crossword.columns }).map((__, column) => {
                    const key = `${row}-${column}`;
                    const cell = crosswordCellMap.get(key);
                    if (!cell) {
                      return <div key={key} className="game-crossword-cell game-crossword-cell-empty" />;
                    }
                    const isActive =
                      cell.across_entry_id === crosswordEntry.entry_id || cell.down_entry_id === crosswordEntry.entry_id;
                    return (
                      <div
                        key={key}
                        className={[
                          "game-crossword-cell",
                          isActive ? "game-crossword-cell-active" : "",
                          crosswordVisibleLetters.has(key) ? "game-crossword-cell-filled" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      >
                        {cell.clue_number ? <span className="game-crossword-number">{cell.clue_number}</span> : null}
                        <strong>{crosswordVisibleLetters.get(key) ?? ""}</strong>
                      </div>
                    );
                  }),
                )}
              </div>

              <label className="field game-answer-field">
                <span>Your answer</span>
                <input
                  type="text"
                  value={crosswordInput}
                  onChange={(event) => setCrosswordInput(event.target.value)}
                  disabled={!!roundOutcome}
                  autoCapitalize="characters"
                  autoCorrect="off"
                  spellCheck={false}
                  placeholder={`Fill ${crosswordEntry.length} letters`}
                />
              </label>

              <div className="library-action-row">
                <button
                  type="button"
                  className="btn btn--create btn-tone-mint primary-button"
                  onClick={handleCrosswordSubmit}
                  disabled={!!roundOutcome || normalizeWord(crosswordInput).length === 0}
                >
                  Check answer
                </button>
                <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleSkipCurrentRound} disabled={!!roundOutcome}>
                  Skip this clue
                </button>
              </div>

              <div className="game-crossword-clues">
                <article className="panel inset-panel">
                  <p className="eyebrow">Across</p>
                  <div className="tooling-mini-list">
                    {crosswordPayload.crossword.across_clues.map((entry) => (
                      <div
                        key={entry.entry_id}
                        className={entry.entry_id === crosswordEntry.entry_id ? "tooling-mini-card game-crossword-clue-active" : "tooling-mini-card"}
                      >
                        <strong>
                          {entry.clue_number}. {entry.clue}
                        </strong>
                        <p>{entry.length} letters</p>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="panel inset-panel">
                  <p className="eyebrow">Down</p>
                  <div className="tooling-mini-list">
                    {crosswordPayload.crossword.down_clues.map((entry) => (
                      <div
                        key={entry.entry_id}
                        className={entry.entry_id === crosswordEntry.entry_id ? "tooling-mini-card game-crossword-clue-active" : "tooling-mini-card"}
                      >
                        <strong>
                          {entry.clue_number}. {entry.clue}
                        </strong>
                        <p>{entry.length} letters</p>
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            </div>
          ) : null}

          {!sessionComplete && flashCard ? (
            <div className="game-stage-shell">
              <article className="game-clue-card">
                <p className="eyebrow">Flash card</p>
                <h3>Flip the card, then choose how it felt.</h3>
                <p>Quick review counts too. Strong words and tricky words both help shape future practice.</p>
              </article>

              <button
                type="button"
                className={["game-flash-card", flashCardFlipped ? "game-flash-card-flipped" : ""].filter(Boolean).join(" ")}
                onClick={() => setFlashCardFlipped((current) => !current)}
                disabled={!!roundOutcome}
              >
                <span className="eyebrow">{flashCardFlipped ? "Meaning" : "Word"}</span>
                <strong>{flashCardFlipped ? flashCard.back_text : flashCard.front_text}</strong>
                {flashCardFlipped && flashCard.example_sentence ? <span>{flashCard.example_sentence}</span> : null}
              </button>

              <div className="library-action-row">
                {!flashCardFlipped ? (
                  <button type="button" className="btn btn--secondary btn-tone-sky primary-button" onClick={() => setFlashCardFlipped(true)} disabled={!!roundOutcome}>
                    Show meaning
                  </button>
                ) : (
                  <>
                    <button type="button" className="btn btn--create btn-tone-mint primary-button" onClick={() => handleFlashCardDecision(true)} disabled={!!roundOutcome}>
                      I know it
                    </button>
                    <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={() => handleFlashCardDecision(false)} disabled={!!roundOutcome}>
                      Practice again
                    </button>
                  </>
                )}
                <button type="button" className="btn btn--secondary btn-tone-neutral ghost-button" onClick={handleSkipCurrentRound} disabled={!!roundOutcome}>
                  Skip this card
                </button>
              </div>
            </div>
          ) : null}

          {roundOutcome ? (
            <div className={roundOutcome.correct ? "status-card game-outcome-card success" : "status-card game-outcome-card"}>
              <h3>{roundOutcome.correct ? "Correct answer" : roundOutcome.skipped ? "Skipped for now" : "Let's learn from this one"}</h3>
              <p>{roundOutcome.message}</p>
              <button type="button" className="btn btn--primary btn-tone-gold primary-button" onClick={handleContinue}>
                {currentRoundIndex >= totalRounds - 1 ? "Open session summary" : "Next word"}
              </button>
            </div>
          ) : null}

          {sessionComplete ? (
            <div className="game-summary-grid">
              <article className="status-card">
                <h3>Session complete</h3>
                <p>{roundResults.filter((attempt) => attempt.correct).length} correct out of {roundResults.length} words.</p>
              </article>
              <article className="status-card">
                <h3>Time spent</h3>
                <p>{elapsedSeconds} seconds of vocabulary practice.</p>
              </article>
              <article className="status-card">
                <h3>Next step</h3>
                <p>Save this session so it feeds analytics, goals, and future practice.</p>
              </article>
              <div className="library-action-row">
                <button type="button" className="btn btn--create btn-tone-mint primary-button" onClick={handleSaveSession} disabled={savingSession}>
                  {savingSession ? "Saving session..." : "Save session"}
                </button>
                <button
                  type="button"
                  className="btn btn--danger btn-tone-danger ghost-button"
                  onClick={() => clearActiveSession("Practice session closed without saving.")}
                  disabled={savingSession}
                >
                  Leave without saving
                </button>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="panel inset-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Practice rhythm</p>
            <h2>How this game space helps</h2>
            <p>Each session stays short, tracks real word practice, and keeps the feedback calm enough for repeat play.</p>
          </div>
        </div>
        <div className="game-coming-grid">
          <article className="game-coming-card">
            <p className="eyebrow">Short sessions</p>
            <h3>Eight quick moments</h3>
            <p>Practice stays bite-sized so readers can finish strong and come back later.</p>
          </article>
          <article className="game-coming-card">
            <p className="eyebrow">Vocabulary first</p>
            <h3>Words from reading</h3>
            <p>Game rounds reuse the reader&apos;s word shelf and recent stories instead of disconnected trivia.</p>
          </article>
          <article className="game-coming-card">
            <p className="eyebrow">Saved progress</p>
            <h3>Counts toward analytics</h3>
            <p>Completed sessions feed the same literacy tracking used by parent insights and reader goals.</p>
          </article>
        </div>
      </section>

      {practiceSummary ? (
        <section className="panel inset-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Practice snapshot</p>
              <h2>How game practice is building</h2>
              <p>This summary comes from the new active game sessions, not the retired generator flow.</p>
            </div>
          </div>

          <div className="dashboard-summary-grid">
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Sessions this week</p>
              <h3>{practiceSummary.sessions_this_week}</h3>
              <p>{practiceSummary.sessions_total} total saved sessions in the new suite.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Words practiced</p>
              <h3>{practiceSummary.words_practiced}</h3>
              <p>{practiceSummary.words_correct} correct answers saved into active game analytics.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Success rate</p>
              <h3>{practiceSummary.average_success_rate ?? "—"}%</h3>
              <p>Trend: {describeTrend(practiceSummary.improvement_trend)}.</p>
            </article>
            <article className="status-card dashboard-summary-card">
              <p className="eyebrow">Practice time</p>
              <h3>{formatPracticeTime(practiceSummary.practice_time_seconds)}</h3>
              <p>
                Best fit: {formatGameType(practiceSummary.strongest_game_type)} | Support next:{" "}
                {formatGameType(practiceSummary.weakest_game_type)}
              </p>
            </article>
          </div>

          <div className="reader-grid">
            <article className="reader-panel">
              <div>
                <p className="eyebrow">Accuracy by game</p>
                <h3>What feels strongest right now</h3>
              </div>
              <div className="tooling-mini-list">
                {practiceSummary.accuracy_by_game_type.length > 0 ? (
                  practiceSummary.accuracy_by_game_type.map((item) => (
                    <div key={item.game_type} className="tooling-mini-card">
                      <strong>{formatGameType(item.game_type)}</strong>
                      <p>
                        {item.success_rate ?? "—"}% success | {item.words_correct}/{item.words_attempted} words |{" "}
                        {item.sessions_played} sessions
                      </p>
                    </div>
                  ))
                ) : (
                  <p>No completed sessions yet in the new suite.</p>
                )}
              </div>
            </article>

            <article className="reader-panel">
              <div>
                <p className="eyebrow">Repeated missed words</p>
                <h3>Helpful words to revisit</h3>
              </div>
              <div className="tooling-mini-list">
                {practiceSummary.repeated_missed_words.length > 0 ? (
                  practiceSummary.repeated_missed_words.map((item) => (
                    <div key={item.word_text} className="tooling-mini-card">
                      <strong>{item.word_text}</strong>
                      <p>Missed {item.miss_count} times across saved sessions.</p>
                    </div>
                  ))
                ) : (
                  <p>No repeated misses yet. The new suite will start surfacing them as sessions build up.</p>
                )}
              </div>
            </article>
          </div>
        </section>
      ) : null}

      <section className="panel inset-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Saved history</p>
            <h2>Recent game results</h2>
          </div>
        </div>
        <div className="library-grid">
          {history.length > 0 ? (
            history.map((item) => (
              <article key={item.game_result_id} className="panel inset-panel">
                <h3>{formatGameType(item.game_type)}</h3>
                <p>Difficulty {item.difficulty_level ?? "?"}</p>
                <p>Score {item.score ?? "?"}%</p>
                <p>{item.duration_seconds ? `${item.duration_seconds} seconds` : "Duration unavailable"}</p>
              </article>
            ))
          ) : (
            <div className="status-card">
              <h3>No saved sessions yet</h3>
              <p>Complete one of the new games and save it to start building reader analytics.</p>
            </div>
          )}
        </div>
      </section>
    </section>
  );
}
