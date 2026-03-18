import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderAreaNav } from "../components/ReaderAreaNav";
import {
  assignWorldToReader,
  generateStoryForReader,
  getReaderLibrary,
  getReaderWorlds,
  getWorlds,
  publishLibraryStory,
  type ReaderLibraryResponse,
  type ReaderWorld,
  type World,
} from "../services/api";
import { useAuth } from "../services/auth";

const TARGET_LENGTH_OPTIONS = [
  { value: "short", label: "Short adventure" },
  { value: "medium", label: "Medium adventure" },
  { value: "long", label: "Long adventure" },
];

export function ReaderLibraryPage() {
  const { readerId } = useParams();
  const { token } = useAuth();
  const [library, setLibrary] = useState<ReaderLibraryResponse | null>(null);
  const [readerWorlds, setReaderWorlds] = useState<ReaderWorld[]>([]);
  const [allWorlds, setAllWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [publishingStoryId, setPublishingStoryId] = useState<number | null>(null);
  const [assigningWorld, setAssigningWorld] = useState(false);
  const [creatingForWorldId, setCreatingForWorldId] = useState<number | null>(null);
  const [activeCreateWorldId, setActiveCreateWorldId] = useState<number | null>(null);
  const [selectedWorldId, setSelectedWorldId] = useState<number | "">("");
  const [customShelfName, setCustomShelfName] = useState("");
  const [createTheme, setCreateTheme] = useState("");
  const [createTargetLength, setCreateTargetLength] = useState("medium");

  async function loadWorkspace(activeToken: string, activeReaderId: number) {
    const [libraryPayload, readerWorldPayload, worldsPayload] = await Promise.all([
      getReaderLibrary(activeReaderId, activeToken),
      getReaderWorlds(activeReaderId, activeToken),
      getWorlds(),
    ]);
    setLibrary(libraryPayload);
    setReaderWorlds(readerWorldPayload);
    setAllWorlds(worldsPayload);
  }

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    loadWorkspace(token, Number(readerId))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the reader library workspace."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

  const availableWorlds = useMemo(() => {
    const assigned = new Set(readerWorlds.map((entry) => entry.world_id).filter((value): value is number => typeof value === "number"));
    return allWorlds.filter((world) => !assigned.has(world.world_id));
  }, [allWorlds, readerWorlds]);

  const storiesByReaderWorld = useMemo(() => {
    const grouped = new Map<number, ReaderLibraryResponse["stories"]>();
    for (const story of library?.stories ?? []) {
      if (typeof story.reader_world_id !== "number") {
        continue;
      }
      const existing = grouped.get(story.reader_world_id) ?? [];
      existing.push(story);
      grouped.set(story.reader_world_id, existing);
    }
    return grouped;
  }, [library?.stories]);

  const unassignedStories = useMemo(
    () => (library?.stories ?? []).filter((story) => typeof story.reader_world_id !== "number"),
    [library?.stories],
  );
  const activeCreatingShelf =
    creatingForWorldId === null
      ? null
      : readerWorlds.find((entry) => entry.world_id === creatingForWorldId) ?? null;

  async function handlePublish(storyId: number) {
    if (!token || !readerId) {
      return;
    }

    setPublishingStoryId(storyId);
    setError(null);
    setNotice(null);

    try {
      await publishLibraryStory(Number(readerId), storyId, token);
      await loadWorkspace(token, Number(readerId));
      setNotice("Story published to EPUB.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to publish the story.");
    } finally {
      setPublishingStoryId(null);
    }
  }

  async function handleAssignWorld(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !readerId || selectedWorldId === "") {
      return;
    }

    setAssigningWorld(true);
    setError(null);
    setNotice(null);

    try {
      await assignWorldToReader(
        Number(readerId),
        {
          world_id: selectedWorldId,
          custom_name: customShelfName.trim() || null,
        },
        token,
      );
      await loadWorkspace(token, Number(readerId));
      setSelectedWorldId("");
      setCustomShelfName("");
      setNotice("World shelf added.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to add the world shelf.");
    } finally {
      setAssigningWorld(false);
    }
  }

  async function handleGenerateStory(event: FormEvent<HTMLFormElement>, worldId: number) {
    event.preventDefault();
    if (!token || !readerId) {
      return;
    }

    setCreatingForWorldId(worldId);
    setError(null);
    setNotice(null);

    try {
      const result = await generateStoryForReader(
        {
          reader_id: Number(readerId),
          world_id: worldId,
          theme: createTheme.trim(),
          target_length: createTargetLength,
        },
        token,
      );
      await loadWorkspace(token, Number(readerId));
      setActiveCreateWorldId(null);
      setCreateTheme("");
      setCreateTargetLength("medium");
      setNotice(`Created "${result.title}".`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create the story.");
    } finally {
      setCreatingForWorldId(null);
    }
  }

  return (
    <section className="panel">
      {loading ? <LoadingState label="Opening the library workspace..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {library ? (
        <>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Reader library</p>
              <h1>{library.reader_name ?? "Reader"}'s world shelves</h1>
              <p>{library.story_count} generated stories are available across this reader's assigned worlds.</p>
            </div>
            <div className="library-action-row">
              <Link to={`/reader/${library.reader_id}`} className="ghost-button">
                Reader home
              </Link>
              <Link to={`/reader/${library.reader_id}/games`} className="ghost-button">
                Open game shelf
              </Link>
              <Link to={`/reader/${library.reader_id}/words`} className="ghost-button">
                Open vocabulary shelf
              </Link>
              <Link to="/classics" className="text-link">
                Visit classics shelf
              </Link>
            </div>
          </div>

          <ReaderAreaNav readerId={library.reader_id} />

          {notice ? (
            <div className="status-card dashboard-notice-card">
              <h3>Saved</h3>
              <p>{notice}</p>
            </div>
          ) : null}

          {activeCreatingShelf ? (
            <div className="status-card dashboard-notice-card">
              <h3>Processing</h3>
              <p>
                Building a new book for {activeCreatingShelf.custom_name || activeCreatingShelf.world.name || "this world"}
                . The shelf will refresh when it is ready.
              </p>
            </div>
          ) : null}

          <section className="panel inset-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">World shelves</p>
                <h2>Add a world to this reader</h2>
                <p>Assigned worlds become shelves where new generated books live.</p>
              </div>
            </div>

            {availableWorlds.length > 0 ? (
              <form className="world-assignment-form" onSubmit={handleAssignWorld}>
                <label className="field">
                  <span>World template</span>
                  <select
                    value={selectedWorldId}
                    onChange={(event) => setSelectedWorldId(event.target.value ? Number(event.target.value) : "")}
                    required
                  >
                    <option value="">Choose a world</option>
                    {availableWorlds.map((world) => (
                      <option key={world.world_id} value={world.world_id}>
                        {world.name ?? `World ${world.world_id}`}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>Custom shelf name</span>
                  <input
                    value={customShelfName}
                    onChange={(event) => setCustomShelfName(event.target.value)}
                    placeholder="Optional custom name"
                  />
                </label>

                <button type="submit" className="primary-button" disabled={assigningWorld || selectedWorldId === ""}>
                  {assigningWorld ? "Adding shelf..." : "Add world shelf"}
                </button>
              </form>
            ) : (
              <div className="status-card">
                <h3>All worlds assigned</h3>
                <p>This reader already has every available world shelf assigned.</p>
              </div>
            )}
          </section>

          <div className="library-shelf-grid">
            {readerWorlds.length > 0 ? (
              readerWorlds.map((readerWorld) => {
                const shelfStories = storiesByReaderWorld.get(readerWorld.reader_world_id) ?? [];
                const shelfName = readerWorld.custom_name || readerWorld.world.name || "Unnamed world shelf";

                return (
                  <article key={readerWorld.reader_world_id} className="panel inset-panel world-shelf-card">
                    <div className="section-heading">
                      <div>
                        <p className="eyebrow">World shelf</p>
                        <h3>{shelfName}</h3>
                        <p>{readerWorld.world.description ?? "No world description available yet."}</p>
                      </div>
                      <span className="chip">{shelfStories.length} stories</span>
                    </div>

                    {activeCreateWorldId === readerWorld.world_id ? (
                      <form className="story-create-form" onSubmit={(event) => void handleGenerateStory(event, readerWorld.world_id ?? 0)}>
                        <label className="field">
                          <span>Theme</span>
                          <input
                            value={createTheme}
                            onChange={(event) => setCreateTheme(event.target.value)}
                            placeholder="friendship, courage, mystery"
                            required
                          />
                        </label>

                        <label className="field">
                          <span>Length</span>
                          <select value={createTargetLength} onChange={(event) => setCreateTargetLength(event.target.value)}>
                            {TARGET_LENGTH_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </label>

                        <div className="library-action-row">
                          <button
                            type="submit"
                            className="primary-button"
                            disabled={
                              creatingForWorldId === (readerWorld.world_id ?? 0) ||
                              typeof readerWorld.world_id !== "number" ||
                              !createTheme.trim()
                            }
                          >
                            {creatingForWorldId === (readerWorld.world_id ?? 0) ? "Processing book..." : "Create book in this world"}
                          </button>
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={() => {
                              setActiveCreateWorldId(null);
                              setCreateTheme("");
                              setCreateTargetLength("medium");
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : (
                      <div className="library-action-row">
                        <button
                          type="button"
                          className="primary-button"
                          onClick={() => {
                            setActiveCreateWorldId(readerWorld.world_id ?? null);
                            setCreateTheme("");
                            setCreateTargetLength("medium");
                          }}
                          disabled={typeof readerWorld.world_id !== "number"}
                        >
                          Create book in this world
                        </button>
                        {typeof readerWorld.world_id === "number" ? (
                          <Link className="ghost-button" to={`/reader/${library.reader_id}/worlds/${readerWorld.world_id}`}>
                            World info
                          </Link>
                        ) : null}
                      </div>
                    )}

                    <div className="library-grid">
                      {shelfStories.length > 0 ? (
                        shelfStories.map((story) => (
                          <article key={story.story_id} className="panel inset-panel">
                            <p className="eyebrow">Generated book</p>
                            <h3>{story.title ?? "Untitled Story"}</h3>
                            <p>Version {story.current_version ?? 1}</p>
                            <p>{story.trait_focus ?? "Trait focus pending"}</p>
                            <div className="library-story-actions">
                              <Link className="primary-button" to={`/reader/${library.reader_id}/books/${story.story_id}/read`}>
                                Open immersive reader
                              </Link>
                              <Link className="ghost-button" to={`/reader/${library.reader_id}/books/${story.story_id}`}>
                                View story
                              </Link>
                              <button
                                type="button"
                                className="primary-button"
                                onClick={() => handlePublish(story.story_id)}
                                disabled={publishingStoryId === story.story_id}
                              >
                                {publishingStoryId === story.story_id
                                  ? "Publishing..."
                                  : story.published
                                    ? "Republish EPUB"
                                    : "Publish EPUB"}
                              </button>
                              {story.epub_url ? (
                                <a className="ghost-button" href={story.epub_url} target="_blank" rel="noreferrer">
                                  Open EPUB
                                </a>
                              ) : (
                                <span className="chip muted">Not published yet</span>
                              )}
                            </div>
                          </article>
                        ))
                      ) : (
                        <div className="status-card">
                          <h3>No books on this shelf yet</h3>
                          <p>Create the first story in this world to place a book on the shelf.</p>
                        </div>
                      )}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="status-card">
                <h3>No world shelves yet</h3>
                <p>Add a world above to start organizing generated books by universe.</p>
              </div>
            )}
          </div>

          {unassignedStories.length > 0 ? (
            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Ungrouped stories</p>
                  <h2>Stories without a visible world shelf</h2>
                </div>
              </div>
              <div className="library-grid">
                {unassignedStories.map((story) => (
                  <article key={story.story_id} className="panel inset-panel">
                    <p className="eyebrow">Generated book</p>
                    <h3>{story.title ?? "Untitled Story"}</h3>
                    <p>{story.trait_focus ?? "Trait focus pending"}</p>
                    <div className="library-story-actions">
                      <Link className="primary-button" to={`/reader/${library.reader_id}/books/${story.story_id}/read`}>
                        Open immersive reader
                      </Link>
                      <Link className="ghost-button" to={`/reader/${library.reader_id}/books/${story.story_id}`}>
                        View story
                      </Link>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
