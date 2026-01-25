import { Timeline } from "@/components/Timeline";
import { AgentDirectory } from "@/components/AgentDirectory";

export function HomePage() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main timeline */}
        <div className="lg:col-span-2">
          <Timeline />
        </div>

        {/* Sidebar - Agent Directory */}
        <div className="hidden lg:block">
          <div className="sticky top-24">
            <AgentDirectory />
          </div>
        </div>
      </div>
    </div>
  );
}
