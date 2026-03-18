import { Link } from "react-router-dom";

import { PageSeo } from "../components/PageSeo";

export function HowItWorksPage() {
  return (
    <div className="page-grid">
      <PageSeo
        title="How It Works | Persistent Story Universe"
        description="Learn how guest discovery, family setup, reader routes, classics, goals, and immersive story tools work together in Persistent Story Universe."
      />

      <section className="hero-panel growth-hero growth-hero-how">
        <div className="hero-copy">
          <p className="eyebrow">How it works</p>
          <h1>From guest discovery to a living family reading system</h1>
          <p>
            The public funnel is simple on purpose: try the classics, explore a guest game, create an account, then
            move into chooser, parent, and reader spaces built for their different jobs.
          </p>
          <div className="hero-actions">
            <Link to="/games/guest" className="primary-button">
              Try guest games
            </Link>
            <Link to="/register" className="ghost-button">
              Start free
            </Link>
          </div>
        </div>
        <div className="growth-quote-card">
          <p className="eyebrow">Platform shape</p>
          <h3>Guest discovery leads into a family account, then splits cleanly into parent and reader experiences.</h3>
        </div>
      </section>

      <section className="panel">
        <div className="growth-timeline">
          <article className="growth-step">
            <p className="eyebrow">1. Discover</p>
            <h3>Browse classics or try a guest game</h3>
            <p>Guests can sample the platform with bounded access and clear conversion prompts.</p>
          </article>
          <article className="growth-step">
            <p className="eyebrow">2. Set up</p>
            <h3>Create an account and use the chooser</h3>
            <p>The chooser becomes the family’s clean entry point after login.</p>
          </article>
          <article className="growth-step">
            <p className="eyebrow">3. Parent view</p>
            <h3>Manage readers, analytics, and goals</h3>
            <p>Parents get visibility and control without cluttering the child-facing flow.</p>
          </article>
          <article className="growth-step">
            <p className="eyebrow">4. Reader view</p>
            <h3>Read, practice, play, and keep going</h3>
            <p>Children get a calmer route structure centered on books, words, games, and goals.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
