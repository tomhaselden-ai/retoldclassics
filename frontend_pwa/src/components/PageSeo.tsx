import { useEffect } from "react";

interface PageSeoProps {
  title: string;
  description: string;
}

function ensureMetaDescriptionTag(): HTMLMetaElement | null {
  if (typeof document === "undefined") {
    return null;
  }

  let tag = document.querySelector('meta[name="description"]');
  if (tag instanceof HTMLMetaElement) {
    return tag;
  }

  tag = document.createElement("meta");
  tag.setAttribute("name", "description");
  document.head.appendChild(tag);
  return tag as HTMLMetaElement;
}

export function PageSeo({ title, description }: PageSeoProps) {
  useEffect(() => {
    const previousTitle = document.title;
    const metaTag = ensureMetaDescriptionTag();
    const previousDescription = metaTag?.getAttribute("content") ?? "";

    document.title = title;
    if (metaTag) {
      metaTag.setAttribute("content", description);
    }

    return () => {
      document.title = previousTitle;
      if (metaTag) {
        metaTag.setAttribute("content", previousDescription);
      }
    };
  }, [description, title]);

  return null;
}
