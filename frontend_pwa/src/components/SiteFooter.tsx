export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <p>© {new Date().getFullYear()} StoryBloom by Retold Classics Studios</p>
        <a href="mailto:info@retoldclassics.com" className="site-footer-link">
          info@retoldclassics.com
        </a>
      </div>
    </footer>
  );
}
