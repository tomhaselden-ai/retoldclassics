import type { ReactNode } from "react";
import { Navigate, NavLink, Route, Routes, useLocation, useParams } from "react-router-dom";

import { ProtectedRoute } from "./routes/ProtectedRoute";
import { ParentProtectedRoute } from "./routes/ParentProtectedRoute";
import { SiteFooter } from "./components/SiteFooter";
import { useAuth } from "./services/auth";
import { ClassicReaderPage } from "./pages/ClassicReaderPage";
import { ClassicStoryDetailPage } from "./pages/ClassicStoryDetailPage";
import { ClassicsShelfPage } from "./pages/ClassicsShelfPage";
import { BlogIndexPage } from "./pages/BlogIndexPage";
import { BlogPostPage } from "./pages/BlogPostPage";
import { ChooserPage } from "./pages/ChooserPage";
import { ContactPage } from "./pages/ContactPage";
import { DashboardPage } from "./pages/DashboardPage";
import { GeneratedStoryReaderPage } from "./pages/GeneratedStoryReaderPage";
import { GameShelfPage } from "./pages/GameShelfPage";
import { GuestGamesPage } from "./pages/GuestGamesPage";
import { HomePage } from "./pages/HomePage";
import { HowItWorksPage } from "./pages/HowItWorksPage";
import { LoginPage } from "./pages/LoginPage";
import { LibraryStoryPage } from "./pages/LibraryStoryPage";
import { FamiliesPage } from "./pages/FamiliesPage";
import { ParentAnalyticsPage } from "./pages/ParentAnalyticsPage";
import { ParentAreaPage } from "./pages/ParentAreaPage";
import { ParentCharacterCanonPage } from "./pages/ParentCharacterCanonPage";
import { ParentContentPage } from "./pages/ParentContentPage";
import { ParentGoalsPage } from "./pages/ParentGoalsPage";
import { ParentPinPage } from "./pages/ParentPinPage";
import { ParentReaderPage } from "./pages/ParentReaderPage";
import { PasswordResetConfirmPage } from "./pages/PasswordResetConfirmPage";
import { PasswordResetRequestPage } from "./pages/PasswordResetRequestPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReaderGoalsPage } from "./pages/ReaderGoalsPage";
import { ReaderHomePage } from "./pages/ReaderHomePage";
import { ReaderLibraryPage } from "./pages/ReaderLibraryPage";
import { VocabularyShelfPage } from "./pages/VocabularyShelfPage";
import { WorldInfoPage } from "./pages/WorldInfoPage";

function LegacyReaderLibraryRedirect() {
  const { readerId } = useParams();
  const location = useLocation();
  return <Navigate replace to={`/reader/${readerId}/books${location.search}`} />;
}

function LegacyReaderStoryRedirect() {
  const { readerId, storyId } = useParams();
  const location = useLocation();
  return <Navigate replace to={`/reader/${readerId}/books/${storyId}${location.search}`} />;
}

function LegacyReaderStoryReadRedirect() {
  const { readerId, storyId } = useParams();
  const location = useLocation();
  return <Navigate replace to={`/reader/${readerId}/books/${storyId}/read${location.search}`} />;
}

function LegacyReaderWorldRedirect() {
  const { readerId, worldId } = useParams();
  const location = useLocation();
  return <Navigate replace to={`/reader/${readerId}/worlds/${worldId}${location.search}`} />;
}

function LegacyReaderGamesRedirect() {
  const { readerId } = useParams();
  const location = useLocation();
  return <Navigate replace to={`/reader/${readerId}/games${location.search}`} />;
}

function LegacyReaderVocabularyRedirect() {
  const { readerId } = useParams();
  const location = useLocation();
  return <Navigate replace to={`/reader/${readerId}/words${location.search}`} />;
}

function HeaderNavLink({
  to,
  className,
  icon,
  children,
}: {
  to: string;
  className?: string;
  icon?: ReactNode;
  children: string;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        ["btn", "btn--secondary", "btn-size-compact", "app-header-button", isActive ? "active" : "", className]
          .filter(Boolean)
          .join(" ")
      }
    >
      {icon ? <span className="app-header-button-icon" aria-hidden="true">{icon}</span> : null}
      <span className="app-header-button-label">{children}</span>
    </NavLink>
  );
}

function App() {
  const { account, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/" className="brand">
          <img src="/retold-classics-logo.png" alt="Retold Classics Studios" className="brand-logo" />
          <span>
            <strong>StoryBloom</strong>
            <small>Retold Classics Studios</small>
          </span>
        </NavLink>

        <nav className="nav-links">
          <HeaderNavLink to="/classics" className="btn-tone-sky" icon="🧭">
            Classics
          </HeaderNavLink>
          <HeaderNavLink to="/blog" className="btn-tone-plum" icon="📝">
            Blog
          </HeaderNavLink>
          <HeaderNavLink to="/games/guest" className="btn-tone-mint" icon="🎮">
            Free Games
          </HeaderNavLink>
          <HeaderNavLink to="/for-families" className="btn-tone-coral" icon="❤️">
            Families
          </HeaderNavLink>
          <HeaderNavLink to="/contact" className="btn-tone-sky" icon="✉">
            Contact
          </HeaderNavLink>
          <HeaderNavLink to="/how-it-works" className="btn-tone-plum" icon="🪄">
            How It Works
          </HeaderNavLink>
          {account ? (
            <HeaderNavLink to="/chooser" className="btn-tone-sky" icon="🏠">
              Family Space
            </HeaderNavLink>
          ) : (
            <HeaderNavLink to="/login" className="btn-tone-sky" icon="🔑">
              Sign In
            </HeaderNavLink>
          )}
          {!account ? (
            <HeaderNavLink to="/register" className="btn-tone-gold" icon="✨">
              Start Free
            </HeaderNavLink>
          ) : null}
          {account ? (
            <button
              type="button"
              className="btn btn--secondary btn-tone-neutral btn-size-compact app-header-button"
              onClick={logout}
            >
              <span className="app-header-button-icon" aria-hidden="true">↩</span>
              <span className="app-header-button-label">Sign Out</span>
            </button>
          ) : null}
        </nav>
      </header>

      <main className="page-shell">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/reset-password" element={<PasswordResetRequestPage />} />
          <Route path="/reset-password/confirm" element={<PasswordResetConfirmPage />} />
          <Route path="/classics" element={<ClassicsShelfPage />} />
          <Route path="/blog" element={<BlogIndexPage />} />
          <Route path="/blog/:slug" element={<BlogPostPage />} />
          <Route path="/classics/:storyId" element={<ClassicStoryDetailPage />} />
          <Route path="/classics/:storyId/read" element={<ClassicReaderPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/games/guest" element={<GuestGamesPage />} />
          <Route path="/for-families" element={<FamiliesPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route
            path="/chooser"
            element={
              <ProtectedRoute>
                <ChooserPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent"
            element={
              <ParentProtectedRoute>
                <ParentAreaPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/parent/pin"
            element={
              <ProtectedRoute>
                <ParentPinPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/analytics"
            element={
              <ParentProtectedRoute>
                <ParentAnalyticsPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/parent/goals"
            element={
              <ParentProtectedRoute>
                <ParentGoalsPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/parent/content"
            element={
              <ParentProtectedRoute>
                <ParentContentPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/parent/readers/:readerId"
            element={
              <ParentProtectedRoute>
                <ParentReaderPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/parent/readers/:readerId/worlds/:worldId/canon"
            element={
              <ParentProtectedRoute>
                <ParentCharacterCanonPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ParentProtectedRoute>
                <DashboardPage />
              </ParentProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId"
            element={
              <ProtectedRoute>
                <ReaderHomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/books"
            element={
              <ProtectedRoute>
                <ReaderLibraryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/books/:storyId"
            element={
              <ProtectedRoute>
                <LibraryStoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/books/:storyId/read"
            element={
              <ProtectedRoute>
                <GeneratedStoryReaderPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/worlds/:worldId"
            element={
              <ProtectedRoute>
                <WorldInfoPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/games"
            element={
              <ProtectedRoute>
                <GameShelfPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/words"
            element={
              <ProtectedRoute>
                <VocabularyShelfPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reader/:readerId/goals"
            element={
              <ProtectedRoute>
                <ReaderGoalsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/library"
            element={
              <ProtectedRoute>
                <LegacyReaderLibraryRedirect />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/library/:storyId"
            element={
              <ProtectedRoute>
                <LegacyReaderStoryRedirect />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/library/:storyId/read"
            element={
              <ProtectedRoute>
                <LegacyReaderStoryReadRedirect />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/worlds/:worldId"
            element={
              <ProtectedRoute>
                <LegacyReaderWorldRedirect />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/games"
            element={
              <ProtectedRoute>
                <LegacyReaderGamesRedirect />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/vocabulary"
            element={
              <ProtectedRoute>
                <LegacyReaderVocabularyRedirect />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
      <SiteFooter />
    </div>
  );
}

export default App;
