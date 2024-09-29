def divider():
    return { "type": "Divider" }

def paragraph(text):
    return { "type": "Paragraph", "params": text }

def header(text):
    return { "type": "Header", "params": text }

def row(items):
    return { "type": "Row", "params": items }

def link(text, cmd):
    return {
            "type": "Link",
            "params": {
                "text": text,
                "cmd": cmd
                }
            }
