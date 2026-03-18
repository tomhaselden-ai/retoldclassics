import { Link } from "react-router-dom";

import { PageSeo } from "../components/PageSeo";

export function FamiliesPage() {
  return (
    <div className="page-grid">
      <PageSeo
        title="For Families | Persistent Story Universe"
        description="See how Persistent Story Universe supports parents, readers, classics discovery, and personalized story growth in one calm reading platform."
      />

      <section className="hero-panel growth-hero growth-hero-families">
        <div className="hero-copy">
          <p className="eyebrow">For families</p>
          <h1>A reading platform built for both the grown-up and the young reader</h1>
          <p>
            Parents need visibility. Children need delight and simplicity. Persistent Story Universe is designed so both
            sides can succeed without fighting the interface.
          </p>
          <div className="hero-actions">
            <Link to="/register" className="primary-button">
              Create free account
            </Link>
            <Link to="/classics" className="ghost-button">
              Browse classics
            </Link>
          </div>
        </div>
        <div className="growth-quote-card">
          <p className="eyebrow">What this means in practice</p>
          <h3>Calm child UX, clear parent visibility, and a real reading journey that can keep growing.</h3>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent confidence</p>
            <h2>What parents can actually see and control</h2>
          </div>
        </div>
        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Reader goals</h3>
            <p>Set practical reading, vocabulary, and game goals without turning the platform into homework software.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Analytics that make sense</h3>
            <p>See stories read, words mastered, strengths, and focus areas in a parent-legible format.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Protected parent layer</h3>
            <p>Parent routes stay distinct, with a PIN-gated layer designed to keep child navigation simple.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Reader experience</p>
            <h2>What children get</h2>
          </div>
        </div>
        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Continue reading quickly</h3>
            <p>A child-first home keeps the next book, the next word, and the next game easy to reach.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Immersive reading</h3>
            <p>Classics and generated stories support audio, highlighting, and guided reading interactions.</p>
          </article>
          <article className="panel inset-panel">
            <h3>A platform that grows</h3>
            <p>Readers can move from guest classics to personalized stories, worlds, and guided goals.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
