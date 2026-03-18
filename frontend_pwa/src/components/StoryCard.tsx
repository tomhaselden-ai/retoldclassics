import { Link } from "react-router-dom";

import type { ShelfItem } from "../services/api";

const ACCENT_CLASS_MAP: Record<string, string> = {
  aurora: "accent-aurora",
  comet: "accent-comet",
  sunrise: "accent-sunrise",
  lagoon: "accent-lagoon",
};

interface StoryCardProps {
  item: ShelfItem;
  infoLabel?: string;
  infoTo?: string;
  readTo?: string | null;
  authorLabel?: string | null;
  metaOverride?: string[];
}

export function StoryCard({
  item,
  infoLabel = "Story info",
  infoTo,
  readTo = null,
  authorLabel,
  metaOverride,
}: StoryCardProps) {
  const accentClass = ACCENT_CLASS_MAP[item.cover.accent_token ?? ""] ?? "accent-default";
  const resolvedInfoTo = infoTo ?? `/classics/${item.story_id}`;
  const resolvedAuthorLabel = authorLabel ?? item.source_author;
  const resolvedMeta = metaOverride ?? [item.age_range, item.reading_level].filter((value): value is string => !!value);

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
        {resolvedAuthorLabel ? <span className="story-author">{resolvedAuthorLabel}</span> : null}
        <h3>{item.cover.display_title ?? item.title ?? "Untitled Story"}</h3>
      </div>
      <div className="story-card-body">
        {resolvedMeta.length > 0 ? <div className="meta-row">{resolvedMeta.map((value) => <span key={value}>{value}</span>)}</div> : null}
        <p>{item.preview_text}</p>
        <div className="story-card-actions">
          <Link to={resolvedInfoTo} className={readTo ? "ghost-button" : "primary-link"}>
            {infoLabel}
          </Link>
          {readTo ? (
            <Link to={readTo} className="primary-link">
              Read
            </Link>
          ) : null}
        </div>
      </div>
    </article>
  );
}
