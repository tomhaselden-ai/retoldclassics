import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";

type StoryBloomShape = "sun" | "star" | "diamond" | "heart" | "moon";
type StoryBloomVariant = "primary" | "ghost";
type StoryBloomTone = "gold" | "coral" | "sky" | "mint" | "plum" | "neutral" | "danger";
type StoryBloomDepth = "raised" | "flat";
type StoryBloomFamily = "nav" | "primary" | "secondary" | "control" | "create" | "admin" | "danger" | "chip";
type StoryBloomSize = "hero" | "default" | "compact";

interface BaseProps {
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
  shape?: StoryBloomShape;
  variant?: StoryBloomVariant;
  tone?: StoryBloomTone;
  depth?: StoryBloomDepth;
  family?: StoryBloomFamily;
  size?: StoryBloomSize;
}

interface LinkProps extends BaseProps {
  to: string;
}

interface ButtonProps extends BaseProps, Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children"> {
  to?: never;
}

type StoryBloomActionButtonProps = LinkProps | ButtonProps;

function buildClassName(
  variant: StoryBloomVariant,
  family: StoryBloomFamily,
  tone: StoryBloomTone,
  size: StoryBloomSize,
  className?: string,
) {
  return [
    "btn",
    `btn--${family}`,
    `btn-tone-${tone}`,
    `btn-size-${size}`,
    variant === "ghost" ? "btn--secondary" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");
}

export function StoryBloomActionButton(props: StoryBloomActionButtonProps) {
  const variant = props.variant ?? "primary";
  const tone = props.tone ?? "gold";
  const family = props.family ?? "primary";
  const size = props.size ?? "default";
  const className = buildClassName(variant, family, tone, size, props.className);
  const icon = props.icon;

  if (typeof (props as LinkProps).to === "string") {
    const { to, children } = props as LinkProps;
    return (
      <Link to={to} className={className}>
        {icon ? <span className="storybloom-button-icon" aria-hidden="true">{icon}</span> : null}
        <span className="storybloom-button-label">{children}</span>
      </Link>
    );
  }

  const {
    children,
    shape: _shape,
    variant: _variant,
    tone: _tone,
    depth: _depth,
    family: _family,
    size: _size,
    icon: _icon,
    className: _className,
    ...buttonProps
  } = props;
  return (
    <button {...buttonProps} className={className}>
      {icon ? <span className="storybloom-button-icon" aria-hidden="true">{icon}</span> : null}
      <span className="storybloom-button-label">{children}</span>
    </button>
  );
}
