import { Link } from "react-router-dom";

type RouteScaffoldAction = {
  label: string;
  to: string;
  variant?: "primary" | "ghost" | "text";
};

interface RouteScaffoldPageProps {
  eyebrow: string;
  title: string;
  message: string;
  actions: RouteScaffoldAction[];
  notes?: string[];
}

function actionClassName(variant: RouteScaffoldAction["variant"]): string {
  if (variant === "primary") {
    return "btn btn--primary btn-tone-gold primary-button";
  }
  if (variant === "text") {
    return "btn btn--secondary btn-tone-plum ghost-button";
  }
  return "btn btn--secondary btn-tone-sky ghost-button";
}

export function RouteScaffoldPage({
  eyebrow,
  title,
  message,
  actions,
  notes,
}: RouteScaffoldPageProps) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{message}</p>
        </div>
        <div className="library-action-row">
          {actions.map((action) => (
            <Link key={`${action.to}-${action.label}`} to={action.to} className={actionClassName(action.variant)}>
              {action.label}
            </Link>
          ))}
        </div>
      </div>

      {notes?.length ? (
        <div className="detail-grid">
          {notes.map((note, index) => (
            <article key={`${index}-${note}`} className="panel inset-panel">
              <p className="eyebrow">Phase 1 scaffold</p>
              <p>{note}</p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
