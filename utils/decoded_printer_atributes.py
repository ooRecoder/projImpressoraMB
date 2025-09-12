from typing import List
def decode_printer_attributes(attributes: int) -> List[str]:
    """Decodifica as flags de atributos da impressora"""
    flags = {
        1: "PRINTER_ATTRIBUTE_QUEUED",
        2: "PRINTER_ATTRIBUTE_DIRECT", 
        4: "PRINTER_ATTRIBUTE_DEFAULT",
        8: "PRINTER_ATTRIBUTE_SHARED",
        16: "PRINTER_ATTRIBUTE_NETWORK",
        32: "PRINTER_ATTRIBUTE_HIDDEN",
        64: "PRINTER_ATTRIBUTE_LOCAL",
        128: "PRINTER_ATTRIBUTE_ENABLE_DEVQ",
        256: "PRINTER_ATTRIBUTE_KEEPPRINTEDJOBS",
        512: "PRINTER_ATTRIBUTE_DO_COMPLETE_FIRST",
        1024: "PRINTER_ATTRIBUTE_WORK_OFFLINE",
        2048: "PRINTER_ATTRIBUTE_ENABLE_BIDI",
        4096: "PRINTER_ATTRIBUTE_RAW_ONLY",
        8192: "PRINTER_ATTRIBUTE_PUBLISHED",
        16384: "PRINTER_ATTRIBUTE_FAX",
        32768: "PRINTER_ATTRIBUTE_PUSHED_USER",
        65536: "PRINTER_ATTRIBUTE_PUSHED_MACHINE",
        131072: "PRINTER_ATTRIBUTE_MACHINE",
        262144: "PRINTER_ATTRIBUTE_FRIENDLY_NAME",
        8388608: "PRINTER_ATTRIBUTE_IPP/WSD_SPECIFIC"
    }
    
    active_flags = []
    for flag_value, flag_name in flags.items():
        if attributes & flag_value:
            active_flags.append(flag_name)
    
    return active_flags

if __name__ == "__main__":
    attributes = 8388608
    decoded = decode_printer_attributes(attributes)
    print(f"Atributos {attributes}: {decoded}")