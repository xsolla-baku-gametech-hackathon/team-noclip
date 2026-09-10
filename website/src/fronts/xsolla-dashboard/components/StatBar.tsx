interface StatBarProps {
  value: number;
  max: number;
  colorClassName: string;
}

const StatBar = ({ value, max, colorClassName }: StatBarProps) => {
  const percent = Math.min(100, Math.round((value / max) * 100));

  return (
    <div className="w-full bg-slate-200 rounded-full h-1.5 mt-1">
      <div className={`${colorClassName} h-1.5 rounded-full`} style={{ width: `${percent}%` }} />
    </div>
  );
};

export default StatBar;
