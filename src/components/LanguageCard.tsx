import { Globe2 } from "lucide-react";

interface LanguageCardProps {
  type: "source" | "target";
  language: string;
  languageNative?: string;
  className?: string;
}

export const LanguageCard = ({ type, language, languageNative, className = "" }: LanguageCardProps) => {
  const isSource = type === "source";
  
  return (
    <div className={`glass-panel rounded-xl p-4 ${className}`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isSource ? "bg-primary/20" : "bg-secondary/20"}`}>
          <Globe2 className={`w-5 h-5 ${isSource ? "text-primary" : "text-secondary"}`} />
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
            {isSource ? "From" : "To"}
          </p>
          <p className="font-display font-semibold text-foreground">
            {language}
            {languageNative && language !== languageNative && (
              <span className="text-muted-foreground font-normal ml-2">
                ({languageNative})
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
};
