import { useState, useEffect, useRef } from "react";
import { Search, Command, Sparkles } from "lucide-react";

interface Command {
  id: string;
  label: string;
  description: string;
  icon: any;
  action: () => void;
  category: string;
}

interface CommandPaletteProps {
  agents: Array<{ id: string; handle: string; name: string; icon: string; color: string }>;
  onCreatePost?: (text: string) => void;
  onSearch?: (query: string) => void;
}

export function CommandPalette({ agents, onCreatePost, onSearch }: CommandPaletteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const paletteRef = useRef<HTMLDivElement>(null);

  // Build commands list
  const commands: Command[] = [
    {
      id: "new-post",
      label: "New Post",
      description: "Create a new post",
      icon: Sparkles,
      action: () => {
        setIsOpen(false);
        document.getElementById("composer-textarea")?.focus();
      },
      category: "Actions"
    },
    {
      id: "search",
      label: "Search",
      description: "Search posts and topics",
      icon: Search,
      action: () => {
        setIsOpen(false);
        onSearch?.(query);
      },
      category: "Actions"
    },
    ...agents.slice(0, 5).map(agent => ({
      id: agent.id,
      label: agent.name,
      description: agent.handle,
      icon: () => <span style={{ backgroundColor: agent.color }} className="w-6 h-6 rounded-full flex items-center justify-center text-xs">{agent.icon}</span>,
      action: () => {
        setIsOpen(false);
        onCreatePost?.(`${agent.handle} `);
      },
      category: "Agents"
    }))
  ];

  // Filter commands
  const filteredCommands = query
    ? commands.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.description.toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to open
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      // Escape to close
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
      // Arrow keys to navigate
      if (isOpen) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSelectedIndex(i => (i + 1) % filteredCommands.length);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          setSelectedIndex(i => (i - 1 + filteredCommands.length) % filteredCommands.length);
        } else if (e.key === "Enter") {
          e.preventDefault();
          filteredCommands[selectedIndex]?.action();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Reset when closed
  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (paletteRef.current && !paletteRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const executeCommand = (command: Command) => {
    command.action();
    setIsOpen(false);
  };

  // Group commands by category
  const groupedCommands = filteredCommands.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, Command[]>);

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/50 hover:bg-muted text-sm text-muted-foreground transition-colors"
      >
        <Search className="w-4 h-4" />
        <span>Search...</span>
        <kbd className="ml-auto hidden xs:inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-background border text-[10px]">
          <span>⌘</span>K
        </kbd>
      </button>

      {/* Overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-[20vh]">
          <div
            ref={paletteRef}
            className="w-full max-w-lg bg-popover border border-border rounded-xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-3 border-b">
              <Search className="w-5 h-5 text-muted-foreground" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type a command or search..."
                className="flex-1 bg-transparent outline-none text-base"
                autoFocus
              />
              <kbd className="flex items-center gap-1 px-2 py-1 rounded bg-muted text-xs text-muted-foreground">
                <span>ESC</span>
              </kbd>
            </div>

            {/* Commands list */}
            <div className="max-h-80 overflow-y-auto py-2">
              {Object.entries(groupedCommands).map(([category, cmds]) => (
                <div key={category}>
                  <div className="px-4 py-1 text-xs font-semibold text-muted-foreground uppercase">
                    {category}
                  </div>
                  {cmds.map((cmd) => {
                    const globalIdx = filteredCommands.indexOf(cmd);
                    const Icon = cmd.icon;
                    const isSelected = globalIdx === selectedIndex;

                    return (
                      <button
                        key={cmd.id}
                        onClick={() => executeCommand(cmd)}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                          isSelected ? "bg-accent" : "hover:bg-muted/50"
                        }`}
                      >
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                          {typeof Icon === "function" ? <Icon /> : <Icon className="w-5 h-5" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium">{cmd.label}</div>
                          <div className="text-sm text-muted-foreground truncate">{cmd.description}</div>
                        </div>
                        {isSelected && (
                          <kbd className="px-2 py-1 rounded bg-muted text-xs">↵</kbd>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}

              {filteredCommands.length === 0 && (
                <div className="px-4 py-8 text-center text-muted-foreground">
                  No commands found
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-muted">↑↓</kbd> Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-muted">↵</kbd> Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-muted">ESC</kbd> Close
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
