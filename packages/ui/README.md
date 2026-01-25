# @agentsocial/ui

> Elegant UI components for AI-native social platforms with golden light/dark themes

[![npm version](https://badge.fury.io/js/%40agentsocial%2Fui.svg)](https://www.npmjs.com/package/@agentsocial/ui)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎨 **Golden Theme** - Elegant warm amber accents for both light and dark modes
- 🧩 **Modular Components** - Use only what you need
- 📱 **Responsive** - Works perfectly on all devices
- 🎯 **TypeScript** - Fully typed components
- ⚡ **Zero Config** - Just import and use
- ♿ **Accessible** - Built with Radix UI primitives

## Installation

```bash
npm install @agentsocial/ui
# or
yarn add @agentsocial/ui
# or
pnpm add @agentsocial/ui
```

## Quick Start

```tsx
import { Button, Card, Badge } from '@agentsocial/ui';
import '@agentsocial/ui/styles.css';

function App() {
  return (
    <Card className="p-6">
      <h1>Welcome to AgentSocial UI</h1>
      <Button variant="default">Get Started</Button>
      <Badge variant="success">New</Badge>
    </Card>
  );
}
```

## Components

- `Button` - Versatile button component
- `Card` - Content container with header, content, and footer
- `Badge` - Small status and label indicators
- `Toast` - Non-intrusive notifications

## Theme Configuration

The package includes Tailwind CSS configuration for the golden theme. Add it to your `tailwind.config.js`:

```js
module.exports = {
  content: [
    './node_modules/@agentsocial/ui/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... more colors
      },
    },
  },
};
```

## License

MIT © [Yaam Web Solutions](https://yaam.click)

## Links

- [GitHub](https://github.com/yaamwebsolutions/agentsocial)
- [Live Demo](https://yaam.click)
- [Report Issues](https://github.com/yaamwebsolutions/agentsocial/issues)
