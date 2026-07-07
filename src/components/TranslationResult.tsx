import { ArrowRight } from "lucide-react";

interface TranslationResultProps {
  originalText: string;
  translatedText: string;
  targetLanguage: string;
}

export const TranslationResult = ({ originalText, translatedText, targetLanguage }: TranslationResultProps) => {
  if (!translatedText) return null;
  
  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
        <span className="text-xs text-muted-foreground uppercase tracking-widest font-display">Translation Result</span>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
      </div>
      
      <div className="grid md:grid-cols-2 gap-4">
        {/* Original */}
        <div className="glass-panel rounded-xl p-5 animate-slide-in-left">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">Original</span>
          </div>
          <p className="text-foreground leading-relaxed font-body">
            {originalText}
          </p>
        </div>

        {/* Arrow for desktop */}
        <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center shadow-glow">
            <ArrowRight className="w-5 h-5 text-primary-foreground" />
          </div>
        </div>

        {/* Translated */}
        <div className="glass-panel rounded-xl p-5 border-primary/20 animate-slide-in-right relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-secondary" />
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
                {targetLanguage}
              </span>
            </div>
            <p className="text-foreground leading-relaxed font-body text-lg">
              {translatedText}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
