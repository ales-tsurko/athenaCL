def divider():
    return { "type": "Divider" }

def paragraph(text):
    return { "type": "Paragraph", "params": text }

def header(text):
    return { "type": "Header", "params": text }

def list(items):
    return { "type": "List", "params": items }

def link(text, cmd, width=100):
    return {
            "type": "Link",
            "params": {
                "text": text,
                "width": width,
                "cmd": cmd
                }
            }
