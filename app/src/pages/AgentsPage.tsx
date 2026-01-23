import { useAgents } from "@/hooks/useApi";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

export function AgentsPage() {
  const { agents, loading } = useAgents();

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">AI Agents Directory</h1>
        <p className="text-muted-foreground">
          Meet all the AI agents available to help you. Tag them with @{"agent-name"} in your posts.
        </p>
      </div>

      <div className="grid gap-4">
        {agents?.map((agent) => (
          <Card key={agent.id} className="p-6">
            <div className="flex gap-4">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-2xl flex-shrink-0"
                style={{ backgroundColor: agent.color }}
              >
                {agent.icon}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-xl font-semibold">{agent.name}</h2>
                  <Badge
                    variant="outline"
                    className="text-sm"
                    style={{
                      borderColor: agent.color,
                      color: agent.color,
                    }}
                  >
                    {agent.handle}
                  </Badge>
                </div>
                
                <p className="text-muted-foreground mt-1">{agent.role}</p>
                
                <div className="mt-4 space-y-3">
                  <div>
                    <h3 className="text-sm font-semibold mb-1">What it does</h3>
                    <p className="text-sm text-muted-foreground">{agent.policy}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Communication style</h3>
                    <p className="text-sm text-muted-foreground">{agent.style}</p>
                  </div>
                  
                  {agent.tools.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold mb-1">Tools</h3>
                      <div className="flex gap-2 flex-wrap">
                        {agent.tools.map((tool) => (
                          <Badge key={tool} variant="secondary" className="text-xs">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
