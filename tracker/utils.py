import unicodedata

# Comprehensive mapping of country names (in Spanish, lowercase, without accents) to their flag emojis
COUNTRY_FLAGS = {
    # América
    "argentina": "🇦🇷", "bolivia": "🇧🇴", "brasil": "🇧🇷", "chile": "🇨🇱", "colombia": "🇨🇴",
    "ecuador": "🇪🇨", "paraguay": "🇵🇾", "peru": "🇵🇪", "uruguay": "🇺🇾", "venezuela": "🇻🇪",
    "mexico": "🇲🇽", "costa rica": "🇨🇷", "el salvador": "🇸🇻", "guatemala": "🇬🇹",
    "honduras": "🇭🇳", "nicaragua": "🇳🇮", "panama": "🇵🇦", "cuba": "🇨🇺",
    "republica dominicana": "🇩🇴", "puerto rico": "🇵🇷", "haiti": "🇭🇹", "canada": "🇨🇦",
    "estados unidos": "🇺🇸", "jamaica": "🇯🇲", "bahamas": "🇧🇸", "barbados": "🇧🇧",
    "trinidad y tobago": "🇹🇹", "curazao": "🇨🇼", "aruba": "🇦🇼", "surinam": "🇸🇷",
    "guyana": "🇬🇾",
    
    # Europa
    "espana": "🇪🇸", "portugal": "🇵🇹", "francia": "🇫🇷", "italia": "🇮🇹",
    "alemania": "🇩🇪", "reino unido": "🇬🇧", "inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "escocia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "gales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "irlanda del norte": "🇬🇧", "irlanda": "🇮🇪", "belgica": "🇧🇪",
    "paises bajos": "🇳🇱", "suiza": "🇨🇭", "austria": "🇦🇹", "grecia": "🇬🇷",
    "dinamarca": "🇩🇰", "suecia": "🇸🇪", "noruega": "🇳🇴", "finlandia": "🇫🇮",
    "islandia": "🇮🇸", "polonia": "🇵🇱", "republica checa": "🇨🇿", "chequia": "🇨🇿",
    "eslovaquia": "🇸🇰", "hungria": "🇭🇺", "rumania": "🇷🇴", "bulgaria": "🇧🇬",
    "croacia": "🇭🇷", "serbia": "🇷🇸", "eslovenia": "🇸🇮", "bosnia y herzegovina": "🇧🇦",
    "montenegro": "🇲🇪", "macedonia del norte": "🇲🇰", "albania": "🇦🇱", "ucrania": "🇺🇦",
    "bielorrusia": "🇧🇾", "rusia": "🇷🇺", "turquia": "🇹🇷", "georgia": "🇬🇪",
    "armenia": "🇦🇲", "azerbaiyan": "🇦🇿", "chipre": "🇨🇾", "malta": "🇲🇹",
    "estonia": "🇪🇪", "letonia": "🇱🇻", "lituania": "🇱🇹", "moldavia": "🇲🇩",
    
    # Asia
    "japon": "🇯🇵", "corea del sur": "🇰🇷", "corea del norte": "🇰🇵", "china": "🇨🇳",
    "taiwan": "🇹🇼", "india": "🇮🇳", "pakistan": "🇵🇰", "bangladesh": "🇧🇩",
    "sri lanka": "🇱🇰", "nepal": "🇳🇵", "vietnam": "🇻🇳", "tailandia": "🇹🇭",
    "malasia": "🇲🇾", "singapur": "🇸🇬", "indonesia": "🇮🇩", "filipinas": "🇵🇭",
    "arabia saudita": "🇸🇦", "emiratos arabes unidos": "🇦🇪", "catar": "🇶🇦", "qatar": "🇶🇦",
    "kuwait": "🇰🇼", "oman": "🇴🇲", "barein": "🇧🇭", "yemen": "🇾🇪",
    "irak": "🇮🇶", "iran": "🇮🇷", "siria": "🇸🇾", "jordania": "🇯🇴",
    "libano": "🇱🇧", "israel": "🇮🇱", "palestina": "🇵🇸", "afganistan": "🇦🇫",
    "uzbekistan": "🇺🇿", "kazajistan": "🇰🇿", "turkmenistan": "🇹🇲", "kirguistan": "🇰🇬",
    "tayikistan": "🇹🇯", "mongolia": "🇲🇳",
    
    # África
    "egipto": "🇪🇬", "sudafrica": "🇿🇦", "marruecos": "🇲🇦", "argelia": "🇩🇿",
    "tunez": "🇹🇳", "libia": "🇱🇾", "sudan": "🇸🇩", "nigeria": "🇳🇬",
    "ghana": "🇬🇭", "senegal": "🇸🇳", "camerun": "🇨🇲", "costa de marfil": "🇨🇮",
    "rd del congo": "🇨🇩", "republica democratica del congo": "🇨🇩", "congo": "🇨🇬",
    "kenia": "🇰🇪", "etiopia": "🇪🇹", "tanzania": "🇹🇿", "uganda": "🇺🇬",
    "angola": "🇦🇴", "mozambique": "🇲🇿", "zambia": "🇿🇲", "zimbabue": "🇿🇼",
    "namibia": "🇳🇦", "botsuana": "🇧🇼", "madagascar": "🇲🇬", "cabo verde": "🇨🇻",
    "mali": "🇲🇱", "niger": "🇳🇪", "burkina faso": "🇧🇫", "togo": "🇹🇬",
    "benin": "🇧🇯", "guinea": "🇬🇳", "liberia": "🇱🇷", "sierra leona": "🇸🇱",
    "gambia": "🇬🇲", "guinea-bisau": "🇬🇼", "gabon": "🇬🇦", "eritrea": "🇪🇷",
    "somalia": "🇸🇴", "yibuti": "🇩🇯", "ruanda": "🇷🇼", "burundi": "🇧🇮",
    "malaui": "🇲🇼",
    
    # Oceanía
    "australia": "🇦🇺", "nueva zelanda": "🇳🇿", "fiyi": "🇫🇯", "papua nueva guinea": "🇵🇬",
    "samoa": "🇼🇸", "tonga": "🇹🇴", "vanuatu": "🇻🇺", "islas salomon": "🇸🇧"
}

def normalize_name(name):
    """
    Normaliza el nombre del país para búsqueda: minúsculas, sin espacios al inicio/fin,
    y removiendo acentos/diacríticos.
    """
    if not name:
        return ""
    # Strip spaces and convert to lower
    name = name.strip().lower()
    # Normalize to decompose accents/diacritics, then filter them out
    normalized = unicodedata.normalize('NFD', name)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

def get_flag_emoji(country_name):
    """
    Retorna el emoji de la bandera correspondiente al nombre del país en español.
    Si no se encuentra, retorna una bandera blanca genérica '🏳️'.
    """
    norm = normalize_name(country_name)
    return COUNTRY_FLAGS.get(norm, "🏳️")
