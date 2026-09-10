import { motion, useTransform, type MotionValue } from 'framer-motion';

interface AnimatedLetterProps {
  char: string;
  progress: MotionValue<number>;
  range: [number, number];
}

const AnimatedLetter = ({ char, progress, range }: AnimatedLetterProps) => {
  const opacity = useTransform(progress, range, [0.2, 1]);

  return <motion.span style={{ opacity }}>{char === ' ' ? ' ' : char}</motion.span>;
};

export default AnimatedLetter;
