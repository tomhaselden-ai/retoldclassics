import { NavLink } from "react-router-dom";

interface ReaderAreaNavProps {
  readerId: number | string;
}

export function ReaderAreaNav({ readerId }: ReaderAreaNavProps) {
  const base = `/reader/${readerId}`;

  return (
    <nav className="reader-area-nav" aria-label="Reader area">
      <NavLink end to={base} className="reader-area-link">
        Home
      </NavLink>
      <NavLink to={`${base}/books`} className="reader-area-link">
        Books
      </NavLink>
      <NavLink to={`${base}/words`} className="reader-area-link">
        Words
      </NavLink>
      <NavLink to={`${base}/games`} className="reader-area-link">
        Play
      </NavLink>
      <NavLink to={`${base}/goals`} className="reader-area-link">
        Goals
      </NavLink>
    </nav>
  );
}
