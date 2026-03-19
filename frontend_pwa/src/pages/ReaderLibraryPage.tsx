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

  async function loadBookshelf(activeToken: string, activeReaderId: number) {
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

    loadBookshelf(token, Number(readerId))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the reader bookshelf."))
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
    const previewParts = [
      story.trait_focus ? `Focus: ${story.trait_focus}` : null,
      story.narration_available ? "Narration ready" : "Text-first reading",
      story.artwork_available ? "Artwork ready" : null,
    ].filter((value): value is string => !!value);

    return {
      story_id: story.story_id,
      title: story.title,
      source_author: shelfName,
      age_range: shelfName ? `${shelfName} universe` : "Reader library",
      reading_level: `Version ${story.current_version ?? 1}`,
      preview_text: previewParts.join(" • "),
      cover: {
        mode: "generated-library",
        image_url: story.cover_image_url,
        accent_token: story.artwork_available ? "sunrise" : story.published ? "sunrise" : "lagoon",
        display_title: story.title ?? "Untitled Story",
      },
      immersive_reader_available: true,
      narration_available: story.narration_available,
    };
  }

  function buildReadTo(storyId: number, playlist?: number[], playlistIndex = 0): string {
    const params = new URLSearchParams();
    params.set("autoplay", "1");
    params.set("focus", "now-reading");
    if (playlist && playlist.length > 0) {
      params.set("playlist", playlist.join(","));
      params.set("playlistIndex", String(playlistIndex));
    }
    return `/reader/${library?.reader_id}/books/${storyId}/read?${params.toString()}`;
  }

  return (
    <section className="panel">
      {loading ? <LoadingState label="Opening the reader bookshelf..." /> : null}
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
              <Link to={`/reader/${library.reader_id}`} className="btn btn--secondary btn-tone-neutral ghost-button">
                Reader Home
              </Link>
              <Link to={`/reader/${library.reader_id}/games`} className="btn btn--secondary btn-tone-sky ghost-button">
                Open Game Shelf
              </Link>
              <Link to={`/reader/${library.reader_id}/words`} className="btn btn--secondary btn-tone-sky ghost-button">
                Open Vocabulary Shelf
              </Link>
              <Link to="/classics" className="btn btn--secondary btn-tone-plum ghost-button">
                Browse Classics
              </Link>
            </div>
          </div>

          <ReaderAreaNav readerId={library.reader_id} />

          <div className="library-shelf-grid">
            {readerWorlds.length > 0 ? (
              readerWorlds.map((readerWorld) => {
                const shelfStories = storiesByReaderWorld.get(readerWorld.reader_world_id) ?? [];
                const shelfName = readerWorld.custom_name || readerWorld.world.name || "Unnamed universe shelf";
                const playlist = shelfStories.map((story) => story.story_id);

                return (
                  <article key={readerWorld.reader_world_id} className="panel inset-panel world-shelf-card">
                    <div className="section-heading world-shelf-header">
                      <div>
                        <p className="eyebrow">Universe shelf</p>
                        <h3>{shelfName}</h3>
                        <p>
                          {shelfStories.length > 0
                            ? "Choose a book to open the story details, start reading, or play through the whole shelf."
                            : "This universe is ready for its first book."}
                        </p>
                      </div>
                      <div className="library-action-row">
                        <span className="chip">{shelfStories.length} books</span>
                        {shelfStories.length > 0 ? (
                          <Link className="btn btn--primary btn-tone-gold primary-button" to={buildReadTo(shelfStories[0].story_id, playlist, 0)}>
                            Play all
                          </Link>
                        ) : null}
                        {typeof readerWorld.world_id === "number" ? (
                          <Link className="btn btn--secondary btn-tone-sky ghost-button" to={`/reader/${library.reader_id}/worlds/${readerWorld.world_id}`}>
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
                            readTo={buildReadTo(story.story_id)}
                            authorLabel={null}
                            metaOverride={[
                              story.trait_focus ? `Focus: ${story.trait_focus}` : "StoryBloom book",
                              story.narration_available ? "Narration ready" : "Text-first reading",
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
                    readTo={buildReadTo(story.story_id)}
                    authorLabel={null}
                    metaOverride={[
                      story.trait_focus ? `Focus: ${story.trait_focus}` : "StoryBloom book",
                      story.narration_available ? "Narration ready" : "Text-first reading",
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
