import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Header } from "@/components/Header";
import { HomePage } from "@/pages/HomePage";
import { AgentsPage } from "@/pages/AgentsPage";
import { ThreadView } from "@/components/ThreadView";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/contexts/ThemeContext";

function App() {
  return (
    <ThemeProvider>
      <TooltipProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-background">
            <Header />
            <main className="pt-0">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/agents" element={<AgentsPage />} />
                <Route path="/thread/:threadId" element={<ThreadView />} />
              </Routes>
            </main>
            <Toaster />
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
