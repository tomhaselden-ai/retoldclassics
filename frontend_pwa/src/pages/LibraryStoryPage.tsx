import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  checkReaderWorldStoryContinuity,
  checkTextSafety,
  getLatestStoryMediaJob,
  getMediaJob,
  getGeneratedStoryIllustrations,
  getGeneratedStoryNarration,
  getStoryMemory,
  getStorySafetyReport,
  illustrateGeneratedStory,
  getLibraryStoryDetail,
  narrateGeneratedStory,
  publishLibraryStory,
  type ContinuityResponse,
  type MediaJobStatus,
  type SceneIllustrationMetadata,
  type LibraryStoryDetailResponse,
  type SafetyEvaluationResponse,
  type StoryMemoryEvent,
  type StorySafetyReportResponse,
} from "../services/api";
import { useAuth } from "../services/auth";

function isActiveMediaJob(job: MediaJobStatus | null): job is MediaJobStatus {
  return job?.status === "pending" || job?.status === "processing";
}

export function LibraryStoryPage() {
  const { readerId, storyId } = useParams();
  const { token } = useAuth();
  const [detail, setDetail] = useState<LibraryStoryDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [narrating, setNarrating] = useState(false);
  const [illustrating, setIllustrating] = useState(false);
  const [hasNarration, setHasNarration] = useState(false);
  const [illustrations, setIllustrations] = useState<SceneIllustrationMetadata[]>([]);
  const [narrationJob, setNarrationJob] = useState<MediaJobStatus | null>(null);
  const [illustrationJob, setIllustrationJob] = useState<MediaJobStatus | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [toolError, setToolError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [storyMemory, setStoryMemory] = useState<StoryMemoryEvent[] | null>(null);
  const [storySafety, setStorySafety] = useState<StorySafetyReportResponse | null>(null);
  const [textSafety, setTextSafety] = useState<SafetyEvaluationResponse | null>(null);
  const [storyContinuity, setStoryContinuity] = useState<ContinuityResponse | null>(null);
  const [loadingMemory, setLoadingMemory] = useState(false);
  const [loadingSafety, setLoadingSafety] = useState(false);
  const [checkingTextSafety, setCheckingTextSafety] = useState(false);
  const [checkingContinuity, setCheckingContinuity] = useState(false);
  const [textSafetyInput, setTextSafetyInput] = useState("");
  const [continuitySummary, setContinuitySummary] = useState("");

  useEffect(() => {
    if (!token || !readerId || !storyId) {
      return;
    }

    Promise.all([
      getLibraryStoryDetail(Number(readerId), Number(storyId), token),
      getGeneratedStoryNarration(Number(storyId), token),
      getGeneratedStoryIllustrations(Number(storyId), token),
      getLatestStoryMediaJob(Number(storyId), "narration", token),
      getLatestStoryMediaJob(Number(storyId), "illustration", token),
    ])
      .then(([detailPayload, narrationPayload, illustrationPayload, latestNarrationJob, latestIllustrationJob]) => {
        setDetail(detailPayload);
        setHasNarration(narrationPayload.some((item) => !!item.audio_url));
        setIllustrations(illustrationPayload);
        setNarrationJob(latestNarrationJob);
        setIllustrationJob(latestIllustrationJob);
      })
      .catch((err) => setPageError(err instanceof Error ? err.message : "Unable to load story details."))
      .finally(() => setLoading(false));
  }, [readerId, storyId, token]);

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
          const [narrationPayload, illustrationPayload] = await Promise.all([
            getGeneratedStoryNarration(Number(storyId), token),
            getGeneratedStoryIllustrations(Number(storyId), token),
          ]);
          if (cancelled) {
            return;
          }
          setHasNarration(narrationPayload.some((item) => !!item.audio_url));
          setIllustrations(illustrationPayload);
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

  const illustratedScenes = illustrations.filter((item) => !!item.image_url);
  const firstIllustrationUrl = illustratedScenes[0]?.image_url ?? null;
  const hasIllustrations = illustratedScenes.length > 0;

  async function handlePublish() {
    if (!token || !readerId || !storyId) {
      return;
    }

    setPublishing(true);
    setToolError(null);
    setNotice(null);

    try {
      const result = await publishLibraryStory(Number(readerId), Number(storyId), token);
      setDetail((current) => (current ? { ...current, story: result.story } : current));
      setNotice("Story published to EPUB.");
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to publish the story.");
    } finally {
      setPublishing(false);
    }
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
        const narrationPayload = await getGeneratedStoryNarration(Number(storyId), token);
        setHasNarration(narrationPayload.some((item) => !!item.audio_url));
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
        const illustrationPayload = await getGeneratedStoryIllustrations(Number(storyId), token);
        setIllustrations(illustrationPayload);
        setNotice("Illustration is already ready for this story.");
      } else {
        setNotice(result.status === "processing" ? "Illustration is processing." : "Illustration queued.");
      }
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to generate illustrations.");
    } finally {
      setIllustrating(false);
    }
  }

  async function handleLoadStoryMemory() {
    if (!storyId) {
      return;
    }

    setLoadingMemory(true);
    setToolError(null);
    try {
      const payload = await getStoryMemory(Number(storyId), token);
      setStoryMemory(payload);
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to load story memory.");
    } finally {
      setLoadingMemory(false);
    }
  }

  async function handleLoadStorySafety() {
    if (!token || !storyId) {
      return;
    }

    setLoadingSafety(true);
    setToolError(null);
    try {
      const payload = await getStorySafetyReport(Number(storyId), token);
      setStorySafety(payload);
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to load story safety report.");
    } finally {
      setLoadingSafety(false);
    }
  }

  async function handleCheckTextSafety(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !textSafetyInput.trim()) {
      return;
    }

    setCheckingTextSafety(true);
    setToolError(null);
    try {
      const payload = await checkTextSafety(textSafetyInput.trim(), token);
      setTextSafety(payload);
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to check text safety.");
    } finally {
      setCheckingTextSafety(false);
    }
  }

  async function handleCheckContinuity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !readerId || !storyId || !detail?.story.world_id || !continuitySummary.trim()) {
      return;
    }

    setCheckingContinuity(true);
    setToolError(null);
    try {
      const payload = await checkReaderWorldStoryContinuity(
        Number(readerId),
        detail.story.world_id,
        Number(storyId),
        continuitySummary.trim(),
        token,
      );
      setStoryContinuity(payload);
    } catch (err) {
      setToolError(err instanceof Error ? err.message : "Unable to run story continuity check.");
    } finally {
      setCheckingContinuity(false);
    }
  }

  return (
    <section className="panel">
      {loading ? <LoadingState label="Opening story details..." /> : null}
      {pageError ? <ErrorState message={pageError} /> : null}

      {detail ? (
        <>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Story info</p>
              <h1>{detail.story.title ?? "Untitled Story"}</h1>
              <p>
                Reader: <strong>{detail.reader_name ?? "Reader"}</strong>
              </p>
            </div>
            <Link to={`/reader/${detail.reader_id}/books`} className="text-link">
              Back to bookshelf
            </Link>
          </div>

          {notice ? (
            <div className="status-card dashboard-notice-card">
              <h3>Saved</h3>
              <p>{notice}</p>
            </div>
          ) : null}

          {toolError ? (
            <div className="status-card">
              <h3>Tooling issue</h3>
              <p>{toolError}</p>
            </div>
          ) : null}

          {isActiveMediaJob(narrationJob) || isActiveMediaJob(illustrationJob) ? (
            <div className="status-card dashboard-notice-card">
              <h3>Processing</h3>
              <p>
                {isActiveMediaJob(narrationJob) ? "Narration" : "Illustration"} is running in the background.
                This page will update automatically when it finishes.
              </p>
            </div>
          ) : null}

          <div className="detail-grid">
            <article className="panel inset-panel">
              <p className="eyebrow">Universe</p>
              <h3>{detail.story.world_name ?? detail.story.custom_world_name ?? "Universe in progress"}</h3>
              <p>{detail.story.reader_world_id ? `Shelf ID ${detail.story.reader_world_id}` : "Shelf placement is still being prepared."}</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Book version</p>
              <h3>Version {detail.story.current_version ?? 1}</h3>
              <p>{detail.story.trait_focus ? `Trait focus: ${detail.story.trait_focus}` : "Trait focus will appear here when it is ready."}</p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Book file</p>
              <h3>{detail.story.published ? "Book file ready" : "Book file not published yet"}</h3>
              <p>
                {detail.story.epub_created_at
                  ? `EPUB created at ${detail.story.epub_created_at}`
                  : "A downloadable book file can be published when needed."}
              </p>
            </article>
            <article className="panel inset-panel">
              <p className="eyebrow">Story art</p>
              <h3>{hasIllustrations ? "Artwork ready" : "Artwork not added yet"}</h3>
              <p>
                {hasIllustrations
                  ? "A story image is ready for immersive reading."
                  : "Artwork can be added to the book when it is ready."}
              </p>
            </article>
          </div>

          <div className="library-action-row">
            <Link
              to={`/reader/${detail.reader_id}/books/${detail.story.story_id}/read?autoplay=1&focus=now-reading`}
              className="primary-button"
            >
              Read
            </Link>
            {hasIllustrations ? (
              <span className="chip">Artwork ready</span>
            ) : (
              <button
                type="button"
                className="ghost-button"
                onClick={handleIllustrate}
                disabled={illustrating || isActiveMediaJob(illustrationJob)}
              >
                {illustrating || isActiveMediaJob(illustrationJob) ? "Artwork queued..." : "Add artwork"}
              </button>
            )}
            {hasNarration ? (
              <span className="chip">Narration ready</span>
            ) : (
              <button
                type="button"
                className="ghost-button"
                onClick={handleNarrate}
                disabled={narrating || isActiveMediaJob(narrationJob)}
              >
                {narrating || isActiveMediaJob(narrationJob) ? "Narration queued..." : "Add narration"}
              </button>
            )}
            <button type="button" className="primary-button" onClick={handlePublish} disabled={publishing}>
              {publishing ? "Publishing..." : detail.story.published ? "Republish book file" : "Publish book file"}
            </button>
            {detail.story.epub_url ? (
              <a className="ghost-button" href={detail.story.epub_url} target="_blank" rel="noreferrer">
                Open book file
              </a>
            ) : null}
          </div>

          <section className="panel inset-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Reading choices</p>
                <h2>Choose how to open this book</h2>
                <p>Use Read to start immersive reading right away, or stay here to look over the book details.</p>
              </div>
            </div>
          </section>

          {hasIllustrations ? (
            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Artwork preview</p>
                  <h2>Story artwork</h2>
                </div>
              </div>

              {firstIllustrationUrl ? (
                <img className="story-detail-image" src={firstIllustrationUrl} alt="" />
              ) : null}
              <p>
                The reader now uses the first available generated image as the primary story illustration.
              </p>
            </section>
          ) : null}

          <div className="tooling-grid">
            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Story tools</p>
                  <h2>Story memory</h2>
                  <p>Load the stored memory events behind this book.</p>
                </div>
                <button type="button" className="ghost-button" onClick={handleLoadStoryMemory} disabled={loadingMemory}>
                  {loadingMemory ? "Loading memory..." : "Load story memory"}
                </button>
              </div>
              <div className="tooling-list">
                {storyMemory ? (
                  storyMemory.length > 0 ? (
                    storyMemory.map((event) => (
                      <article key={event.event_id} className="panel inset-panel tooling-card">
                        <h3>Event {event.event_id}</h3>
                        <p>{event.event_summary ?? "No summary available."}</p>
                        {event.location_id ? <p>Location ID: {event.location_id}</p> : null}
                        {event.characters?.length ? <p>Characters: {event.characters.join(", ")}</p> : null}
                      </article>
                    ))
                  ) : (
                    <div className="status-card">
                      <h3>No memory events</h3>
                      <p>This story does not currently have stored event memory.</p>
                    </div>
                  )
                ) : (
                  <div className="status-card">
                    <h3>Memory not loaded</h3>
                    <p>Use the button above to inspect stored story events.</p>
                  </div>
                )}
              </div>
            </section>

            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Story tools</p>
                  <h2>Story safety report</h2>
                  <p>Inspect this book against the current account safety policy.</p>
                </div>
                <button type="button" className="ghost-button" onClick={handleLoadStorySafety} disabled={loadingSafety}>
                  {loadingSafety ? "Loading safety..." : "Load safety report"}
                </button>
              </div>
              {storySafety ? (
                <div className="tooling-stack">
                  <div className="detail-grid">
                    <article className="panel inset-panel">
                      <p className="eyebrow">Classification</p>
                      <h3>{storySafety.classification}</h3>
                      <p>Safety score {storySafety.safety_score}</p>
                    </article>
                    <article className="panel inset-panel">
                      <p className="eyebrow">Flags</p>
                      <h3>{storySafety.flags.length}</h3>
                      <p>{storySafety.flags.join(", ") || "No safety flags."}</p>
                    </article>
                  </div>
                  <div className="tooling-list">
                    {storySafety.scenes.map((scene) => (
                      <article key={scene.scene_id} className="panel inset-panel tooling-card">
                        <h3>Scene {scene.scene_order ?? scene.scene_id}</h3>
                        <p>{scene.classification} - score {scene.safety_score}</p>
                        <p>{scene.scene_text}</p>
                      </article>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="status-card">
                  <h3>Safety not loaded</h3>
                  <p>Use the button above to inspect the full story safety report.</p>
                </div>
              )}
            </section>
          </div>

          <div className="tooling-grid">
            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Story tools</p>
                  <h2>Check custom text</h2>
                  <p>Run the platform safety evaluator against any text excerpt or proposed edit.</p>
                </div>
              </div>
              <form className="world-assignment-form" onSubmit={handleCheckTextSafety}>
                <label className="field">
                  <span>Text to evaluate</span>
                  <textarea
                    className="tooling-textarea"
                    value={textSafetyInput}
                    onChange={(event) => setTextSafetyInput(event.target.value)}
                    placeholder="Paste text to check against the current story security policy."
                  />
                </label>
                <button type="submit" className="primary-button" disabled={checkingTextSafety || !textSafetyInput.trim()}>
                  {checkingTextSafety ? "Checking safety..." : "Run text safety check"}
                </button>
              </form>
              {textSafety ? (
                <div className="tooling-result-card">
                  <h3>{textSafety.classification}</h3>
                  <p>Safety score {textSafety.safety_score}</p>
                  <p>{textSafety.flags.join(", ") || "No safety flags."}</p>
                </div>
              ) : null}
            </section>

            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Story tools</p>
                  <h2>Story continuity check</h2>
                  <p>Provide a short story summary or planned revision to check against the current world memory.</p>
                </div>
              </div>
              <form className="world-assignment-form" onSubmit={handleCheckContinuity}>
                <label className="field">
                  <span>Story summary</span>
                  <textarea
                    className="tooling-textarea"
                    value={continuitySummary}
                    onChange={(event) => setContinuitySummary(event.target.value)}
                    placeholder="Summarize the story or describe the revision you want to validate."
                  />
                </label>
                <button
                  type="submit"
                  className="primary-button"
                  disabled={checkingContinuity || !continuitySummary.trim() || !detail.story.world_id}
                >
                  {checkingContinuity ? "Checking continuity..." : "Run story continuity check"}
                </button>
              </form>
              {storyContinuity ? (
                <div className="tooling-result-card">
                  <h3>{storyContinuity.continuity_valid ? "Continuity valid" : "Continuity conflicts found"}</h3>
                  {storyContinuity.conflicts.length > 0 ? (
                    <ul className="tooling-conflict-list">
                      {storyContinuity.conflicts.map((conflict) => (
                        <li key={conflict}>{conflict}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No continuity conflicts were detected.</p>
                  )}
                </div>
              ) : null}
            </section>
          </div>
        </>
      ) : null}
    </section>
  );
}
