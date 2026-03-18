import { NavLink, Route, Routes } from "react-router-dom";

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

function App() {
  const { account, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/" className="brand">
          <span className="brand-mark">SB</span>
          <span>
            <strong>StoryBloom</strong>
            <small>Retold Classics Studios</small>
          </span>
        </NavLink>

        <nav className="nav-links">
          <NavLink to="/classics">Classics</NavLink>
          <NavLink to="/blog">Blog</NavLink>
          <NavLink to="/games/guest">Free games</NavLink>
          <NavLink to="/for-families">Families</NavLink>
          <NavLink to="/contact">Contact</NavLink>
          <NavLink to="/how-it-works">How it works</NavLink>
          {account ? <NavLink to="/chooser">Family space</NavLink> : <NavLink to="/login">Login</NavLink>}
          {!account ? <NavLink to="/register">Start free</NavLink> : null}
          {account ? (
            <button type="button" className="ghost-button" onClick={logout}>
              Sign out
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
                <ReaderLibraryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/library/:storyId"
            element={
              <ProtectedRoute>
                <LibraryStoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/library/:storyId/read"
            element={
              <ProtectedRoute>
                <GeneratedStoryReaderPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/worlds/:worldId"
            element={
              <ProtectedRoute>
                <WorldInfoPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/games"
            element={
              <ProtectedRoute>
                <GameShelfPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/readers/:readerId/vocabulary"
            element={
              <ProtectedRoute>
                <VocabularyShelfPage />
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
