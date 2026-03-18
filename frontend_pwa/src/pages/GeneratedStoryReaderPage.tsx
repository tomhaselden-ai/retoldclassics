import { type ReactNode, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  getLatestStoryMediaJob,
  getMediaJob,
  getGeneratedStoryRead,
  illustrateGeneratedStory,
  narrateGeneratedStory,
  type MediaJobStatus,
  type GeneratedReadingScene,
  type GeneratedStoryReadResponse,
} from "../services/api";
import { useAuth } from "../services/auth";

function isActiveMediaJob(job: MediaJobStatus | null): job is MediaJobStatus {
  return job?.status === "pending" || job?.status === "processing";
}

function getMarkRange(mark: { start?: number | null; end?: number | null; value?: string | null }) {
  const start = typeof mark.start === "number" ? mark.start : 0;
  if (typeof mark.value === "string" && mark.value.length > 0) {
    return { start, end: start + mark.value.length };
  }
  return { start, end: typeof mark.end === "number" ? mark.end : start };
}

function getTimedSceneWordMarks(scene: GeneratedReadingScene) {
  return scene.speech_marks_json
    .filter(
      (mark) =>
        mark?.type === "word" &&
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

function getRenderableSceneWordMarks(scene: GeneratedReadingScene) {
  return getTimedSceneWordMarks(scene).slice().sort((left, right) => {
    if ((left.start ?? 0) !== (right.start ?? 0)) {
      return (left.start ?? 0) - (right.start ?? 0);
    }
    return (left.end ?? 0) - (right.end ?? 0);
  });
}

function resolveActiveWord(
  scene: GeneratedReadingScene,
  currentMs: number,
): { start: number; end: number } | null {
  const wordMarks = getTimedSceneWordMarks(scene);
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

function renderHighlightedSceneText(scene: GeneratedReadingScene, currentMs: number) {
  const activeWord = resolveActiveWord(scene, currentMs);
  if (!activeWord) {
    return scene.scene_text;
  }

  const before = scene.scene_text.slice(0, activeWord.start);
  const active = scene.scene_text.slice(activeWord.start, activeWord.end);
  const after = scene.scene_text.slice(activeWord.end);

  return (
    <>
      {before}
      <mark className="reader-highlight">{active}</mark>
      {after}
    </>
  );
}

function getSceneWordMarks(scene: GeneratedReadingScene) {
  return getRenderableSceneWordMarks(scene);
}

function renderInteractiveSceneText(
  scene: GeneratedReadingScene,
  currentMs: number,
  onWordClick: (startMs: number) => void,
) {
  const wordMarks = getSceneWordMarks(scene);
  if (wordMarks.length === 0) {
    return renderHighlightedSceneText(scene, currentMs);
  }

  const activeWord = resolveActiveWord(scene, currentMs);
  const fragments: ReactNode[] = [];
  let cursor = 0;

  wordMarks.forEach((mark, index) => {
    const { start, end } = getMarkRange(mark);
    const time = typeof mark.time === "number" ? mark.time : 0;

    if (start > cursor) {
      fragments.push(
        <span key={`text-${scene.scene_id}-${index}`}>{scene.scene_text.slice(cursor, start)}</span>,
      );
    }

    const wordText = typeof mark.value === "string" && mark.value.length > 0
      ? mark.value
      : scene.scene_text.slice(start, end);
    const isActive = !!activeWord && activeWord.start === start && activeWord.end === end;
    fragments.push(
      <button
        key={`word-${scene.scene_id}-${index}`}
        type="button"
        className={isActive ? "reader-word-button active" : "reader-word-button"}
        onClick={() => onWordClick(time)}
      >
        {wordText}
      </button>,
    );
    cursor = end;
  });

  if (cursor < scene.scene_text.length) {
    fragments.push(<span key={`text-tail-${scene.scene_id}`}>{scene.scene_text.slice(cursor)}</span>);
  }

  return <>{fragments}</>;
}

export function GeneratedStoryReaderPage() {
  const { readerId, storyId } = useParams();
  const { token } = useAuth();
  const [story, setStory] = useState<GeneratedStoryReadResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [toolError, setToolError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [narrationJob, setNarrationJob] = useState<MediaJobStatus | null>(null);
  const [illustrationJob, setIllustrationJob] = useState<MediaJobStatus | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [narrating, setNarrating] = useState(false);
  const [illustrating, setIllustrating] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const sceneRefs = useRef<Array<HTMLElement | null>>([]);
  const autoplayAcrossScenesRef = useRef(false);
  const pendingPlaybackRef = useRef<{ index: number; startSeconds: number } | null>(null);

  async function loadStory(activeToken: string, activeStoryId: number) {
    const payload = await getGeneratedStoryRead(activeStoryId, activeToken);
    setStory(payload);
    setActiveIndex(0);
  }

  useEffect(() => {
    if (!token || !storyId) {
      return;
    }

    loadStory(token, Number(storyId))
      .catch((err) => setPageError(err instanceof Error ? err.message : "Unable to load the immersive reader."))
      .finally(() => setLoading(false));
  }, [storyId, token]);

  useEffect(() => {
    if (!token || !storyId) {
      return;
    }

    Promise.all([
      getLatestStoryMediaJob(Number(storyId), "narration", token),
      getLatestStoryMediaJob(Number(storyId), "illustration", token),
    ])
      .then(([latestNarrationJob, latestIllustrationJob]) => {
        setNarrationJob(latestNarrationJob);
        setIllustrationJob(latestIllustrationJob);
      })
      .catch((err) => setToolError(err instanceof Error ? err.message : "Unable to load media job status."));
  }, [storyId, token]);

  const activeScene = story?.scenes[activeIndex] ?? null;
  const sceneAudioUrl = activeScene?.audio_url ?? null;
  const currentMs = Math.floor(currentTime * 1000);
  const hasAudio = !!sceneAudioUrl;
  const hasNarration = !!story?.scenes.some((scene) => !!scene.audio_url);
  const storyIllustrationUrl = story?.scenes.find((scene) => !!scene.illustration_url)?.illustration_url ?? null;
  const hasIllustrations = !!storyIllustrationUrl;

  useEffect(() => {
    if (!token || !storyId) {
      return;
    }

    const activeJobs = [narrationJob, illustrationJob].filter(isActiveMediaJob);
    if (activeJobs.length === 0) {
      return;
    }

    let cancelled = false;
    const poll = async () => {
      try {
        const updates = await Promise.all(activeJobs.map((job) => getMediaJob(job.job_id, token)));
        if (cancelled) {
          return;
        }

        const nextNarrationJob = updates.find((job) => job.job_type === "narration") ?? narrationJob;
        const nextIllustrationJob = updates.find((job) => job.job_type === "illustration") ?? illustrationJob;
        setNarrationJob(nextNarrationJob ?? null);
        setIllustrationJob(nextIllustrationJob ?? null);

        const completedJob = updates.find((job) => job.status === "completed");
        if (completedJob) {
          await loadStory(token, Number(storyId));
          if (cancelled) {
            return;
          }
          setToolError(null);
          setNotice(completedJob.job_type === "narration" ? "Narration is ready." : "Illustration is ready.");
        }

        const failedJob = updates.find((job) => job.status === "failed" && job.error_message);
        if (failedJob) {
          setToolError(failedJob.error_message ?? "Media generation failed.");
        }
      } catch (err) {
        if (!cancelled) {
          setToolError(err instanceof Error ? err.message : "Unable to refresh media job status.");
        }
      }
    };

    void poll();
    const intervalId = window.setInterval(() => {
      void poll();
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [illustrationJob, narrationJob, storyId, token]);

  useEffect(() => {
    const activeElement = sceneRefs.current[activeIndex];
    if (!activeElement) {
      return;
    }
    activeElement.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [activeIndex]);

  useEffect(() => {
    if (!audioRef.current) {
      return;
    }

    const audio = audioRef.current;
    audio.volume = volume;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onPause = () => setIsPlaying(false);
    const onPlay = () => setIsPlaying(true);
    const onError = () => setToolError("Audio playback failed for this scene.");
    const onEnded = () => {
      setIsPlaying(false);
      if (!story || activeIndex >= story.scenes.length - 1) {
        autoplayAcrossScenesRef.current = false;
        return;
      }
      if (!autoplayAcrossScenesRef.current) {
        return;
      }

      const nextSceneIndex = story.scenes.findIndex((scene, index) => index > activeIndex && !!scene.audio_url);
      if (nextSceneIndex < 0) {
        autoplayAcrossScenesRef.current = false;
        return;
      }

      pendingPlaybackRef.current = { index: nextSceneIndex, startSeconds: 0 };
      setActiveIndex(nextSceneIndex);
    };

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("error", onError);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("error", onError);
      audio.removeEventListener("ended", onEnded);
    };
  }, [activeIndex, story, volume]);

  useEffect(() => {
    setCurrentTime(0);
    setIsPlaying(false);
  }, [sceneAudioUrl]);

  useEffect(() => {
    if (!audioRef.current || !sceneAudioUrl) {
      return;
    }

    const pendingPlayback = pendingPlaybackRef.current;
    if (!pendingPlayback || pendingPlayback.index !== activeIndex) {
      return;
    }

    const audio = audioRef.current;
    const startPlayback = async () => {
      try {
        audio.currentTime = pendingPlayback.startSeconds;
        await audio.play();
      } catch (err) {
        autoplayAcrossScenesRef.current = false;
        setToolError(err instanceof Error ? err.message : "Audio playback could not start.");
      } finally {
        pendingPlaybackRef.current = null;
      }
    };

    if (audio.readyState >= 1) {
      void startPlayback();
      return;
    }

    const onLoadedMetadata = () => {
      void startPlayback();
    };
    audio.addEventListener("loadedmetadata", onLoadedMetadata, { once: true });
    return () => {
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
    };
  }, [activeIndex, sceneAudioUrl]);

  async function seekAndPlay(index: number, startSeconds: number) {
    const targetScene = story?.scenes[index] ?? null;
    if (!targetScene?.audio_url) {
      return;
    }

    autoplayAcrossScenesRef.current = true;
    setToolError(null);

    if (index !== activeIndex) {
      pendingPlaybackRef.current = { index, startSeconds };
      setActiveIndex(index);
      return;
    }

    if (!audioRef.current) {
      return;
    }

    try {
      audioRef.current.pause();
      audioRef.current.currentTime = startSeconds;
      await audioRef.current.play();
    } catch (err) {
      autoplayAcrossScenesRef.current = false;
      setToolError(err instanceof Error ? err.message : "Audio playback could not start.");
    }
  }

  async function togglePlayback() {
    if (!audioRef.current || !sceneAudioUrl) {
      return;
    }

    try {
      if (audioRef.current.paused) {
        autoplayAcrossScenesRef.current = true;
        await audioRef.current.play();
      } else {
        autoplayAcrossScenesRef.current = false;
        audioRef.current.pause();
      }
    } catch (err) {
      autoplayAcrossScenesRef.current = false;
      setToolError(err instanceof Error ? err.message : "Audio playback could not start.");
    }
  }

  async function playStoryFromBeginning() {
    if (!story) {
      return;
    }

    const firstNarratedSceneIndex = story.scenes.findIndex((scene) => !!scene.audio_url);
    if (firstNarratedSceneIndex < 0) {
      return;
    }

    await seekAndPlay(firstNarratedSceneIndex, 0);
  }

  function goToScene(index: number) {
    setActiveIndex(index);
  }

  async function handleNarrate() {
    if (!token || !storyId) {
      return;
    }

    setNarrating(true);
    setToolError(null);
    setNotice(null);

    try {
      const result = await narrateGeneratedStory(Number(storyId), token);
      setNarrationJob(result);
      if (result.already_ready) {
        await loadStory(token, Number(storyId));
        setNotice("Narration is already ready for this story.");
      } else {
        setNotice(result.status === "processing" ? "Narration is processing." : "Narration queued.");
      }
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to generate narration.");
    } finally {
      setNarrating(false);
    }
  }

  async function handleIllustrate() {
    if (!token || !storyId) {
      return;
    }

    setIllustrating(true);
    setToolError(null);
    setNotice(null);

    try {
      const result = await illustrateGeneratedStory(Number(storyId), token);
      setIllustrationJob(result);
      if (result.already_ready) {
        await loadStory(token, Number(storyId));
        setNotice("Illustration is already ready for this story.");
      } else {
        setNotice(result.status === "processing" ? "Illustration is processing." : "Illustration queued.");
      }
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to generate illustration.");
    } finally {
      setIllustrating(false);
    }
  }

  if (loading) {
    return <LoadingState label="Opening generated immersive reader..." />;
  }

  if (pageError) {
    return <ErrorState message={pageError} />;
  }

  if (!story) {
    return <ErrorState message="Generated story reader is unavailable." />;
  }

  return (
    <section className="reader-experience">
      {notice ? (
        <div className="status-card dashboard-notice-card">
          <h3>Saved</h3>
          <p>{notice}</p>
        </div>
      ) : null}
      {toolError ? (
        <div className="status-card">
          <h3>Media issue</h3>
          <p>{toolError}</p>
        </div>
      ) : null}
      {isActiveMediaJob(narrationJob) || isActiveMediaJob(illustrationJob) ? (
        <div className="status-card dashboard-notice-card">
          <h3>Processing</h3>
          <p>
            {isActiveMediaJob(narrationJob) ? "Narration" : "Illustration"} is running in the background.
            This reader will refresh when it finishes.
          </p>
        </div>
      ) : null}
      <aside className="reader-sidebar">
        <div className="reader-stats">
          <span>Generated story</span>
          {story.trait_focus ? <span>Theme: {story.trait_focus}</span> : null}
          <span>{story.scenes.length} scenes</span>
          <span>{hasAudio ? "Scene audio available" : "Text-first mode"}</span>
        </div>
        <ol className="reader-unit-list">
          {story.scenes.map((scene, index) => (
            <li key={scene.scene_id}>
              <button
                type="button"
                className={index === activeIndex ? "unit-button active" : "unit-button"}
                onClick={() => goToScene(index)}
              >
                <strong>Scene {scene.scene_order ?? index + 1}</strong>
                <span>{scene.scene_text.slice(0, 70)}...</span>
              </button>
            </li>
          ))}
        </ol>
      </aside>

      <div className="reader-stage">
        <div className="reader-stage-header">
          <div>
            <p className="eyebrow">Generated immersive reader</p>
            <h2>{story.title ?? "Untitled story"}</h2>
            <p className="reader-stage-subtitle">
              Scene {activeScene?.scene_order ?? activeIndex + 1}
            </p>
          </div>
          <div className="reader-controls">
            {hasIllustrations ? (
              <span className="chip">Illustration ready</span>
            ) : (
              <button
                type="button"
                className="ghost-button"
                onClick={handleIllustrate}
                disabled={illustrating || isActiveMediaJob(illustrationJob)}
              >
                {illustrating || isActiveMediaJob(illustrationJob) ? "Illustration queued..." : "Generate illustration"}
              </button>
            )}
            {hasNarration ? <span className="chip">Narration ready</span> : (
              <button
                type="button"
                className="ghost-button"
                onClick={handleNarrate}
                disabled={narrating || isActiveMediaJob(narrationJob)}
              >
                {narrating || isActiveMediaJob(narrationJob) ? "Narration queued..." : "Generate narration"}
              </button>
            )}
            <Link to={`/reader/${readerId}/books/${story.story_id}`} className="ghost-button">
              Back to story
            </Link>
          </div>
        </div>

        {hasAudio && activeScene ? (
          <section className="panel reader-media-panel">
            <audio ref={audioRef} src={sceneAudioUrl} preload="metadata" />
            <div className="reader-media-row">
              <button type="button" className="primary-button" onClick={() => void togglePlayback()}>
                {isPlaying ? "Pause" : "Play"}
              </button>
              <button type="button" className="ghost-button" onClick={() => void playStoryFromBeginning()}>
                Play from story beginning
              </button>
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
            </div>
            <p className="reader-audio-tip">Click a word in the active scene to restart from that point.</p>
          </section>
        ) : (
          <section className="panel reader-media-panel">
            <h3>Text-first immersive reading</h3>
            <p>
              This generated story can be read right away. Audio and illustrations can be added later without
              blocking reading.
            </p>
            {!hasNarration ? <p>Use Generate narration when you want scene audio and word highlighting.</p> : null}
            {!hasIllustrations ? <p>Use Generate illustration when you want a story image to appear above the reader.</p> : null}
          </section>
        )}

        {storyIllustrationUrl ? (
          <section className="panel reader-illustration-panel">
            <img className="reader-illustration-image" src={storyIllustrationUrl} alt="" />
          </section>
        ) : null}

        <article className="reader-card story-flow">
          <header className="reader-story-header">
            <p className="eyebrow">Now Reading</p>
            <h3>{story.title ?? "Untitled story"}</h3>
          </header>
          <div className="reader-story-units">
            {story.scenes.map((scene, index) => {
              const paragraphs = scene.scene_text.split(/\n\s*\n/).filter((part) => part.trim());
              return (
                <section
                  key={scene.scene_id}
                  ref={(element) => {
                    sceneRefs.current[index] = element;
                  }}
                  className={index === activeIndex ? "reader-unit-card active" : "reader-unit-card"}
                >
                  <p className="reader-scene-label">Scene {scene.scene_order ?? index + 1}</p>
                  {!hasAudio && paragraphs.length > 1 ? (
                    paragraphs.map((paragraph, paragraphIndex) => (
                      <p key={`${scene.scene_id}-${paragraphIndex}`} className="reader-text">
                        {paragraph}
                      </p>
                    ))
                  ) : (
                    <p className="reader-text">
                      {index === activeIndex && hasAudio
                        ? renderInteractiveSceneText(scene, currentMs, (startMs) => {
                            void seekAndPlay(index, Math.max(0, startMs / 1000));
                          })
                        : scene.scene_text}
                    </p>
                  )}
                </section>
              );
            })}
          </div>
        </article>
      </div>
    </section>
  );
}
