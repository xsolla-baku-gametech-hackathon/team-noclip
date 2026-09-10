import { Check, ArrowRight } from 'lucide-react';
import WordsPullUpMultiStyle from '../components/WordsPullUpMultiStyle';
import FeatureCard from '../components/FeatureCard';

interface ChecklistCardData {
  number: string;
  title: string;
  icon: string;
  items: string[];
}

const CARD_2: ChecklistCardData = {
  number: '01',
  title: 'Project Storyboard.',
  icon: 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260405_171918_4a5edc79-d78f-4637-ac8b-53c43c220606.png&w=1280&q=85',
  items: ['Scene-by-scene breakdown', 'Shot list generation', 'Visual reference boards', 'Timeline coordination'],
};

const CARD_3: ChecklistCardData = {
  number: '02',
  title: 'Smart Critiques.',
  icon: 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260405_171741_ed9845ab-f5b2-4018-8ce7-07cc01823522.png&w=1280&q=85',
  items: ['AI-powered scene analysis', 'Collaborative creative notes', 'Third-party tool integrations'],
};

const CARD_4: ChecklistCardData = {
  number: '03',
  title: 'Immersion Capsule.',
  icon: 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260405_171809_f56666dc-c099-4778-ad82-9ad4f209567b.png&w=1280&q=85',
  items: ['Automatic notification silencing', 'Curated ambient soundscapes', 'Cross-device schedule syncing'],
};

const ChecklistCard = ({ data, index }: { data: ChecklistCardData; index: number }) => (
  <FeatureCard index={index} className="bg-[#212121] p-5 sm:p-6 flex flex-col h-full min-h-[280px] lg:min-h-0">
    <img src={data.icon} alt="" className="w-10 h-10 sm:w-12 sm:h-12 rounded object-cover" />
    <h3 className="text-primary text-lg sm:text-xl mt-4 sm:mt-6">
      <span className="text-gray-500 mr-2">({data.number})</span>
      {data.title}
    </h3>
    <ul className="mt-4 sm:mt-6 flex flex-col gap-2 sm:gap-3 flex-1">
      {data.items.map((item) => (
        <li key={item} className="flex items-start gap-2 text-xs sm:text-sm text-gray-400">
          <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
    <a href="#" className="group flex items-center gap-2 text-primary text-xs sm:text-sm mt-4 sm:mt-6 w-fit">
      <span>Learn more</span>
      <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" style={{ transform: 'rotate(-45deg)' }} />
    </a>
  </FeatureCard>
);

const Features = () => {
  return (
    <section className="relative min-h-screen bg-black py-16 sm:py-24 md:py-32 px-4 md:px-6 overflow-hidden">
      <div className="bg-noise absolute inset-0 opacity-[0.15] pointer-events-none" />

      <div className="relative max-w-6xl mx-auto text-center mb-12 sm:mb-16 md:mb-20">
        <div className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-normal leading-tight">
          <WordsPullUpMultiStyle
            segments={[{ text: 'Studio-grade workflows for visionary creators.', className: 'text-primary' }]}
          />
        </div>
        <div className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-normal leading-tight mt-1">
          <WordsPullUpMultiStyle
            segments={[{ text: 'Built for pure vision. Powered by art.', className: 'text-gray-500' }]}
          />
        </div>
      </div>

      <div className="relative max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-2 md:gap-1 lg:h-[480px]">
        <FeatureCard index={0} className="relative min-h-[320px] lg:min-h-0 lg:h-full">
          <video
            className="absolute inset-0 h-full w-full object-cover"
            src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260406_133058_0504132a-0cf3-4450-a370-8ea3b05c95d4.mp4"
            autoPlay
            loop
            muted
            playsInline
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
          <p className="absolute bottom-5 left-5 sm:bottom-6 sm:left-6 text-base sm:text-lg" style={{ color: '#E1E0CC' }}>
            Your creative canvas.
          </p>
        </FeatureCard>

        <ChecklistCard data={CARD_2} index={1} />
        <ChecklistCard data={CARD_3} index={2} />
        <ChecklistCard data={CARD_4} index={3} />
      </div>
    </section>
  );
};

export default Features;
