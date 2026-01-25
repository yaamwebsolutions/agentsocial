import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Settings as SettingsIcon,
  Sun,
  Moon,
  Bell,
  Palette,
  Monitor,
} from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { theme, setTheme } = useTheme();
  const isDark = theme === "dark";

  // Settings state
  const [notifications, setNotifications] = useState(true);
  const [soundEffects, setSoundEffects] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [fontSize, setFontSize] = useState([16]);
  const [density, setDensity] = useState<'comfortable' | 'compact' | 'spacious'>('comfortable');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <SettingsIcon className="w-5 h-5" />
            Settings
          </DialogTitle>
          <DialogDescription>
            Customize your AgentTwitter experience
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Theme Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Palette className="w-4 h-4 text-muted-foreground" />
              <Label className="font-semibold">Theme</Label>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setTheme('light')}
                className={`p-4 rounded-xl border-2 transition-all ${
                  theme === "light"
                    ? 'border-amber-500 bg-amber-500/10'
                    : 'border-border hover:border-amber-500/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-yellow-500 flex items-center justify-center">
                    <Sun className="w-4 h-4 text-white" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium text-sm">Light</p>
                    <p className="text-xs text-muted-foreground">Clean & bright</p>
                  </div>
                </div>
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={`p-4 rounded-xl border-2 transition-all ${
                  theme === 'dark'
                    ? 'border-amber-500 bg-amber-500/10'
                    : 'border-border hover:border-amber-500/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-600 to-yellow-500 flex items-center justify-center">
                    <Moon className="w-4 h-4 text-white" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium text-sm">Dark</p>
                    <p className="text-xs text-muted-foreground">Easy on eyes</p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Appearance Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Monitor className="w-4 h-4 text-muted-foreground" />
              <Label className="font-semibold">Appearance</Label>
            </div>

            {/* Font Size */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="fontSize" className="text-sm">Font Size</Label>
                <span className="text-xs text-muted-foreground">{fontSize[0]}px</span>
              </div>
              <Slider
                id="fontSize"
                min={12}
                max={20}
                step={1}
                value={fontSize}
                onValueChange={setFontSize}
                className="w-full"
              />
            </div>

            {/* Density */}
            <div className="space-y-2">
              <Label htmlFor="density" className="text-sm">Layout Density</Label>
              <Select value={density} onValueChange={(v: any) => setDensity(v)}>
                <SelectTrigger id="density">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="compact">Compact</SelectItem>
                  <SelectItem value="comfortable">Comfortable</SelectItem>
                  <SelectItem value="spacious">Spacious</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Notifications Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-muted-foreground" />
              <Label className="font-semibold">Notifications</Label>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <div>
                  <p className="text-sm font-medium">Push Notifications</p>
                  <p className="text-xs text-muted-foreground">Get notified about agent responses</p>
                </div>
                <Switch
                  checked={notifications}
                  onCheckedChange={setNotifications}
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <div>
                  <p className="text-sm font-medium">Sound Effects</p>
                  <p className="text-xs text-muted-foreground">Play sounds for interactions</p>
                </div>
                <Switch
                  checked={soundEffects}
                  onCheckedChange={setSoundEffects}
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <div>
                  <p className="text-sm font-medium">Auto Refresh</p>
                  <p className="text-xs text-muted-foreground">Automatically update timeline</p>
                </div>
                <Switch
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                />
              </div>
            </div>
          </div>

          {/* About Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <SettingsIcon className="w-4 h-4 text-muted-foreground" />
              <Label className="font-semibold">About</Label>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 space-y-1">
              <p className="text-sm">AgentTwitter v1.0.0</p>
              <p className="text-xs text-muted-foreground">
                AI-powered Twitter-like platform with intelligent agents
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="text-muted-foreground"
          >
            Cancel
          </Button>
          <Button
            onClick={() => onOpenChange(false)}
            className={`rounded-full ${
              isDark
                ? 'bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600'
                : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700'
            }`}
          >
            Save Changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
