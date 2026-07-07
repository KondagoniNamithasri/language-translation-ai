
from flask import Blueprint, request, jsonify
from services.translation_service import TranslationService

translation_bp = Blueprint('translation', __name__)
translation_service = TranslationService()

@translation_bp.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        text = data.get('text')
        
        # Map frontend language codes to mBART language codes
        # Supports all 50 languages from mBART-50 many-to-many model
        language_map = {
            'af': 'af_ZA',  # Afrikaans
            'ar': 'ar_AR',  # Arabic
            'az': 'az_AZ',  # Azerbaijani
            'bn': 'bn_IN',  # Bengali
            'cs': 'cs_CZ',  # Czech
            'de': 'de_DE',  # German
            'en': 'en_XX',  # English
            'es': 'es_XX',  # Spanish
            'et': 'et_EE',  # Estonian
            'fa': 'fa_IR',  # Persian
            'fi': 'fi_FI',  # Finnish
            'fr': 'fr_XX',  # French
            'gl': 'gl_ES',  # Galician
            'gu': 'gu_IN',  # Gujarati
            'he': 'he_IL',  # Hebrew
            'hi': 'hi_IN',  # Hindi
            'hr': 'hr_HR',  # Croatian
            'id': 'id_ID',  # Indonesian
            'it': 'it_IT',  # Italian
            'ja': 'ja_XX',  # Japanese
            'ka': 'ka_GE',  # Georgian
            'kk': 'kk_KZ',  # Kazakh
            'km': 'km_KH',  # Khmer
            'ko': 'ko_KR',  # Korean
            'lt': 'lt_LT',  # Lithuanian
            'lv': 'lv_LV',  # Latvian
            'mk': 'mk_MK',  # Macedonian
            'ml': 'ml_IN',  # Malayalam
            'mn': 'mn_MN',  # Mongolian
            'mr': 'mr_IN',  # Marathi
            'my': 'my_MM',  # Burmese
            'ne': 'ne_NP',  # Nepali
            'nl': 'nl_XX',  # Dutch
            'pl': 'pl_PL',  # Polish
            'ps': 'ps_AF',  # Pashto
            'pt': 'pt_XX',  # Portuguese
            'ro': 'ro_RO',  # Romanian
            'ru': 'ru_RU',  # Russian
            'si': 'si_LK',  # Sinhala
            'sl': 'sl_SI',  # Slovene
            'sv': 'sv_SE',  # Swedish
            'sw': 'sw_KE',  # Swahili
            'ta': 'ta_IN',  # Tamil
            'te': 'te_IN',  # Telugu
            'th': 'th_TH',  # Thai
            'tl': 'tl_XX',  # Tagalog
            'tr': 'tr_TR',  # Turkish
            'uk': 'uk_UA',  # Ukrainian
            'ur': 'ur_PK',  # Urdu
            'vi': 'vi_VN',  # Vietnamese
            'xh': 'xh_ZA',  # Xhosa
            'zh': 'zh_CN',  # Chinese
        }
        
        target_lang = language_map.get(data.get('target_lang', 'en'), 'en_XX')
        source_lang = language_map.get(data.get('source_lang', 'en'), 'en_XX')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        result = translation_service.translate(text, source_lang, target_lang)
        
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
