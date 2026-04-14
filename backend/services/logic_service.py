import re
import random

class LogicService:
    def __init__(self):
        self.templates = {
            "hi-IN": {
                "greeting": ["नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?", "हैلو! आप कैसे हैं?"],
                "balance": ["आपका वर्तमान बैलेंस ₹5000 है।", "आपके खाते में ₹5000 शेष हैं।"],
                "unknown": ["माफ़ कीजिये, मुझे समझ नहीं आया।", "क्या आप फिर से कह सकते हैं?"]
            },
            "ta-IN": {
                "greeting": ["வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?", "ஹலோ! நீங்கள் எப்படி இருக்கிறீர்கள்?"],
                "balance": ["உங்கள் தற்போதைய இருப்பு ₹5000 ஆகும்.", "உங்கள் கணக்கில் ₹5000 உள்ளது."],
                "unknown": ["மன்னிக்கவும், எனக்கு புரியவில்லை.", "தயవుசெய்து மீண்டும் சொல்ல முடியுமா?"]
            },
            "en-IN": {
                "greeting": ["Hello! How can I help you today?", "Hi there! How are you?"],
                "balance": ["Your current balance is ₹5000.", "You have ₹5000 in your account."],
                "unknown": ["Sorry, I didn't quite catch that.", "Could you please repeat?"]
            },
            "bn-IN": {
                "greeting": ["নমস্কার! আমি আপনাকে কীভাবে সাহায্য করতে পারি?"],
                "balance": ["আপনার বর্তমান ব্যালেন্স হল ₹৫০০০।"],
                "unknown": ["দুঃখিত, আমি বুঝতে পারিনি।"]
            },
            "te-IN": {
                "greeting": ["నమస్కారం! నేను మీకు ఎలా సహాయం చేయగలను?"],
                "balance": ["మీ ప్రస్తుత బ్యాలెన్స్ ₹5000."],
                "unknown": ["క్షమించండి, నాకు అర్థం కాలేదు."]
            },
            "kn-IN": {
                "greeting": ["ನಮಸ್ಕಾರ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"],
                "balance": ["ನಿಮ್ಮ ಪ್ರಸ್ತುత ಬ್ಯಾಲೆನ್ಸ್ ₹5000."],
                "unknown": ["ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ."]
            },
            "gu-IN": {
                "greeting": ["નમસ્તે! હું તમારી શું મદદ કરી શકું?"],
                "balance": ["તમારું વર્તમાન બેલેન્સ ₹5000 છે."],
                "unknown": ["ક્ષમા કરશો, મને સમજાયું નહીં."]
            },
            "mr-IN": {
                "greeting": ["नमस्कार! मी तुम्हाला कशी मदत करू शकतो?"],
                "balance": ["तुमची सध्याची शिल्लक ₹५००० आहे."],
                "unknown": ["क्षमस्व, मला समजले नाही."]
            },
            "pa-IN": {
                "greeting": ["ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"],
                "balance": ["ਤੁਹਾਡਾ ਮੌਜੂਦਾ ਬੈਲੇਂਸ ₹5000 ਹੈ।"],
                "unknown": ["ਮੁਆਫ ਕਰਨਾ, ਮੈਨੂੰ ਸਮਝ نہیں ਆਇਆ।"]
            },
            "ml-IN": {
                "greeting": ["നമസ്കാരം! എനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാനാകും?"],
                "balance": ["നിങ്ങളുടെ നിലവിലെ ബാലൻസ് ₹5000 ആണ്."],
                "unknown": ["ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല."]
            },
            "od-IN": {
                "greeting": ["ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ្យ କରିପାରିବି?"],
                "balance": ["ଆପଣଙ୍କର ବର୍ତ୍ତମାନର ବାଲାନ୍ସ ₹5000 ଅଟେ।"],
                "unknown": ["ଦୟାକରି କ୍ଷମା କରିବେ, ମୁଁ ବୁଝିପାରିଲି ନାହିଁ।"]
            },
            "as-IN": {
                "greeting": ["নমস্কাৰ! মই আপোনাক কেনেকৈ সহায় কৰিব পাৰোঁ?"],
                "balance": ["আপোনাৰ বৰ্তমানৰ বেলেঞ্চ ৫০০৩ টকা।"],
                "unknown": ["ক্ষমা কৰিব, মই বুজি পোৱা নাই।"]
            },
            "ur-IN": {
                "greeting": ["آداب! میں آپ کی کیا مدد کر سکتا ہوں؟"],
                "balance": ["آپ کا موجودہ بیلنس 5000 روپے ہے۔"],
                "unknown": ["معذرت، میں سمجھ نہیں سکا۔"]
            },
            "ne-IN": {
                "greeting": ["नमस्ते! म तपाईंलाई कसरी सहयोग गर्न सक्छु?"],
                "balance": ["तपाईंको वर्तमान ब्यालेన్స్ ₹५००० छ।"],
                "unknown": ["माफ गर्नुहोस्, मैले बुझिन।"]
            },
            "kok-IN": {
                "greeting": ["नमस्कार! हांव तुमकां कशी मदत करूं शकता?"],
                "balance": ["तुमचें सध्याचें बॅलन्स ₹5000 आसा."],
                "unknown": ["माफ करा, म्हाका समजलें ना."]
            },
            "ks-IN": {
                "greeting": ["नमस्कार! बह क्या छिथ करन मुदत?"],
                "balance": ["थवव बैलेंस छु 5000 रुपय."],
                "unknown": ["माफ करिव, बह समजुनस न."]
            },
            "sd-IN": {
                "greeting": ["نمستي! مان توهان جي ڪيئن مدد ڪري سگهان ٿو؟"],
                "balance": ["توهان جي موجوده بقايا 5000 رپيا آهي."],
                "unknown": ["معاف ڪجو، مان سمجهي نه سگهيس."]
            },
            "sa-IN": {
                "greeting": ["नमस्ते! अहं कथं साहाय्यं कर्तुं शक्नोमि?"],
                "balance": ["भवतः वर्तमानं शेषधनं ५००० रुप्यकाणि अस्ति।"],
                "unknown": ["क्षम्यताम्, अहं न अवगतवान्।"]
            },
            "sat-IN": {
                "greeting": ["Johar! In jaha leka dhorom dake?"],
                "balance": ["Amak balance do 5000 taka kana."],
                "unknown": ["Ikạ kaṇ me, iń bạń bujhạu le-a."]
            },
            "mni-IN": {
                "greeting": ["Khurumjari! Ei nangonda karamna mateng pangba ngagani?"],
                "balance": ["Nangi balance adu lupa 5000 ni."],
                "unknown": ["Ngakpa kani, ei khunghandey."]
            },
            "brx-IN": {
                "greeting": ["Kulumba! आं नोंथांखौ माबोरै हेफाजाब होनो हागौ?"],
                "balance": ["नोंथांनि दासिमनि बेलेन्सआ 5000 रां।"],
                "unknown": ["निमाहा बिनो, आं बुजिबोनाय नङा।"]
            },
            "mai-IN": {
                "greeting": ["प्रणाम! हम अहाँक की सहायता कऽ सकैत छी?"],
                "balance": ["अहाँक वर्तमान बैलेंस ₹५००० अछि।"],
                "unknown": ["क्षमा करब, हम नहि बुझि सकलहुँ।"]
            },
            "doi-IN": {
                "greeting": ["नमस्ते! मैं थुंदी की मदद करी सकदा हां?"],
                "balance": ["थुंदा मौजूदा बैलेंस ₹5000 ऐ।"],
                "unknown": ["माफ करना, मैंन्नी समझ नहीं आया।"]
            }
        }
        
        # Supported language list
        self.supported_languages = list(self.templates.keys())

    def detect_intent(self, text: str):
        text = text.lower()
        if any(w in text for w in ["balance", "पैसे", "बैलेंस", "இருப்பு", "বেলেঞ্চ", "ব্যাবালেন্স"]):
            return "balance"
        if any(w in text for w in ["hello", "नमस्ते", "வணக்கம்", "hi", "নমস্কার", "נמסטה"]):
            return "greeting"
        return "unknown"

    def normalize_hinglish(self, text: str):
        return text.strip()

    def generate_response(self, text: str, lang: str = "hi-IN"):
        # Default to hi-IN if lang not specified or not supported
        if lang not in self.templates:
            lang = "hi-IN"
        
        intent = self.detect_intent(text)
        responses = self.templates[lang][intent]
        
        return random.choice(responses), lang

logic_service = LogicService()
