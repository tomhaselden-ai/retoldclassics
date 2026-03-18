import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";

import { resolveApiAssetUrl, type ClassicReadResponse, type ClassicReadUnit } from "../services/api";

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "0:00";
  }
  const total = Math.floor(seconds);
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function getMarkRange(mark: { start?: number | null; end?: number | null; value?: string | null }) {
  const start = typeof mark.start === "number" ? mark.start : 0;
  if (typeof mark.value === "string" && mark.value.length > 0) {
    return { start, end: start + mark.value.length };
  }
  return { start, end: typeof mark.end === "number" ? mark.end : start };
}

function getTimedUnitWordMarks(unit: ClassicReadUnit) {
  return unit.speech_marks
    .filter(
      (mark) =>
        mark.type === "word" &&
        typeof mark.time === "number" &&
        typeof mark.start === "number" &&
        typeof mark.end === "number",
    )
    .sort((left, right) => {
      if ((left.time ?? 0) !== (right.time ?? 0)) {
        return (left.time ?? 0) - (right.time ?? 0);
      }
      return (left.start ?? 0) - (right.start ?? 0);
    });
}

function getRenderableUnitWordMarks(unit: ClassicReadUnit) {
  return getTimedUnitWordMarks(unit).slice().sort((left, right) => {
    if ((left.start ?? 0) !== (right.start ?? 0)) {
      return (left.start ?? 0) - (right.start ?? 0);
    }
    return (left.end ?? 0) - (right.end ?? 0);
  });
}

function resolveActiveWord(unit: ClassicReadUnit, currentMs: number): { start: number; end: number } | null {
  const wordMarks = getTimedUnitWordMarks(unit);
  if (wordMarks.length === 0) {
    return null;
  }

  let active = wordMarks[0];
  for (const mark of wordMarks) {
    if ((mark.time ?? 0) <= currentMs) {
      active = mark;
    } else {
      break;
    }
  }

  if (typeof active.start !== "number" || typeof active.end !== "number") {
    return null;
  }

  return getMarkRange(active);
}

function renderHighlightedText(unit: ClassicReadUnit, currentMs: number) {
  const activeWord = resolveActiveWord(unit, currentMs);
  if (!activeWord) {
    return unit.text;
  }

  const before = unit.text.slice(0, activeWord.start);
  const active = unit.text.slice(activeWord.start, activeWord.end);
  const after = unit.text.slice(activeWord.end);

  return (
    <>
      {before}
      <mark className="reader-highlight">{active}</mark>
      {after}
    </>
  );
}

function getUnitWordMarks(unit: ClassicReadUnit) {
  return getRenderableUnitWordMarks(unit);
}

function renderInteractiveText(
  unit: ClassicReadUnit,
  currentMs: number,
  onWordClick: (startMs: number) => void,
) {
  const wordMarks = getUnitWordMarks(unit);
  if (wordMarks.length === 0) {
    return renderHighlightedText(unit, currentMs);
  }

  const activeWord = resolveActiveWord(unit, currentMs);
  const fragments: ReactNode[] = [];
  let cursor = 0;

  wordMarks.forEach((mark, index) => {
    const { start, end } = getMarkRange(mark);
    const time = typeof mark.time === "number" ? mark.time : 0;

    if (start > cursor) {
      fragments.push(<span key={`text-${unit.unit_id}-${index}`}>{unit.text.slice(cursor, start)}</span>);
    }

    const wordText = typeof mark.value === "string" && mark.value.length > 0
      ? mark.value
      : unit.text.slice(start, end);
    const isActive = !!activeWord && activeWord.start === start && activeWord.end === end;
    fragments.push(
      <button
        key={`word-${unit.unit_id}-${index}`}
        type="button"
        className={isActive ? "reader-word-button active" : "reader-word-button"}
        onClick={() => onWordClick(time)}
      >
        {wordText}
      </button>,
    );
    cursor = end;
  });

  if (cursor < unit.text.length) {
    fragments.push(<span key={`text-tail-${unit.unit_id}`}>{unit.text.slice(cursor)}</span>);
  }

  return <>{fragments}</>;
}

export function ImmersiveReader({ story }: { story: ClassicReadResponse }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const unitRefs = useRef<Array<HTMLElement | null>>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);

  const currentMs = Math.floor(currentTime * 1000);
  const resolvedAudioUrl = resolveApiAssetUrl(story.audio_url);
  const hasPlayableNarration = Boolean(resolvedAudioUrl);

  const activeIndexFromAudio = useMemo(() => {
    if (!hasPlayableNarration) {
      return activeIndex;
    }

    const found = story.units.findIndex((unit) => {
      if (typeof unit.audio_start_ms !== "number") {
        return false;
      }
      const end = typeof unit.audio_end_ms === "number" ? unit.audio_end_ms : Number.MAX_SAFE_INTEGER;
      return currentMs >= unit.audio_start_ms && currentMs <= end;
    });

    return found >= 0 ? found : activeIndex;
  }, [activeIndex, currentMs, hasPlayableNarration, story.units]);

  const activeUnit = story.units[activeIndexFromAudio];
  const activeLabel =
    activeUnit.unit_type === "title"
      ? "Story Title"
      : activeUnit.scene_title ?? `Part ${Math.max(1, activeUnit.unit_order - 1)}`;
  const activeIllustrationUrl = resolveApiAssetUrl(activeUnit.illustration.image_url ?? story.cover.image_url ?? null);
  const activeIllustrationLabel =
    activeUnit.illustration.prompt_excerpt ??
    activeUnit.scene_title ??
    story.title ??
    "Classic story illustration";

  useEffect(() => {
    const activeElement = unitRefs.current[activeIndexFromAudio];
    if (!activeElement) {
      return;
    }
    activeElement.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [activeIndexFromAudio]);

  useEffect(() => {
    if (!hasPlayableNarration || !audioRef.current) {
      return;
    }
    audioRef.current.volume = volume;
  }, [hasPlayableNarration, volume]);

  useEffect(() => {
    if (!hasPlayableNarration || !audioRef.current) {
      return;
    }

    const audio = audioRef.current;
    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration || 0);
    const onEnded = () => setIsPlaying(false);
    const onPause = () => setIsPlaying(false);
    const onPlay = () => {
      setIsPlaying(true);
      setAudioStatus(null);
    };
    const onCanPlay = () => setAudioStatus(null);
    const onError = () => {
      setIsPlaying(false);
      setAudioStatus("Audio could not be loaded for this classic yet.");
    };

    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("loadedmetadata", updateDuration);
    audio.addEventListener("durationchange", updateDuration);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("canplay", onCanPlay);
    audio.addEventListener("error", onError);

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("loadedmetadata", updateDuration);
      audio.removeEventListener("durationchange", updateDuration);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("canplay", onCanPlay);
      audio.removeEventListener("error", onError);
    };
  }, [hasPlayableNarration]);

  function jumpToUnit(index: number) {
    setActiveIndex(index);
    if (!hasPlayableNarration || !audioRef.current) {
      return;
    }

    const unit = story.units[index];
    if (typeof unit.audio_start_ms === "number") {
      audioRef.current.currentTime = unit.audio_start_ms / 1000;
      setCurrentTime(audioRef.current.currentTime);
    }
  }

  async function togglePlayback() {
    if (!hasPlayableNarration || !audioRef.current) {
      return;
    }
    try {
      if (audioRef.current.paused) {
        await audioRef.current.play();
      } else {
        audioRef.current.pause();
      }
    } catch {
      setAudioStatus("Playback was blocked. Try pressing play again or check that audio is loaded.");
    }
  }

  async function playFromBeginning() {
    if (!hasPlayableNarration || !audioRef.current) {
      return;
    }
    try {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setActiveIndex(0);
      await audioRef.current.play();
    } catch {
      setAudioStatus("Playback was blocked. Try pressing play again or check that audio is loaded.");
    }
  }

  async function playFromWord(startMs: number, index: number) {
    if (!hasPlayableNarration || !audioRef.current) {
      return;
    }
    try {
      const startSeconds = Math.max(0, startMs / 1000);
      setActiveIndex(index);
      audioRef.current.pause();
      audioRef.current.currentTime = startSeconds;
      await audioRef.current.play();
    } catch {
      setAudioStatus("Word-level playback was blocked. Try pressing play once, then click the word again.");
    }
  }

  function handleSeek(seconds: number) {
    if (!audioRef.current) {
      return;
    }
    audioRef.current.currentTime = seconds;
    setCurrentTime(seconds);
  }

  return (
    <section className="reader-experience">
      <aside className="reader-sidebar">
        <div className="reader-stats">
          <span>{story.source_author}</span>
          <span>{story.reading_level ?? "Open reading level"}</span>
          <span>{story.units.length} reading units</span>
          {story.voice ? <span>Voice: {story.voice}</span> : null}
        </div>
        <ol className="reader-unit-list">
          {story.units.map((unit, index) => (
            <li key={unit.unit_id}>
              <button
                type="button"
                className={index === activeIndexFromAudio ? "unit-button active" : "unit-button"}
                onClick={() => jumpToUnit(index)}
              >
                <strong>{unit.unit_type === "title" ? "Story Title" : unit.scene_title ?? `Part ${Math.max(1, unit.unit_order - 1)}`}</strong>
                <span>{unit.text.slice(0, 70)}...</span>
              </button>
            </li>
          ))}
        </ol>
      </aside>

      <div className="reader-stage">
        <div className="reader-stage-header">
          <div>
            <p className="eyebrow">Immersive Reader</p>
            <h2>{story.title ?? "Story moment"}</h2>
            <p className="reader-stage-subtitle">{activeLabel}</p>
          </div>
          <div className="reader-controls">
            <button
              type="button"
              className="ghost-button"
              onClick={() => jumpToUnit(Math.max(0, activeIndexFromAudio - 1))}
              disabled={activeIndexFromAudio === 0}
            >
              Previous
            </button>
            <button
              type="button"
              className="primary-button"
              onClick={() => jumpToUnit(Math.min(story.units.length - 1, activeIndexFromAudio + 1))}
              disabled={activeIndexFromAudio === story.units.length - 1}
            >
              Next
            </button>
          </div>
        </div>

        {activeIllustrationUrl ? (
          <section className="panel reader-illustration-panel">
            <img
              src={activeIllustrationUrl}
              alt={activeIllustrationLabel}
              className="reader-illustration-image"
            />
            {activeUnit.illustration.prompt_excerpt ? (
              <p className="reader-illustration-caption">{activeUnit.illustration.prompt_excerpt}</p>
            ) : null}
          </section>
        ) : null}

        {hasPlayableNarration && resolvedAudioUrl ? (
          <section className="panel reader-media-panel">
            <audio ref={audioRef} src={resolvedAudioUrl} preload="metadata" />
            <div className="reader-media-row">
              <button type="button" className="primary-button" onClick={() => void togglePlayback()}>
                {isPlaying ? "Pause" : "Play"}
              </button>
              <button type="button" className="ghost-button" onClick={() => void playFromBeginning()}>
                Play from beginning
              </button>
              <label className="reader-range">
                <span>Timeline</span>
                <input
                  type="range"
                  min={0}
                  max={duration || 0}
                  step={0.1}
                  value={Math.min(currentTime, duration || currentTime)}
                  onChange={(event) => handleSeek(Number(event.target.value))}
                />
              </label>
              <span className="chip">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>
            <div className="reader-media-row">
              <label className="reader-range reader-volume">
                <span>Volume</span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={volume}
                  onChange={(event) => setVolume(Number(event.target.value))}
                />
              </label>
              {story.generated_at ? <span className="chip">Audio ready</span> : null}
            </div>
            {audioStatus ? <p className="reader-audio-tip">{audioStatus}</p> : null}
            <p className="reader-audio-tip">Click a word in the active section to restart from that word.</p>
          </section>
        ) : (
          <section className="panel reader-media-panel">
            <h3>Text-first immersive reading</h3>
            <p>Audio narration is not available for this classic yet. You can still read it in immersive mode.</p>
          </section>
        )}

        <article className="reader-card story-flow">
          <header className="reader-story-header">
            <p className="eyebrow">Now Reading</p>
            <h3>{story.title ?? "Untitled classic"}</h3>
          </header>
          <div className="reader-story-units">
            {story.units.map((unit, index) => (
              <section
                key={unit.unit_id}
                ref={(element) => {
                  unitRefs.current[index] = element;
                }}
                className={index === activeIndexFromAudio ? "reader-unit-card active" : "reader-unit-card"}
              >
                {unit.unit_type === "title" ? (
                  <p className="reader-title-text">
                    {index === activeIndexFromAudio
                      ? renderInteractiveText(unit, currentMs, (startMs) => {
                          void playFromWord(startMs, index);
                        })
                      : unit.text}
                  </p>
                ) : (
                  <>
                    {unit.scene_title ? <p className="reader-scene-label">{unit.scene_title}</p> : null}
                    <p className="reader-text">
                      {index === activeIndexFromAudio
                        ? renderInteractiveText(unit, currentMs, (startMs) => {
                            void playFromWord(startMs, index);
                          })
                        : unit.text}
                    </p>
                  </>
                )}
                {unit.narration_text && !story.narration_available ? (
                  <div className="reader-note">
                    <strong>Narration note</strong>
                    <p>{unit.narration_text}</p>
                  </div>
                ) : null}
              </section>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
