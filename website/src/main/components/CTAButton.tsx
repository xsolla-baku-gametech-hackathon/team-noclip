interface CTAButtonProps {
  label: string;
  size?: 'large' | 'small';
  className?: string;
  disabled?: boolean;
  ariaBusy?: boolean;
  type?: 'button' | 'submit';
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
}: CTAButtonProps) => {
  if (size === 'small') {
    return (
      <button
        type={type}
        disabled={disabled}
        aria-busy={ariaBusy}
        className={`menu-cta-btn ${disabled ? 'is-disabled' : ''} ${className}`}
      >
        <span className="menu-cta-bg" />
        <span className="menu-cta-text">{label}</span>
        <span className="menu-cta-circle">
          <ArrowIcon size={14} />
        </span>
      </button>
    );
  }

  return (
    <button
      type={type}
      disabled={disabled}
      aria-busy={ariaBusy}
      className={`cta-btn ${disabled ? 'is-disabled' : ''} ${className}`}
    >
      <span className="cta-btn-bg" />
      <span className="cta-btn-text">{label}</span>
      <span className="cta-btn-circle">
        <ArrowIcon size={18} />
      </span>
    </button>
  );
};

export default CTAButton;
