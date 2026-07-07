import { Languages, Cpu, Mic, Volume2 } from "lucide-react";

const technologies = [
  {
    icon: Mic,
    name: "Whisper ASR",
    description: "OpenAI's speech recognition",
    color: "from-primary to-accent"
  },
  {
    icon: Languages,
    name: "mBART-50 NMT",
    description: "Neural machine translation",
    color: "from-secondary to-primary"
  },
  {
    icon: Volume2,
    name: "gTTS Synthesis",
    description: "Natural text-to-speech",
    color: "from-accent to-secondary"
  },
  {
    icon: Cpu,
    name: "Contextual Memory",
    description: "Sliding-window coherence",
    color: "from-primary to-secondary"
  }
];

export const TechStack = () => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {technologies.map((tech, index) => (
        <div
          key={tech.name}
          className="glass-panel rounded-xl p-4 glow-effect group cursor-default animate-fade-in-up"
          style={{ animationDelay: `${index * 0.1}s` }}
        >
          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${tech.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300`}>
            <tech.icon className="w-5 h-5 text-primary-foreground" />
          </div>
          <h3 className="font-display font-semibold text-foreground text-sm">
            {tech.name}
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            {tech.description}
          </p>
        </div>
      ))}
    </div>
  );
};
