import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ReaderAreaNav } from "../components/ReaderAreaNav";
import { StoryCard } from "../components/StoryCard";
import {
  getReaderLibrary,
  getReaderWorlds,
  type ReaderLibraryResponse,
  type ReaderWorld,
  type ShelfItem,
} from "../services/api";
import { useAuth } from "../services/auth";

export function ReaderLibraryPage() {
  const { readerId } = useParams();
  const { token } = useAuth();
  const [library, setLibrary] = useState<ReaderLibraryResponse | null>(null);
  const [readerWorlds, setReaderWorlds] = useState<ReaderWorld[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadWorkspace(activeToken: string, activeReaderId: number) {
    const [libraryPayload, readerWorldPayload] = await Promise.all([
      getReaderLibrary(activeReaderId, activeToken),
      getReaderWorlds(activeReaderId, activeToken),
    ]);
    setLibrary(libraryPayload);
    setReaderWorlds(readerWorldPayload);
  }

  useEffect(() => {
    if (!token || !readerId) {
      return;
    }

    loadWorkspace(token, Number(readerId))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the reader library workspace."))
      .finally(() => setLoading(false));
  }, [readerId, token]);

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

  function buildGeneratedStoryItem(
    story: ReaderLibraryResponse["stories"][number],
    shelfName: string | null,
  ): ShelfItem {
    const previewParts = [story.trait_focus ? `Focus: ${story.trait_focus}` : null, `Version ${story.current_version ?? 1}`].filter(
      (value): value is string => !!value,
    );

    return {
      story_id: story.story_id,
      title: story.title,
      source_author: shelfName,
      age_range: shelfName ? `${shelfName} universe` : "Reader library",
      reading_level: story.published ? "EPUB ready" : "Read in StoryBloom",
      preview_text: previewParts.join(" • "),
      cover: {
        mode: "generated-library",
        image_url: null,
        accent_token: story.published ? "sunrise" : "lagoon",
        display_title: story.title ?? "Untitled Story",
      },
      immersive_reader_available: true,
      narration_available: false,
    };
  }

  return (
    <section className="panel">
      {loading ? <LoadingState label="Opening the library workspace..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {library ? (
        <>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Reader bookshelf</p>
              <h1>{library.reader_name ?? "Reader"}'s books</h1>
              <p>{library.story_count} books are ready across this reader's universes.</p>
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

          <div className="library-shelf-grid">
            {readerWorlds.length > 0 ? (
              readerWorlds.map((readerWorld) => {
                const shelfStories = storiesByReaderWorld.get(readerWorld.reader_world_id) ?? [];
                const shelfName = readerWorld.custom_name || readerWorld.world.name || "Unnamed world shelf";

                return (
                  <article key={readerWorld.reader_world_id} className="panel inset-panel world-shelf-card">
                    <div className="section-heading world-shelf-header">
                      <div>
                        <p className="eyebrow">Universe shelf</p>
                        <h3>{shelfName}</h3>
                        <p>{shelfStories.length > 0 ? "Choose a book to open the story details or start reading." : "This universe is ready for its first book."}</p>
                      </div>
                      <div className="library-action-row">
                        <span className="chip">{shelfStories.length} books</span>
                        {typeof readerWorld.world_id === "number" ? (
                          <Link className="ghost-button" to={`/reader/${library.reader_id}/worlds/${readerWorld.world_id}`}>
                            Info
                          </Link>
                        ) : null}
                      </div>
                    </div>

                    <div className="library-grid">
                      {shelfStories.length > 0 ? (
                        shelfStories.map((story) => (
                          <StoryCard
                            key={story.story_id}
                            item={buildGeneratedStoryItem(story, shelfName)}
                            infoLabel="Story info"
                            infoTo={`/reader/${library.reader_id}/books/${story.story_id}`}
                            readTo={`/reader/${library.reader_id}/books/${story.story_id}/read`}
                            authorLabel={null}
                            metaOverride={[
                              story.trait_focus ? `Focus: ${story.trait_focus}` : "StoryBloom book",
                              `Version ${story.current_version ?? 1}`,
                            ]}
                          />
                        ))
                      ) : (
                        <div className="status-card library-empty-card">
                          <h3>No books on this shelf yet</h3>
                          <p>This universe is ready. When a new story is added, it will appear here like the other books.</p>
                        </div>
                      )}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="status-card">
                <h3>No universe shelves yet</h3>
                <p>This reader does not have any universe shelves available yet.</p>
              </div>
            )}
          </div>

          {unassignedStories.length > 0 ? (
            <section className="panel inset-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Library shelf</p>
                  <h2>Books without a universe shelf</h2>
                  <p>These books are still ready to open with the same familiar controls.</p>
                </div>
              </div>
              <div className="library-grid">
                {unassignedStories.map((story) => (
                  <StoryCard
                    key={story.story_id}
                    item={buildGeneratedStoryItem(story, null)}
                    infoLabel="Story info"
                    infoTo={`/reader/${library.reader_id}/books/${story.story_id}`}
                    readTo={`/reader/${library.reader_id}/books/${story.story_id}/read`}
                    authorLabel={null}
                    metaOverride={[
                      story.trait_focus ? `Focus: ${story.trait_focus}` : "StoryBloom book",
                      `Version ${story.current_version ?? 1}`,
                    ]}
                  />
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
