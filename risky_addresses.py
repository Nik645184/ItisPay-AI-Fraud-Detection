"""
Lists of known risky Ethereum addresses.
These are examples and would need to be updated regularly in a production system.
A real system would connect to specialized services like Chainalysis or TRM Labs.
"""

# Known mixer services (example addresses, these are just for demonstration)
KNOWN_MIXER_ADDRESSES = {
    '0x8589427373d6d84e98730d7795d8f6f8731fda16',  # Tornado Cash (example)
    '0x722122df12d4e14e13ac3b6895a86e84145b6967',  # Tornado Cash (example)
    '0xd90e2f925da726b50c4ed8d0fb90ad053324f31b',  # Tornado Cash (example)
    '0xd96f2b1c14db8458374d9aca76e26c3d18364307',  # Tornado Cash (example)
    '0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d',  # Example mixer
    '0x169ad27a470d064dede56a2d3ff727986b15d52b',  # Example mixer
    '0x0836222f2b2b24a3f36f98668ed8f0b38d1a872f',  # Example mixer
    '0xf67721a2d8f736e75a49fdd7fad2e31d8676542a',  # Example mixer
    '0x9ad122c22b14202b4490edaf288fdb3c7cb3ff5e',  # Example mixer
}

# Known darknet market addresses (examples for demonstration)
KNOWN_DARKNET_ADDRESSES = {
    '0x3cbded43efdaf0fc77b9c55f6fc9988fcc9b757d',  # Example darknet market
    '0x2c7f66c0e2c62c6386a9b526a6cf546577d9d865',  # Example darknet market
    '0x33f4f55f3a427f2f1d1c2f11bbc2fd06a3ea9f46',  # Example darknet market
    '0xbc830d54ed5e9e26d3a30d71a1e8dc6d42860345',  # Example darknet market
    '0x67fa2c06c9c6d4332f330e14a66bdf1873ef3d2b',  # Example darknet market
    '0x9cb4b8297548f3be359f7ddf4302af6d2288e08f',  # Example darknet market
    '0x9cb4b8297548f3be359f7ddf4302af6d2288e09t',  # Example darknet market
}

# Known scam addresses (examples for demonstration)
KNOWN_SCAM_ADDRESSES = {
    '0x1446d6a152245d26f79082202bcd8a8a34967f4b',  # Example scam
    '0x9e4c14403d7d9a499dc5d293f486926b7876b1a6',  # Example scam
    '0x3f17f1962b36e491b30a40b2405849e597ba5fb5',  # Example scam
    '0x4686a963fad842745afd3c45e622dfefd201a73a',  # Example scam
    '0x8c9b261faef3b3c2e64ab5e58e04615f8c788099',  # Example scam
}

# Combined dictionary with risk scores
RISKY_ADDRESSES_WITH_SCORES = {}

# Add mixer addresses with high risk score
for addr in KNOWN_MIXER_ADDRESSES:
    RISKY_ADDRESSES_WITH_SCORES[addr] = {
        'type': 'mixer',
        'risk_score': 0.9,
        'description': 'Known cryptocurrency mixer service'
    }

# Add darknet addresses with highest risk score
for addr in KNOWN_DARKNET_ADDRESSES:
    RISKY_ADDRESSES_WITH_SCORES[addr] = {
        'type': 'darknet',
        'risk_score': 1.0,
        'description': 'Known darknet market'
    }

# Add scam addresses with high risk score
for addr in KNOWN_SCAM_ADDRESSES:
    RISKY_ADDRESSES_WITH_SCORES[addr] = {
        'type': 'scam',
        'risk_score': 0.85,
        'description': 'Known scam or fraud address'
    }

def check_address_risk(address: str) -> dict:
    """
    Check if an address is known risky and return risk information
    
    Args:
        address: Ethereum address to check
        
    Returns:
        dict: Risk information or None if not found
    """
    address_lower = address.lower()
    return RISKY_ADDRESSES_WITH_SCORES.get(address_lower)
