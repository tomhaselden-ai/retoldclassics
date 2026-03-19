import { NavLink } from "react-router-dom";

interface ReaderAreaNavProps {
  readerId: number | string;
}

export function ReaderAreaNav({ readerId }: ReaderAreaNavProps) {
  const base = `/reader/${readerId}`;

  return (
    <nav className="reader-area-nav" aria-label="Reader area">
      <NavLink end to={base} className={({ isActive }) => ["reader-area-link", "btn", "btn--nav", "btn-tone-neutral", "btn-size-compact", isActive ? "active" : ""].filter(Boolean).join(" ")}>
        Home
      </NavLink>
      <NavLink to={`${base}/books`} className={({ isActive }) => ["reader-area-link", "btn", "btn--nav", "btn-tone-neutral", "btn-size-compact", isActive ? "active" : ""].filter(Boolean).join(" ")}>
        Books
      </NavLink>
      <NavLink to={`${base}/words`} className={({ isActive }) => ["reader-area-link", "btn", "btn--nav", "btn-tone-neutral", "btn-size-compact", isActive ? "active" : ""].filter(Boolean).join(" ")}>
        Words
      </NavLink>
      <NavLink to={`${base}/games`} className={({ isActive }) => ["reader-area-link", "btn", "btn--nav", "btn-tone-neutral", "btn-size-compact", isActive ? "active" : ""].filter(Boolean).join(" ")}>
        Play
      </NavLink>
      <NavLink to={`${base}/goals`} className={({ isActive }) => ["reader-area-link", "btn", "btn--nav", "btn-tone-neutral", "btn-size-compact", isActive ? "active" : ""].filter(Boolean).join(" ")}>
        Goals
      </NavLink>
    </nav>
  );
}
