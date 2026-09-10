import { Backpack, ShoppingBag } from 'lucide-react';
import GlassPanel from '../components/GlassPanel';
import StatBar from '../components/StatBar';

interface Resource {
  label: string;
  emoji: string;
  value: number;
  max: number;
  barColorClassName: string;
}

const RESOURCES: Resource[] = [
  { label: 'Wood', emoji: '🪵', value: 240, max: 400, barColorClassName: 'bg-amber-600' },
  { label: 'Stone', emoji: '🪨', value: 150, max: 150, barColorClassName: 'bg-emerald-500' },
  { label: 'Gold', emoji: '💰', value: 4500, max: 10000, barColorClassName: 'bg-yellow-500' },
];

const formatAmount = (n: number) => (n >= 1000 ? `${parseFloat((n / 1000).toFixed(1))}k` : `${n}`);

const InventoryTracker = () => (
  <GlassPanel className="rounded-3xl p-6">
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
          <Backpack className="text-emerald-500" size={16} />
        </div>
        <h3 className="font-bold text-slate-800">Needed Resources</h3>
      </div>
      <button className="text-xs font-bold text-orange-500 hover:text-orange-600">View All</button>
    </div>

    <div className="grid grid-cols-2 gap-4">
      {RESOURCES.map((resource) => (
        <div
          key={resource.label}
          className="bg-white/70 p-3 rounded-2xl flex flex-col items-center justify-center text-center gap-2 hover:bg-white transition-colors cursor-pointer"
        >
          <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-2xl shadow-inner">
            {resource.emoji}
          </div>
          <div>
            <p className="font-bold text-slate-800 text-sm">{resource.label}</p>
            <p className="text-xs text-slate-500">
              {formatAmount(resource.value)} / {formatAmount(resource.max)}
            </p>
          </div>
          <StatBar value={resource.value} max={resource.max} colorClassName={resource.barColorClassName} />
        </div>
      ))}

      <div className="bg-gradient-to-br from-orange-100 to-pink-100 border border-orange-200 p-3 rounded-2xl flex flex-col items-center justify-center text-center gap-2 hover:shadow-md transition-all cursor-pointer group">
        <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform">
          <ShoppingBag className="text-orange-500" size={16} />
        </div>
        <div>
          <p className="font-bold text-orange-700 text-xs">Short on time?</p>
          <p className="text-[10px] text-orange-600/80">Get resource packs</p>
        </div>
      </div>
    </div>
  </GlassPanel>
);

export default InventoryTracker;
