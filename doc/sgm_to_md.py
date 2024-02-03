# converts the original documentation format (sgm) into markdown

import argparse

from bs4 import BeautifulSoup, NavigableString


def main():
    args = parse_args()
    content = read_doc(args.path)
    md = parse(content)
    with open(args.output, 'w') as file:
        file.write(md)

    
def parse_args():
    parser = argparse.ArgumentParser(description='sgm to md converter')
    parser.add_argument('-p', '--path', type=str, help='path to doc file (sgm format)')
    parser.add_argument('-o', '--output', type=str, help='output file')
    args = parser.parse_args()
    assert args.path, "path to the source file should be specified"
    assert args.output, "path to the output file should be specified"
    return args


def read_doc(path):
    with open(path, 'r') as file:
        return file.read()


def parse(content):
    soup = BeautifulSoup(content, 'html.parser')
    output = ""
    elements = soup.find_all(['chapter', 'preface'])
    children = [child for element in elements for child in element.children if not isinstance(child, NavigableString)]

    for element in children:
        match element.name:
            case "title":
                output += "# " + element.get_text() + "\n\n"
            case "para":
                output += element.get_text() + "\n"
            case "sect1":
                output = parse_sect(element, output)
            # case "graphic": # images are lost
                # output = parse_image(element, output)

    return output

def parse_sect(sect, output):
    for element in sect.children:
        match element.name:
            case "title":
                output += "\n\n\n## " + element.get_text() + "\n\n"
            case "para":
                output += element.get_text() + "\n"
            case "example":
                output = parse_example(element, output)
            # case "graphic":
                # output = parse_image(element, output)

    return output

def parse_example(example, output):
    for element in example.children:
        match element.name:
            case "title":
                output += "\n**" + element.get_text() + "**\n\n"
            case "screen":
                output += "```" + element.get_text() + "```\n\n"
            # case "graphic":
                # output = parse_image(element, output)
    return output

def parse_image(element, output):
    return output + "\n![](" + element["fileref"] + ")\n"

    
if __name__ == "__main__":
    main()
