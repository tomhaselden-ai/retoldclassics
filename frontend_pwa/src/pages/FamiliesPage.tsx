import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";

export function FamiliesPage() {
  return (
    <div className="page-grid">
      <PageSeo
        title="For Families | StoryBloom"
        description="See how StoryBloom supports parents and readers with clear family tools, child-friendly reading spaces, and steady reading growth."
      />

      <section className="hero-panel growth-hero growth-hero-families">
        <div className="hero-copy">
          <p className="eyebrow">For families</p>
          <h1>A family reading platform that respects both the grown-up and the young reader</h1>
          <p>
            Parents need confidence. Children need warmth and clarity. StoryBloom is designed so both can feel at home
            without competing for the same screen.
          </p>
          <div className="hero-actions">
            <StoryBloomActionButton to="/register" family="create" shape="sun" tone="mint" icon="✨">
              Create Account
            </StoryBloomActionButton>
            <StoryBloomActionButton to="/classics" family="secondary" shape="diamond" tone="sky" icon="🧭">
              Browse Classics
            </StoryBloomActionButton>
          </div>
        </div>
        <div className="growth-quote-card">
          <p className="eyebrow">What this means day to day</p>
          <h3>A welcoming reader space, clear parent visibility, and reading routines that can keep growing.</h3>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Parent confidence</p>
            <h2>What parents can actually see and guide</h2>
          </div>
        </div>
        <div className="growth-grid">
          <article className="panel inset-panel">
            <h3>Reader goals</h3>
            <p>Set practical goals for reading, words, and play without making reading time feel like homework.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Analytics that make sense</h3>
            <p>See stories read, words practiced, strengths, and support areas in a parent-friendly format.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Protected parent layer</h3>
            <p>Parent tools stay separate, with a PIN-gated layer that helps keep the child experience simple.</p>
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
            <p>A child-first home keeps the next book, the next word, and the next game close at hand.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Immersive reading</h3>
            <p>Classics and generated stories support narration, highlighting, and guided reading moments.</p>
          </article>
          <article className="panel inset-panel">
            <h3>Room to grow</h3>
            <p>Readers can move from free classics into personalized stories, favorite worlds, and guided goals.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
