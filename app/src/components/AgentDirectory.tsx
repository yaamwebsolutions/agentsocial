import { useAgents } from "@/hooks/useApi";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, Loader2 } from "lucide-react";

export function AgentDirectory() {
  const { agents, loading } = useAgents();

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Bot className="w-5 h-5" />
        AI Agents
      </h2>
      
      <div className="space-y-4">
        {agents?.map((agent) => (
          <div
            key={agent.id}
            className="flex gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-white text-lg flex-shrink-0"
              style={{ backgroundColor: agent.color }}
            >
              {agent.icon}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">{agent.name}</span>
                <Badge
                  variant="outline"
                  className="text-xs"
                  style={{
                    borderColor: agent.color,
                    color: agent.color,
                  }}
                >
                  {agent.handle}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {agent.role}
              </p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                {agent.tools.length} tools available
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-border/50">
        <p className="text-xs text-muted-foreground">
          Tag any agent with @{"agent-name"} in your posts to get AI-powered responses.
        </p>
      </div>
    </Card>
  );
}
