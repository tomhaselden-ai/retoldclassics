import { PageSeo } from "../components/PageSeo";
import { StoryBloomActionButton } from "../components/StoryBloomActionButton";

export function HowItWorksPage() {
  return (
    <div className="page-grid">
      <PageSeo
        title="How It Works | StoryBloom"
        description="Learn how StoryBloom guides families from free discovery into a clear parent space and a child-friendly reading path."
      />

      <section className="hero-panel growth-hero growth-hero-how">
        <div className="hero-copy">
          <p className="eyebrow">How it works</p>
          <h1>From a free first story to a full family reading rhythm</h1>
          <p>
            StoryBloom keeps the first steps simple: explore a classic, try a game, create an account, then move into
            family, parent, and reader spaces built for their different jobs.
          </p>
          <div className="hero-actions">
            <StoryBloomActionButton to="/games/guest" family="secondary" shape="diamond" tone="sky" icon="🎮">
              Try guest games
            </StoryBloomActionButton>
            <StoryBloomActionButton to="/register" family="primary" shape="star" tone="gold" icon="✨">
              Start free
            </StoryBloomActionButton>
          </div>
        </div>
        <div className="growth-quote-card">
          <p className="eyebrow">Platform shape</p>
          <h3>Free discovery leads into a family account, then opens clear parent and reader experiences.</h3>
        </div>
      </section>

      <section className="panel">
        <div className="growth-timeline">
          <article className="growth-step">
            <p className="eyebrow">1. Discover</p>
            <h3>Browse classics or try a free game</h3>
            <p>Families can sample StoryBloom with bounded access and a clear, low-pressure first step.</p>
          </article>
          <article className="growth-step">
            <p className="eyebrow">2. Set up</p>
            <h3>Create an account and use the chooser</h3>
            <p>The chooser becomes the family's simple entry point after login.</p>
          </article>
          <article className="growth-step">
            <p className="eyebrow">3. Parent view</p>
            <h3>Manage readers, analytics, and goals</h3>
            <p>Parents get visibility and guidance without crowding the child-facing flow.</p>
          </article>
          <article className="growth-step">
            <p className="eyebrow">4. Reader view</p>
            <h3>Read, practice, play, and keep going</h3>
            <p>Children get a welcoming route centered on books, words, games, and goals.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
