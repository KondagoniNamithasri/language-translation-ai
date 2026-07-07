import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { useSpeech } from "@/hooks/useSpeech";
import { useTranslation } from "@/hooks/useTranslation";
import { TechStack } from "@/components/TechStack";
import { SoundWave } from "@/components/SoundWave";
import { TranslationResult } from "@/components/TranslationResult";
import { LANGUAGES, getLanguageByCode } from "@/lib/languages";
import { 
  Volume2, 
  Languages, 
  Mic, 
  Square, 
  Sparkles, 
  Globe2, 
  ArrowRight,
  Zap,
  Loader2
} from "lucide-react";

const Index = () => {
  const { toast } = useToast();
  const { speak, speaking, cancel } = useSpeech();
  const { translate, isLoading } = useTranslation();

  const [inputText, setInputText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [sourceLang] = useState("en");
  const [targetLang, setTargetLang] = useState("hi");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const targetLanguage = getLanguageByCode(targetLang);

  const startRecording = async () => {
    if (isRecording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        audioChunksRef.current = [];
        stream.getTracks().forEach((track) => track.stop());

        try {
          setIsTranscribing(true);
          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.webm");

          const transcribeUrl = new URL("http://127.0.0.1:5000/api/transcribe");
          transcribeUrl.searchParams.set("language", sourceLang);

          const response = await fetch(transcribeUrl.toString(), {
            method: "POST",
            body: formData,
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.error || "Transcription failed");
          }

          const text = data.text || "";
          setInputText(text);

          toast({
            title: "Transcription complete",
            description: "Your speech has been converted to text.",
          });
        } catch (error) {
          console.error(error);
          toast({
            title: "Transcription error",
            description: "Could not transcribe your audio. Please check your backend connection.",
            variant: "destructive",
          });
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error(error);
      toast({
        title: "Microphone error",
        description: "Could not access your microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = () => {
    if (!isRecording || !mediaRecorderRef.current) return;
    mediaRecorderRef.current.stop();
    mediaRecorderRef.current = null;
    setIsRecording(false);
  };

  const handleTranslateAndSpeak = async () => {
    if (!inputText.trim()) {
      toast({
        title: "No text provided",
        description: "Please enter or record some text first.",
      });
      return;
    }

    try {
      const translation = await translate(inputText, targetLang, sourceLang);
      setTranslatedText(translation);
      speak(translation, targetLang);
    } catch (error) {
      console.error(error);
      toast({
        title: "Translation error",
        description:
          error instanceof Error
            ? error.message
            : "Something went wrong during translation.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 lg:py-12">
        {/* Header */}
        <header className="text-center mb-12 lg:mb-16 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">AI-Powered Translation</span>
          </div>
          
          <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold mb-4">
            <span className="text-gradient-primary">Break Language</span>
            <br />
            <span className="text-foreground">Barriers</span>
          </h1>
          
          <p className="text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            Real-time speech-to-speech translation powered by Whisper ASR, 
            mBART-50 Neural Machine Translation, and gTTS synthesis.
          </p>
        </header>

        {/* Technology Stack */}
        <section className="mb-12 lg:mb-16">
          <TechStack />
        </section>

        {/* Main Translator Card */}
        <section className="max-w-4xl mx-auto">
          <div className="glass-panel rounded-2xl lg:rounded-3xl p-6 lg:p-10 shadow-elevated relative overflow-hidden">
            {/* Decorative gradient */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-secondary to-accent" />
            
            {/* Language Selection Row */}
            <div className="flex flex-col md:flex-row items-center gap-4 mb-8">
              {/* Source Language */}
              <div className="flex-1 w-full">
                <div className="glass-panel rounded-xl p-4 flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <Globe2 className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">Source Language</p>
                    <p className="font-display font-semibold text-foreground text-lg">English</p>
                  </div>
                </div>
              </div>

              {/* Arrow */}
              <div className="flex items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center shadow-glow">
                  <ArrowRight className="w-5 h-5 text-primary-foreground" />
                </div>
              </div>

              {/* Target Language */}
              <div className="flex-1 w-full">
                <div className="glass-panel rounded-xl p-4">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2">Target Language</p>
                  <Select value={targetLang} onValueChange={setTargetLang}>
                    <SelectTrigger className="w-full bg-muted/50 border-border/50 h-12 font-display font-semibold text-lg">
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px] bg-popover/95 backdrop-blur-lg border-border/50">
                      {LANGUAGES.map((lang) => (
                        <SelectItem 
                          key={lang.code} 
                          value={lang.code}
                          className="font-body hover:bg-primary/10"
                        >
                          <span className="font-medium">{lang.name}</span>
                          {lang.native !== lang.name && (
                            <span className="text-muted-foreground ml-2">({lang.native})</span>
                          )}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Recording Section */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Mic className="w-4 h-4" />
                  Record or type your message
                </label>
                <SoundWave active={isRecording} />
              </div>

              <div className="flex gap-4 mb-4">
                <Button
                  variant={isRecording ? "recording" : "glass"}
                  size="icon-lg"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isTranscribing}
                  className="relative"
                >
                  {isRecording ? (
                    <>
                      <div className="absolute inset-0 rounded-full animate-pulse-ring bg-destructive/50" />
                      <Square className="w-6 h-6 relative z-10" />
                    </>
                  ) : (
                    <Mic className="w-6 h-6" />
                  )}
                </Button>
                
                <div className="flex-1 space-y-2">
                  <Textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Speak into the microphone or type your message here..."
                    className="min-h-[120px] bg-muted/30 border-border/50 resize-none text-foreground placeholder:text-muted-foreground/60 font-body text-base focus:border-primary/50 focus:ring-primary/20"
                  />
                  {isTranscribing && (
                    <div className="flex items-center gap-2 text-primary">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm font-medium">Transcribing audio...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                variant="hero"
                size="xl"
                className="flex-1"
                onClick={handleTranslateAndSpeak}
                disabled={isLoading || speaking || !inputText.trim()}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Translating...
                  </>
                ) : speaking ? (
                  <>
                    <SoundWave active={true} className="mr-2" />
                    Speaking...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    Translate & Speak
                  </>
                )}
              </Button>
              
              {speaking && (
                <Button
                  variant="outline"
                  size="xl"
                  onClick={cancel}
                  className="sm:w-auto"
                >
                  <Volume2 className="w-5 h-5" />
                  Stop Audio
                </Button>
              )}
            </div>
          </div>

          {/* Translation Result */}
          {translatedText && (
            <div className="mt-8 relative">
              <TranslationResult 
                originalText={inputText}
                translatedText={translatedText}
                targetLanguage={targetLanguage?.name || targetLang}
              />
            </div>
          )}
        </section>

        {/* Footer Stats */}
        <section className="mt-16 lg:mt-20">
          <div className="flex flex-wrap justify-center gap-8 lg:gap-16 text-center">
            <div className="animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
              <div className="text-3xl lg:text-4xl font-display font-bold text-gradient-primary">50+</div>
              <div className="text-sm text-muted-foreground mt-1">Languages Supported</div>
            </div>
            <div className="animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
              <div className="text-3xl lg:text-4xl font-display font-bold text-gradient-secondary">Real-time</div>
              <div className="text-sm text-muted-foreground mt-1">Speech Processing</div>
            </div>
            <div className="animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
              <div className="text-3xl lg:text-4xl font-display font-bold text-foreground">Neural</div>
              <div className="text-sm text-muted-foreground mt-1">Machine Translation</div>
            </div>
          </div>
        </section>

        {/* Info Section */}
        <section className="mt-12 lg:mt-16 max-w-3xl mx-auto text-center">
          <div className="glass-panel rounded-xl p-6 lg:p-8">
            <Languages className="w-10 h-10 text-primary mx-auto mb-4" />
            <h2 className="font-display text-xl lg:text-2xl font-semibold text-foreground mb-3">
              Contextual Memory Technology
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Our system incorporates a sliding-window contextual memory mechanism to preserve 
              semantic coherence across consecutive sentences. This improves pronoun resolution 
              and topic continuity, delivering more natural and accurate translations.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Index;
