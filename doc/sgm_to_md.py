# converts the original documentation format (sgm) into markdown

import argparse
import re

from bs4 import BeautifulSoup, NavigableString

index = 0

def main():
    args = parse_args()
    content = read_doc(args.path)
    make_files(content)

    
def parse_args():
    parser = argparse.ArgumentParser(description='sgm to md converter')
    parser.add_argument('-p', '--path', type=str, help='path to doc file (sgm format)')
    args = parser.parse_args()
    assert args.path, "path to the source file should be specified"
    return args


def read_doc(path):
    with open(path, 'r') as file:
        return file.read()


def make_files(content):
    soup = BeautifulSoup(content, 'html.parser')
    output = ""
    elements = soup.find_all(['chapter', 'preface'])
    children = [child for element in elements for child in element.children if not isinstance(child, NavigableString)]
    filename = ""
    
    for element in children:
        match element.name:
            case "title":
                output += "# " + element.get_text() + "\n\n"
                filename = make_filename(element.get_text())
            case "para":
                output += element.get_text() + "\n"
            case "sect1":
                save_part(element)

    with open(filename, 'w') as file:
        file.write(output)

        
def make_filename(title):
    global index
    index += 1
    return "0" + str(index) + "-" + re.sub(r'[^\w\s]', '',
                                title).lower().replace(" ", "-") + ".md"
    

def save_part(sect):
    output = ""
    filename = ""
    for element in sect.children:
        match element.name:
            case "title":
                title = element.get_text()
                output += "## " + title + "\n\n"
                filename = make_filename(title)
            case "para":
                output += element.get_text() + "\n"
            case "example":
                output = parse_example(element, output)

    with open(filename, 'w') as file:
        file.write(output)

        
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
