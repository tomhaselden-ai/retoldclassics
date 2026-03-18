import { Link } from "react-router-dom";

import type { ShelfItem } from "../services/api";

const ACCENT_CLASS_MAP: Record<string, string> = {
  aurora: "accent-aurora",
  comet: "accent-comet",
  sunrise: "accent-sunrise",
  lagoon: "accent-lagoon",
};

export function StoryCard({ item }: { item: ShelfItem }) {
  const accentClass = ACCENT_CLASS_MAP[item.cover.accent_token ?? ""] ?? "accent-default";

  return (
    <article className={`story-card ${accentClass}`}>
      <div className="story-cover">
        {item.cover.image_url ? (
          <img
            src={item.cover.image_url}
            alt={item.cover.display_title ?? item.title ?? "Classic story illustration"}
            className="story-cover-image"
          />
        ) : null}
        <span className="story-author">{item.source_author}</span>
        <h3>{item.cover.display_title ?? item.title ?? "Untitled Story"}</h3>
      </div>
      <div className="story-card-body">
        <div className="meta-row">
          {item.age_range ? <span>{item.age_range}</span> : null}
          {item.reading_level ? <span>{item.reading_level}</span> : null}
        </div>
        <p>{item.preview_text}</p>
        <Link to={`/classics/${item.story_id}`} className="primary-link">
          Explore story
        </Link>
      </div>
    </article>
  );
}
