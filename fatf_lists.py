"""
FATF (Financial Action Task Force) Grey List
Source: FATF website (as of April 2023)
"""

# Countries on the FATF Grey List (Jurisdictions under Increased Monitoring)
FATF_GREY_LIST = [
    'AL',  # Albania
    'BB',  # Barbados
    'BF',  # Burkina Faso
    'BI',  # Burundi
    'BW',  # Botswana
    'CF',  # Central African Republic
    'DZ',  # Algeria
    'ES',  # El Salvador
    'GH',  # Ghana
    'HT',  # Haiti
    'JM',  # Jamaica
    'JO',  # Jordan
    'KH',  # Cambodia
    'MA',  # Morocco
    'ML',  # Mali
    'MU',  # Mauritius
    'MZ',  # Mozambique
    'NG',  # Nigeria
    'PK',  # Pakistan
    'PA',  # Panama
    'SD',  # Sudan
    'SN',  # Senegal
    'SY',  # Syria
    'TR',  # Turkey
    'UG',  # Uganda
    'YE',  # Yemen
    'ZW'   # Zimbabwe
]

# Convert to lowercase for case-insensitive matching
FATF_GREY_LIST_LOWER = [country.lower() for country in FATF_GREY_LIST]

# Countries on the FATF Black List (Call for Action)
FATF_BLACK_LIST = [
    'KP',  # North Korea
    'IR'   # Iran
]

# Convert to lowercase for case-insensitive matching
FATF_BLACK_LIST_LOWER = [country.lower() for country in FATF_BLACK_LIST]

# Function to check if a country is on the FATF lists
def is_fatf_listed(country_code: str) -> dict:
    """
    Check if a country is on the FATF Grey or Black list
    
    Args:
        country_code: Two-letter country code
        
    Returns:
        dict: Result with keys 'listed' (bool), 'list_type' (str or None), 'risk_score' (float 0-1)
    """
    country_code = country_code.upper()
    
    result = {
        'listed': False,
        'list_type': None,
        'risk_score': 0.0
    }
    
    if country_code in FATF_BLACK_LIST:
        result['listed'] = True
        result['list_type'] = 'Black List (Call for Action)'
        result['risk_score'] = 1.0
    elif country_code in FATF_GREY_LIST:
        result['listed'] = True
        result['list_type'] = 'Grey List (Increased Monitoring)'
        result['risk_score'] = 0.7
    
    return result
