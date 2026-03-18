import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";

type StoryBloomShape = "sun" | "star" | "diamond" | "heart" | "moon";
type StoryBloomVariant = "primary" | "ghost";

interface BaseProps {
  children: ReactNode;
  className?: string;
  shape?: StoryBloomShape;
  variant?: StoryBloomVariant;
}

interface LinkProps extends BaseProps {
  to: string;
}

interface ButtonProps extends BaseProps, Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children"> {
  to?: never;
}

type StoryBloomActionButtonProps = LinkProps | ButtonProps;

function buildClassName(variant: StoryBloomVariant, className?: string) {
  return ["storybloom-button", `storybloom-button-${variant}`, className].filter(Boolean).join(" ");
}

export function StoryBloomActionButton(props: StoryBloomActionButtonProps) {
  const shape = props.shape ?? "sun";
  const variant = props.variant ?? "primary";
  const className = buildClassName(variant, props.className);

  if (typeof (props as LinkProps).to === "string") {
    const { to, children } = props as LinkProps;
    return (
      <Link to={to} className={className} data-shape={shape}>
        <span className="storybloom-button-label">{children}</span>
      </Link>
    );
  }

  const { children, shape: _shape, variant: _variant, className: _className, ...buttonProps } = props;
  return (
    <button {...buttonProps} className={className} data-shape={shape}>
      <span className="storybloom-button-label">{children}</span>
    </button>
  );
}
