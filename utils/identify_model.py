import re

def _extract_model(text: str, prefix: str) -> str:
    """
    Extrai provável modelo da string de descrição.
    Exemplo: "hp laserjet 1020 series" -> "HP LaserJet 1020"
    """
    try:
        # Remove excesso de espaços
        clean_text = re.sub(r"\s+", " ", text).strip()
        
        # Tenta pegar algo como "laserjet 1020", "mfc-9340cdw", etc.
        match = re.search(r"([a-z]*\s?\d{3,5}[a-z\-]*)", clean_text, re.IGNORECASE)
        if match:
            return f"{prefix} {match.group(1).title()}"
        return prefix
    except Exception:
        return prefix


def detect_printer_model(printer_name: str, share_name: str = "",
                         driver_name: str = "", comment: str = "") -> str:
    """
    Detecta modelo provável da impressora baseado em nome, compartilhamento, driver ou descrição.
    Retorna string com modelo identificado ou 'Desconhecido'.
    """
    try:
        fields = [printer_name, share_name, driver_name, comment]
        for field in fields:
            if field:
                # Normaliza para facilitar regex
                normalized = field.strip().lower()
                
                # Exemplos de padrões comuns de fabricantes
                if "hp" in normalized or "hewlett-packard" in normalized:
                    return _extract_model(normalized, prefix="HP") # type: ignore
                if "canon" in normalized:
                    return _extract_model(normalized, prefix="Canon") # type: ignore
                if "epson" in normalized:
                    return _extract_model(normalized, prefix="Epson") # type: ignore
                if "brother" in normalized:
                    return _extract_model(normalized, prefix="Brother") # type: ignore
                if "samsung" in normalized:
                    return _extract_model(normalized, prefix="Samsung") # type: ignore
                if "lexmark" in normalized:
                    return _extract_model(normalized, prefix="Lexmark") # type: ignore

        return "Desconhecido"
    except Exception as e:
        print(f"Falha ao detectar modelo da impressora: {e}")
        return "Desconhecido"
