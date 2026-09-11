interface CTAButtonProps {
  label: string;
  size?: 'large' | 'small';
  className?: string;
  disabled?: boolean;
  ariaBusy?: boolean;
  type?: 'button' | 'submit';
  onClick?: () => void;
  href?: string;
  download?: boolean | string;
}

const ArrowIcon = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M5 13L13 5M13 5H6M13 5V12"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const CTAButton = ({
  label,
  size = 'large',
  className = '',
  disabled = false,
  ariaBusy = false,
  type,
  onClick,
  href,
  download,
}: CTAButtonProps) => {
  const bgClass = size === 'small' ? 'menu-cta-bg' : 'cta-btn-bg';
  const textClass = size === 'small' ? 'menu-cta-text' : 'cta-btn-text';
  const circleClass = size === 'small' ? 'menu-cta-circle' : 'cta-btn-circle';
  const rootClass = size === 'small' ? 'menu-cta-btn' : 'cta-btn';
  const arrowSize = size === 'small' ? 14 : 18;

  const inner = (
    <>
      <span className={bgClass} />
      <span className={textClass}>{label}</span>
      <span className={circleClass}>
        <ArrowIcon size={arrowSize} />
      </span>
    </>
  );

  if (href && !disabled) {
    return (
      <a href={href} download={download} className={`${rootClass} ${className}`}>
        {inner}
      </a>
    );
  }

  return (
    <button
      type={type}
      disabled={disabled}
      aria-busy={ariaBusy}
      onClick={onClick}
      className={`${rootClass} ${disabled ? 'is-disabled' : ''} ${className}`}
    >
      {inner}
    </button>
  );
};

export default CTAButton;
