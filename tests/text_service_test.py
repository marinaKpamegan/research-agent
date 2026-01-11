from app.services.text_service import extract_keywords, detect_language

text = "Je cherche une chanson triste des années 90"
print(detect_language(text))  # → 'fr'
print(extract_keywords(text)) # → ['cherche', 'chanson', 'triste', 'années']

