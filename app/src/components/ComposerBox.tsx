import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2, AtSign, Sparkles } from "lucide-react";
import { createPost } from "@/hooks/useApi";
import { useAgents } from "@/hooks/useApi";
import { useTheme } from "@/contexts/ThemeContext";
import type { Post } from "@/types/api";

interface ComposerBoxProps {
  parentId?: string;
  onPostCreated?: (post: Post) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

interface Suggestion {
  id: string;
  label: string;
  subtext?: string;
  icon?: string;
  color?: string;
  type: 'agent' | 'command' | 'emoji';
}

// Command suggestions
const COMMANDS: Suggestion[] = [
  { id: 'search', label: '/search', subtext: 'Search the web', icon: '🔍', type: 'command' },
  { id: 'image', label: '/image', subtext: 'Generate an image', icon: '🎨', type: 'command' },
  { id: 'video', label: '/video', subtext: 'Generate a video', icon: '🎬', type: 'command' },
  { id: 'scrape', label: '/scrape', subtext: 'Scrape a webpage', icon: '📄', type: 'command' },
  { id: 'email', label: '/email', subtext: 'Send as email', icon: '📧', type: 'command' },
];

// Emoji suggestions
const EMOJIS: Suggestion[] = [
  { id: '🚀', label: '🚀', subtext: 'rocket', type: 'emoji' },
  { id: '🔥', label: '🔥', subtext: 'fire', type: 'emoji' },
  { id: '✨', label: '✨', subtext: 'sparkles', type: 'emoji' },
  { id: '💡', label: '💡', subtext: 'idea', type: 'emoji' },
  { id: '🎯', label: '🎯', subtext: 'target', type: 'emoji' },
  { id: '🤖', label: '🤖', subtext: 'robot', type: 'emoji' },
  { id: '🧠', label: '🧠', subtext: 'brain', type: 'emoji' },
  { id: '⚡', label: '⚡', subtext: 'lightning', type: 'emoji' },
];

export function ComposerBox({
  parentId,
  onPostCreated,
  placeholder = "What's happening? Type @ for agents or / for commands...",
  autoFocus = false,
}: ComposerBoxProps) {
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [triggerChar, setTriggerChar] = useState<'@' | '/' | ':' | null>(null);
  const { agents } = useAgents();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  // Get current word before cursor
  const getCurrentWord = useCallback((text: string, cursorPos: number): { word: string; start: number } => {
    const beforeCursor = text.substring(0, cursorPos);
    const words = beforeCursor.split(/\s/);
    const currentWord = words[words.length - 1] || "";
    const start = cursorPos - currentWord.length;
    return { word: currentWord, start };
  }, []);

  // Filter agents based on search
  const filterAgents = useCallback((query: string): Suggestion[] => {
    if (!agents) return [];
    return agents
      .filter(a => a.id.toLowerCase().includes(query.toLowerCase()))
      .map(a => ({
        id: a.id,
        label: a.handle,
        subtext: a.role,
        icon: a.icon,
        color: a.color,
        type: 'agent' as const,
      }));
  }, [agents]);

  // Handle suggestions based on trigger
  const updateSuggestions = useCallback((text: string, cursorPos: number) => {
    const { word } = getCurrentWord(text, cursorPos);

    if (!word) {
      setShowSuggestions(false);
      setTriggerChar(null);
      return;
    }

    const firstChar = word[0];

    if (firstChar === '@') {
      setTriggerChar('@');
      const query = word.slice(1).toLowerCase();
      const filtered = filterAgents(query);
      setSuggestions(filtered);
      setShowSuggestions(true);
      setSelectedIndex(0);
    } else if (firstChar === '/') {
      setTriggerChar('/');
      const query = word.slice(1).toLowerCase();
      const filtered = COMMANDS.filter(c => c.label.slice(1).toLowerCase().includes(query));
      setSuggestions(filtered);
      setShowSuggestions(true);
      setSelectedIndex(0);
    } else if (firstChar === ':') {
      setTriggerChar(':');
      const query = word.slice(1).toLowerCase();
      const filtered = EMOJIS.filter(e => e.subtext?.toLowerCase().includes(query));
      setSuggestions(filtered);
      setShowSuggestions(true);
      setSelectedIndex(0);
    } else {
      setShowSuggestions(false);
      setTriggerChar(null);
    }
  }, [getCurrentWord, filterAgents]);

  // Handle input changes
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    const newCursorPos = e.target.selectionStart;
    setText(newText);
    setCursorPosition(newCursorPos);
    updateSuggestions(newText, newCursorPos);
  };

  // Handle suggestion selection
  const selectSuggestion = (suggestion: Suggestion) => {
    const { start } = getCurrentWord(text, cursorPosition);
    const before = text.substring(0, start);
    const after = text.substring(cursorPosition);

    let replacement = '';
    if (triggerChar === '@' || triggerChar === '/') {
      replacement = suggestion.label;
    } else if (triggerChar === ':') {
      replacement = suggestion.id;
    }

    const newText = before + replacement + after;
    setText(newText);
    setShowSuggestions(false);
    setTriggerChar(null);

    // Focus textarea and set cursor after replacement
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        const newCursorPos = start + replacement.length;
        textareaRef.current.setSelectionRange(newCursorPos, newCursorPos);
      }
    }, 0);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!showSuggestions) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => (i + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => (i - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (suggestions[selectedIndex]) {
        selectSuggestion(suggestions[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setTriggerChar(null);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  // Focus on mount if autoFocus
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setShowSuggestions(false);
    if (showSuggestions) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showSuggestions]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await createPost({ text, parent_id: parentId });
      setText("");
      onPostCreated?.(response.post);
    } catch (error) {
      console.error("Failed to create post:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const insertCommand = (command: string) => {
    setText(prev => prev + command + " ");
    textareaRef.current?.focus();
  };

  const extractMentions = (text: string) => {
    const mentions = text.match(/@([a-zA-Z0-9_]+)/g) || [];
    return mentions.map((m) => m.substring(1));
  };

  const mentions = extractMentions(text);

  return (
    <div className="border-b border-border/50 pb-6 relative">
      <form onSubmit={handleSubmit}>
        <div className="flex gap-4">
          {/* Enhanced Avatar */}
          <div className="flex-shrink-0">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white font-bold text-lg shadow-lg transition-all duration-300 ${
              isDark
                ? "bg-gradient-to-br from-amber-400 to-yellow-600"
                : "bg-gradient-to-br from-blue-400 to-blue-600"
            }`}>
              Y
            </div>
          </div>
          <div className="flex-1">
            <Textarea
              ref={textareaRef}
              id="composer-textarea"
              value={text}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="min-h-[80px] max-h-[200px] border-0 resize-none focus-visible:ring-0 p-0 text-base placeholder:text-muted-foreground/60 leading-relaxed"
              rows={2}
            />

            {/* Enhanced Quick action buttons */}
            <div className="flex gap-1.5 mt-4">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-9 px-3 text-muted-foreground hover:text-primary rounded-full transition-all hover:scale-105"
                onClick={() => insertCommand('@')}
                title="Mention an agent"
              >
                <AtSign className="w-4 h-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-9 px-3 text-muted-foreground hover:text-primary rounded-full transition-all hover:scale-105"
                onClick={() => insertCommand('/')}
                title="Commands"
              >
                <Sparkles className="w-4 h-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-9 px-3 text-muted-foreground hover:text-primary rounded-full transition-all hover:scale-105"
                onClick={() => insertCommand(':')}
                title="Emoji"
              >
                <span className="text-sm">😊</span>
              </Button>
            </div>

            {/* Enhanced Mention badges */}
            {mentions.length > 0 && (
              <div className="flex gap-2 mt-3 flex-wrap">
                {mentions.map((mention) => {
                  const agent = agents?.find(a => a.id === mention);
                  return (
                    <span
                      key={mention}
                      className="text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 font-medium transition-transform hover:scale-105"
                      style={{ backgroundColor: agent?.color || '#3B82F6', color: 'white' }}
                    >
                      <span className="text-sm">{agent?.icon || '🤖'}</span>
                      @{mention}
                    </span>
                  );
                })}
              </div>
            )}

            {/* Character count & Submit */}
            <div className="flex justify-between items-center mt-4">
              <span className={`text-xs ${
                text.length > 450 ? "text-orange-500" : text.length > 500 ? "text-red-500" : "text-muted-foreground"
              }`}>
                {text.length}/500
              </span>
              <Button
                type="submit"
                disabled={!text.trim() || isSubmitting || text.length > 500}
                className={`rounded-full px-8 font-semibold shadow-lg transition-all hover:scale-105 hover:shadow-xl ${
                  isDark
                    ? "bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 shadow-amber-500/30"
                    : "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-blue-500/30"
                }`}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Posting...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Post
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </form>

      {/* Enhanced Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          className="absolute left-14 right-4 mt-2 bg-popover/95 backdrop-blur-xl border border-border rounded-2xl shadow-2xl z-50 max-h-72 overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.id}
              type="button"
              className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-all ${
                index === selectedIndex ? 'bg-accent' : 'hover:bg-muted/50'
              }`}
              onClick={() => selectSuggestion(suggestion)}
            >
              {suggestion.type === 'agent' && (
                <>
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-lg shadow-md transition-transform hover:scale-110"
                    style={{ backgroundColor: suggestion.color || '#3B82F6' }}
                  >
                    {suggestion.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold truncate">{suggestion.label}</div>
                    <div className="text-xs text-muted-foreground truncate">{suggestion.subtext}</div>
                  </div>
                </>
              )}
              {suggestion.type === 'command' && (
                <>
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-lg">
                    {suggestion.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{suggestion.label}</div>
                    <div className="text-xs text-muted-foreground">{suggestion.subtext}</div>
                  </div>
                </>
              )}
              {suggestion.type === 'emoji' && (
                <>
                  <div className="w-10 h-10 flex items-center justify-center text-2xl">
                    {suggestion.id}
                  </div>
                  <div className="flex-1 text-sm text-muted-foreground">
                    {suggestion.subtext}
                  </div>
                </>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
