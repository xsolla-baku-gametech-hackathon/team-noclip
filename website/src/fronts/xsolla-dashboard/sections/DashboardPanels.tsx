import CriticalPriorities from './CriticalPriorities';
import StoryContext from './StoryContext';
import InventoryTracker from './InventoryTracker';

const DashboardPanels = () => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
    <CriticalPriorities />
    <StoryContext />
    <InventoryTracker />
  </div>
);

export default DashboardPanels;
