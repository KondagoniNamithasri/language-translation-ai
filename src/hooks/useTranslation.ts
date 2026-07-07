import { useState, useCallback } from 'react';

export const useTranslation = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const translate = useCallback(async (text: string, targetLang: string, sourceLang: string = 'en') => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://127.0.0.1:5000/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          target_lang: targetLang,
          source_lang: sourceLang,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Translation failed');
      }

      return data.translation;
    } catch (err) {
      console.error('Translation error:', err);
      const message = err instanceof Error ? err.message : 'Translation failed';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { translate, isLoading, error };
};
