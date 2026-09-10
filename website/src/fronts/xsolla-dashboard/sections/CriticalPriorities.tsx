import { AlertTriangle } from 'lucide-react';
import GlassPanel from '../components/GlassPanel';

type Severity = 'HIGH' | 'MED' | 'LOW';

interface Priority {
  title: string;
  severity: Severity;
  description: string;
}

const PRIORITIES: Priority[] = [
  { title: 'Water Crops', severity: 'HIGH', description: '24 crops will die tomorrow if unwatered.' },
  { title: "Mayor's Shorts", severity: 'MED', description: 'Quest expires in 2 in-game days.' },
  { title: 'Pet the Dog', severity: 'LOW', description: 'Relationship decaying slightly.' },
];

const SEVERITY_STYLES: Record<Severity, string> = {
  HIGH: 'bg-red-100 text-red-600',
  MED: 'bg-amber-100 text-amber-600',
  LOW: 'bg-blue-100 text-blue-600',
};

const CriticalPriorities = () => (
  <GlassPanel className="rounded-3xl p-6">
    <div className="flex items-center gap-3 mb-6">
      <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
        <AlertTriangle className="text-red-500" size={16} />
      </div>
      <h3 className="font-bold text-slate-800">Critical Priorities</h3>
    </div>

    <div className="space-y-4">
      {PRIORITIES.map((priority) => (
        <div
          key={priority.title}
          className="p-4 rounded-2xl bg-white/60 hover:bg-white transition-colors cursor-pointer group"
        >
          <div className="flex justify-between items-start mb-1">
            <span className="font-semibold text-slate-800 group-hover:text-orange-500 transition-colors">
              {priority.title}
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${SEVERITY_STYLES[priority.severity]}`}>
              {priority.severity}
            </span>
          </div>
          <p className="text-xs text-slate-500">{priority.description}</p>
        </div>
      ))}
    </div>
  </GlassPanel>
);

export default CriticalPriorities;
