import xml.etree.ElementTree as ET


def remove_namespace(xml):
	it = ET.iterparse(xml)
	for _, el in it:
	    if '}' in el.tag:
	        el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
	root = it.root
	return root

def banner(text, ch='=', length=78):
    spaced_text = ' %s ' % text
    banner = spaced_text.center(length, ch)
    return banner	







