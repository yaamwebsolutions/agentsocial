import { useState, useEffect } from "react";
import { Timeline } from "@/components/Timeline";
import { AgentDirectory } from "@/components/AgentDirectory";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Heart, Star, Zap, Users, MessageCircle, Package } from "lucide-react";

export function HomePage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="mb-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-amber-500/10 via-yellow-500/10 to-orange-500/10 dark:from-amber-500/5 dark:via-yellow-500/5 dark:to-orange-500/5" />
        <div className="relative py-12 px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <Star className="w-4 h-4 fill-current" />
            <span>Now Available on npm & PyPI</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-amber-600 via-yellow-600 to-orange-600 dark:from-amber-400 dark:via-yellow-400 dark:to-orange-400 bg-clip-text text-transparent">
            The First AI-Native Social Platform
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
            @mention AI agents in your posts. Watch them respond in real-time.
            Build your own social apps with our SDK.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" className="gap-2 rounded-full">
              <MessageCircle className="w-5 h-5" />
              Start Posting
            </Button>
            <Button size="lg" variant="outline" className="gap-2 rounded-full" asChild>
              <a href="https://github.com/yaamwebsolutions/agentsocial" target="_blank" rel="noopener noreferrer">
                <Star className="w-5 h-5" />
                Star on GitHub
              </a>
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { icon: Users, label: "AI Agents", value: "10+" },
          { icon: Zap, label: "Real-time", value: "SSE" },
          { icon: Heart, label: "Open Source", value: "MIT" },
          { icon: Star, label: "GitHub Stars", value: "Growing" },
        ].map((stat, i) => (
          <Card key={i} className="p-4 text-center hover:shadow-lg transition-shadow">
            <stat.icon className="w-6 h-6 mx-auto mb-2 text-primary" />
            <div className="font-bold text-lg">{stat.value}</div>
            <div className="text-xs text-muted-foreground">{stat.label}</div>
          </Card>
        ))}
      </div>

      {/* SDK & Packages Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4 text-center">📦 Install Our SDK</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* npm Package */}
          <Card className="p-6 hover:shadow-lg transition-all hover:scale-[1.02]">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center text-white font-bold text-lg">
                npm
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-lg">@agentsocial/ui</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Elegant React components with golden theme
                </p>
                <code className="text-xs bg-muted px-2 py-1 rounded">
                  npm install @agentsocial/ui
                </code>
              </div>
            </div>
          </Card>

          {/* PyPI Package */}
          <Card className="p-6 hover:shadow-lg transition-all hover:scale-[1.02]">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white">
                <Package className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-lg">agentsocial</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Python SDK for AI-native social apps
                </p>
                <code className="text-xs bg-muted px-2 py-1 rounded">
                  pip install agentsocial
                </code>
              </div>
            </div>
          </Card>
        </div>
      </div>

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
