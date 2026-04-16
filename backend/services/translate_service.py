import os
from sarvamai import SarvamAI
from dotenv import load_dotenv

load_dotenv()

class TranslateService:
    """
    Service for high-fidelity translation using Sarvam AI's Mayura model.
    Optimized for Indian language nuances.
    """
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.client = None
        if self.api_key:
            # We initialize a synchronous client for simple blocking calls if needed, 
            # or we can use async if the SDK supports it.
            self.client = SarvamAI(api_subscription_key=self.api_key)
            print("TranslateService: Initialized with Sarvam Mayura")
        else:
            print("TranslateService: WARNING - No API key found")

    def translate_text(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str = "en-IN",
        mode: str = "formal"
    ) -> str:
        """
        Translates text from source to target language.
        
        Args:
            text: Input string (max ~5000 chars recommended)
            target_lang: BCP-47 destination language code
            source_lang: BCP-47 source language code (defaults to en-IN)
            mode: 'formal', 'classic-colloquial', or 'modern-colloquial'
        """
        if not self.client:
            return f"Error: TranslateService not initialized. Orig text: {text[:50]}..."

        try:
            # Note: The translate API might vary slightly by SDK version,
            # but standard usage is client.text.translate
            response = self.client.text.translate(
                input=text,
                source_language_code=source_lang,
                target_language_code=target_lang,
                model="mayura:v1",
                # mode=mode # Mayura supports modes like formal/colloquial
            )
            
            # Extract translated text from response structure
            if hasattr(response, 'translated_text'):
                return response.translated_text
            elif isinstance(response, dict) and 'translated_text' in response:
                return response['translated_text']
            
            return str(response)
        except Exception as e:
            print(f"TranslateService: Translation failed: {e}")
            return f"Error translating: {str(e)}"

# Singleton instance
translate_service = TranslateService()
