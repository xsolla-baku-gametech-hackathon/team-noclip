import { useRef } from 'react';
import { useScroll } from 'framer-motion';
import WordsPullUpMultiStyle from '../components/WordsPullUpMultiStyle';
import AnimatedLetter from '../components/AnimatedLetter';

const BODY_TEXT =
  'Over the last seven years, I have worked with Parallax, a Berlin-based production house that crafts cinema, series, and Noir Studio in Paris. Together, we have created work that has earned international acclaim at several major festivals.';

const About = () => {
  const paragraphRef = useRef<HTMLParagraphElement>(null);
  const { scrollYProgress } = useScroll({
    target: paragraphRef,
    offset: ['start 0.8', 'end 0.2'],
  });

  const chars = BODY_TEXT.split('');
  const totalChars = chars.length;

  return (
    <section className="bg-black py-16 sm:py-24 md:py-32 px-4 md:px-6">
      <div className="bg-[#101010] rounded-2xl md:rounded-[2rem] max-w-6xl mx-auto px-6 py-16 sm:px-10 sm:py-20 md:px-16 md:py-28 text-center">
        <p className="text-primary text-[10px] sm:text-xs uppercase tracking-widest mb-6 sm:mb-8">
          Visual arts
        </p>

        <div className="max-w-3xl mx-auto leading-[0.95] sm:leading-[0.9] text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl">
          <WordsPullUpMultiStyle
            segments={[
              { text: 'I am Marcus Chen,', className: 'font-normal text-primary' },
              { text: 'a self-taught director.', className: 'italic font-serif text-primary' },
              {
                text: 'I have skills in color grading, visual effects, and narrative design.',
                className: 'font-normal text-primary',
              },
            ]}
          />
        </div>

        <p
          ref={paragraphRef}
          className="text-[#DEDBC8] text-xs sm:text-sm md:text-base mt-8 sm:mt-10 max-w-2xl mx-auto leading-relaxed"
        >
          {chars.map((char, index) => {
            const charProgress = index / totalChars;
            const range: [number, number] = [charProgress - 0.1, charProgress + 0.05];
            return (
              <AnimatedLetter key={index} char={char} progress={scrollYProgress} range={range} />
            );
          })}
        </p>
      </div>
    </section>
  );
};

export default About;
