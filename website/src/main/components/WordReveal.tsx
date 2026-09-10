interface WordRevealProps {
  text: string;
  baseDelay?: number;
  className?: string;
}

const WordReveal = ({ text, baseDelay = 1, className = '' }: WordRevealProps) => (
  <h1 className={className}>
    {text.split(' ').map((word, i) => (
      <span key={i} className="word-reveal" style={{ animationDelay: `${baseDelay + i * 0.05}s` }}>
        {word}
      </span>
    ))}
  </h1>
);

export default WordReveal;
