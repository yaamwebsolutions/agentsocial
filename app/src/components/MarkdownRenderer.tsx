import { useTheme } from "@/contexts/ThemeContext";
import { Code } from "lucide-react";
import type { ReactNode } from "react";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const { theme } = useTheme();
  const isGolden = theme === "golden";

  // Parse markdown and convert to React elements
  const renderMarkdown = (text: string): ReactNode[] => {
    const lines = text.split('\n');
    const result: ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      // Code block
      if (trimmed.startsWith('```')) {
        const lang = trimmed.slice(3).trim() || 'text';
        const codeLines: string[] = [];
        i++;
        while (i < lines.length && !lines[i].trim().startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        result.push(
          <div key={`code-${i}`} className="relative group my-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-muted/50 rounded-t-lg border-b border-border/50">
              <Code className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground font-mono uppercase">{lang}</span>
            </div>
            <pre className={`p-4 rounded-b-lg overflow-x-auto ${
              isGolden ? 'bg-amber-950/30' : 'bg-slate-950/50'
            }`}>
              <code className="text-sm font-mono leading-relaxed">
                {codeLines.join('\n')}
              </code>
            </pre>
          </div>
        );
        i++;
        continue;
      }

      // Header ---
      if (trimmed.startsWith('###')) {
        const text = trimmed.slice(3).trim();
        result.push(
          <h3 key={`h3-${i}`} className="text-lg font-bold mt-6 mb-3 text-foreground">
            {parseInline(text)}
          </h3>
        );
        i++;
        continue;
      }

      // Header --
      if (trimmed.startsWith('##')) {
        const text = trimmed.slice(2).trim();
        result.push(
          <h2 key={`h2-${i}`} className="text-xl font-bold mt-6 mb-3 text-foreground">
            {parseInline(text)}
          </h2>
        );
        i++;
        continue;
      }

      // Header -
      if (trimmed.startsWith('#')) {
        const text = trimmed.slice(1).trim();
        result.push(
          <h1 key={`h1-${i}`} className="text-2xl font-bold mt-6 mb-3 text-foreground">
            {parseInline(text)}
          </h1>
        );
        i++;
        continue;
      }

      // Horizontal rule
      if (trimmed === '---') {
        result.push(<hr key={`hr-${i}`} className="my-4 border-border/50" />);
        i++;
        continue;
      }

      // Unordered list item
      if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
        const items: string[] = [];
        while (i < lines.length && (lines[i].trim().startsWith('-') || lines[i].trim().startsWith('*'))) {
          items.push(lines[i].trim().slice(1).trim());
          i++;
        }
        result.push(
          <ul key={`ul-${i}`} className="my-4 space-y-2">
            {items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className={`flex-shrink-0 w-1.5 h-1.5 rounded-full mt-2 ${
                  isGolden ? 'bg-amber-400' : 'bg-blue-400'
                }`} />
                <span className="flex-1">{parseInline(item)}</span>
              </li>
            ))}
          </ul>
        );
        continue;
      }

      // Numbered list item
      if (/^\d+\./.test(trimmed)) {
        const items: { text: string }[] = [];
        while (i < lines.length && /^\d+\./.test(lines[i].trim())) {
          const match = lines[i].trim().match(/^\d+\.\s*(.*)/);
          if (match) {
            items.push({ text: match[1] });
          }
          i++;
        }
        result.push(
          <ol key={`ol-${i}`} className="my-4 space-y-2">
            {items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                  isGolden ? 'bg-amber-500' : 'bg-blue-500'
                }`}>
                  {idx + 1}
                </span>
                <span className="flex-1">{parseInline(item.text)}</span>
              </li>
            ))}
          </ol>
        );
        continue;
      }

      // Blockquote
      if (trimmed.startsWith('>')) {
        const quoteText = trimmed.slice(1).trim();
        result.push(
          <blockquote key={`quote-${i}`} className={`my-4 p-4 border-l-4 rounded-r-lg italic ${
            isGolden
              ? 'bg-amber-950/20 border-amber-500/50 text-amber-100'
              : 'bg-blue-950/20 border-blue-500/50 text-blue-100'
          }`}>
            {parseInline(quoteText)}
          </blockquote>
        );
        i++;
        continue;
      }

      // Empty line
      if (!trimmed) {
        result.push(<br key={`br-${i}`} />);
        i++;
        continue;
      }

      // Regular paragraph
      result.push(
        <p key={`p-${i}`} className="my-2 leading-relaxed">
          {parseInline(line)}
        </p>
      );
      i++;
    }

    return result;
  };

  // Parse inline markdown (bold, italic, code)
  const parseInline = (text: string): ReactNode => {
    const parts: ReactNode[] = [];
    let lastIndex = 0;

    // Match various markdown patterns
    // Order matters: code > bold > italic
    const patterns = [
      { regex: /`([^`]+)`/g, type: 'code' as const },
      { regex: /\*\*\*([^*]+)\*\*\*/g, type: 'bold-italic' as const },
      { regex: /\*\*([^*]+)\*\*/g, type: 'bold' as const },
      { regex: /\*([^*]+)\*/g, type: 'italic' as const },
      { regex: /__([^_]+)__/g, type: 'bold' as const },
      { regex: /_([^_]+)_/g, type: 'italic' as const },
    ];

    let matchIndex = text.length;
    let matchedPattern: typeof patterns[0] | null = null;
    let matchedText = '';
    let matchedStart = 0;

    // Find the first match
    for (const pattern of patterns) {
      pattern.regex.lastIndex = 0;
      const match = pattern.regex.exec(text);
      if (match && match.index < matchIndex) {
        matchIndex = match.index;
        matchedPattern = pattern;
        matchedText = match[1];
        matchedStart = match.index;
      }
    }

    if (matchedPattern) {
      // Text before the match
      if (matchedStart > lastIndex) {
        parts.push(<span key={`text-${lastIndex}`}>{text.slice(lastIndex, matchedStart)}</span>);
      }

      // The matched content
      const matchEnd = matchedStart + matchedText.length + 2 + (matchedPattern.type === 'bold-italic' ? 2 : 0);

      switch (matchedPattern.type) {
        case 'code':
          parts.push(
            <code key={`code-${matchedStart}`} className={`px-1.5 py-0.5 rounded text-sm font-mono ${
              isGolden ? 'bg-amber-950/50 text-amber-300' : 'bg-slate-800 text-blue-300'
            }`}>
              {matchedText}
            </code>
          );
          break;
        case 'bold':
        case 'bold-italic':
          parts.push(
            <strong key={`bold-${matchedStart}`} className="font-semibold text-foreground">
              {matchedText}
            </strong>
          );
          break;
        case 'italic':
          parts.push(
            <em key={`italic-${matchedStart}`} className="italic text-muted-foreground">
              {matchedText}
            </em>
          );
          break;
      }

      // Recursively parse the rest
      const remaining = text.slice(matchEnd);
      if (remaining) {
        parts.push(<span key={`remaining-${matchedStart}`}>{parseInline(remaining)}</span>);
      }
    } else if (lastIndex < text.length) {
      // No matches, return plain text
      parts.push(<span key={`text-${lastIndex}`}>{text.slice(lastIndex)}</span>);
    }

    return parts.length > 0 ? <>{parts}</> : <>{text}</>;
  };

  return (
    <div className="prose prose-invert max-w-none">
      {renderMarkdown(content)}
    </div>
  );
}

// Compact version for inline text (mentions, etc.)
export function InlineMarkdown({ content }: { content: string }) {
  const { theme } = useTheme();
  const isGolden = theme === "golden";

  const parseInline = (text: string): ReactNode => {
    // Split by markdown patterns
    const segments = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);

    return segments.map((seg, idx) => {
      if (!seg) return null;

      // Bold
      if (seg.startsWith('**') && seg.endsWith('**')) {
        return (
          <strong key={idx} className="font-semibold">
            {seg.slice(2, -2)}
          </strong>
        );
      }

      // Italic
      if (seg.startsWith('*') && seg.endsWith('*') && seg.length > 2) {
        return (
          <em key={idx} className="italic">
            {seg.slice(1, -1)}
          </em>
        );
      }

      // Inline code
      if (seg.startsWith('`') && seg.endsWith('`')) {
        return (
          <code key={idx} className={`px-1.5 py-0.5 rounded text-sm font-mono ${
            isGolden ? 'bg-amber-950/50 text-amber-300' : 'bg-slate-800 text-blue-300'
          }`}>
            {seg.slice(1, -1)}
          </code>
        );
      }

      return <span key={idx}>{seg}</span>;
    });
  };

  return <>{parseInline(content)}</>;
}
