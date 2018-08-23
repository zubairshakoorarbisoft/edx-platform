import os
import re
import pprint

ANNOTATION_STRING = ".. pii::"

rootDir = '..'

found_annotations = []

for dirname, _, files in os.walk(rootDir):
    # print('Found directory: %s' % dirname)
    for fname in files:
        if fname.lower().endswith('.py'):
            file_path = os.path.join(dirname, fname)
            with open(file_path, 'r') as f:
                # print('\t%s' % fname)
                lines = f.read()

                # Quick search since we're unlikely to find any
                if lines.find(ANNOTATION_STRING):
                    annotations_in_file = [match.start() for match in re.finditer(ANNOTATION_STRING, lines)]

                    for annotation_end_index in annotations_in_file:
                        line_start = lines.rfind('\n', 0, annotation_end_index)
                        line_end = lines.find('\n', annotation_end_index)
                        line_no = lines[:line_end].count("\n") + 1
                        found_annotations.append((file_path, line_no, lines[line_start:line_end].strip()))

pprint.pprint(found_annotations)
