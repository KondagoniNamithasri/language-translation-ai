interface SoundWaveProps {
  active: boolean;
  className?: string;
}

export const SoundWave = ({ active, className = "" }: SoundWaveProps) => {
  if (!active) return null;
  
  return (
    <div className={`sound-wave ${className}`}>
      <span></span>
      <span></span>
      <span></span>
      <span></span>
      <span></span>
    </div>
  );
};
