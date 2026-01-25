import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Header } from "@/components/Header";
import { HomePage } from "@/pages/HomePage";
import { AgentsPage } from "@/pages/AgentsPage";
import { ThreadView } from "@/components/ThreadView";
import { CallbackPage } from "@/pages/CallbackPage";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";

function App() {
  return (
    <ThemeProvider>
      <TooltipProvider>
        <BrowserRouter>
          <AuthProvider>
            <div className="min-h-screen bg-background">
              <Header />
              <main className="pt-0">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/agents" element={<AgentsPage />} />
                  <Route path="/thread/:threadId" element={<ThreadView />} />
                  <Route path="/callback" element={<CallbackPage />} />
                </Routes>
              </main>
              <Toaster />
            </div>
          </AuthProvider>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
