import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

interface WordsPullUpProps {
  text: string;
  className?: string;
  showAsterisk?: boolean;
}

const WordsPullUp = ({ text, className = '', showAsterisk = false }: WordsPullUpProps) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const words = text.split(' ');

  return (
    <span ref={ref} className={className}>
      {words.map((word, wordIndex) => {
        const isLastWord = wordIndex === words.length - 1;
        const isLastLetterA = isLastWord && word.endsWith('a');

        return (
          <span key={wordIndex} className="inline-block overflow-hidden align-top pb-[0.1em]">
            <motion.span
              className="inline-block relative"
              initial={{ y: 20, opacity: 0 }}
              animate={isInView ? { y: 0, opacity: 1 } : { y: 20, opacity: 0 }}
              transition={{
                duration: 0.6,
                delay: wordIndex * 0.08,
                ease: [0.16, 1, 0.3, 1],
              }}
            >
              {showAsterisk && isLastLetterA ? (
                <>
                  {word.slice(0, -1)}
                  <span className="relative">
                    a
                    <span className="absolute top-[0.65em] -right-[0.3em] text-[0.31em]">*</span>
                  </span>
                </>
              ) : (
                word
              )}
              {!isLastWord && ' '}
            </motion.span>
          </span>
        );
      })}
    </span>
  );
};

export default WordsPullUp;
