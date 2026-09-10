import { BookOpen, Check, Heart, Clock, type LucideIcon } from 'lucide-react';
import GlassPanel from '../components/GlassPanel';

type EventStatus = 'done' | 'active' | 'pending';

interface StoryEvent {
  title: string;
  description: string;
  status: EventStatus;
  icon: LucideIcon;
}

const STORY_EVENTS: StoryEvent[] = [
  { title: 'Mines Level 40', description: 'Reached iron ore levels.', status: 'done', icon: Check },
  { title: 'Abigail (4 Hearts)', description: "Need an amethyst for her birthday.", status: 'active', icon: Heart },
  { title: 'Coop Upgrade', description: "Pending Robin's construction.", status: 'pending', icon: Clock },
];

const MARKER_STYLES: Record<EventStatus, string> = {
  done: 'bg-indigo-500 text-white',
  active: 'bg-orange-400 text-white',
  pending: 'bg-slate-200 text-slate-400',
};

const CARD_STYLES: Record<EventStatus, string> = {
  done: 'bg-white/80 shadow-sm',
  active: 'bg-white/80 shadow-sm',
  pending: 'bg-white/50 border border-white',
};

const TEXT_STYLES: Record<EventStatus, { title: string; description: string }> = {
  done: { title: 'text-slate-800', description: 'text-slate-500' },
  active: { title: 'text-slate-800', description: 'text-slate-500' },
  pending: { title: 'text-slate-600', description: 'text-slate-400' },
};

const StoryContext = () => (
  <GlassPanel className="rounded-3xl p-6">
    <div className="flex items-center gap-3 mb-6">
      <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
        <BookOpen className="text-indigo-500" size={16} />
      </div>
      <h3 className="font-bold text-slate-800">Story Context</h3>
    </div>

    <ul className="relative space-y-6">
      <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-transparent via-slate-300 to-transparent" />

      {STORY_EVENTS.map(({ title, description, status, icon: Icon }) => (
        <li key={title} className="relative flex items-center gap-4">
          <div
            className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-4 border-white shadow shrink-0 ${MARKER_STYLES[status]}`}
          >
            <Icon size={14} />
          </div>
          <div className={`flex-1 p-4 rounded-xl ${CARD_STYLES[status]}`}>
            <div className={`font-bold text-sm mb-1 ${TEXT_STYLES[status].title}`}>{title}</div>
            <div className={`text-xs ${TEXT_STYLES[status].description}`}>{description}</div>
          </div>
        </li>
      ))}
    </ul>
  </GlassPanel>
);

export default StoryContext;
