import os
import argparse
import fnmatch

def parse_arguments():
    parser = argparse.ArgumentParser(description='Search for a word in files within a directory.')
    parser.add_argument('-d', '--directory', type=str, help='Directory path to search in')
    parser.add_argument('-w', '--word', type=str, help='Word or wildcard pattern to search for in files')
    parser.add_argument('-e', '--extensions', nargs='+', default=['.html', '.txt'], help='File extensions to search within')
    parser.add_argument('-o', '--output', type=str, help='Output file path to save results')
    parser.add_argument('-r', '--recursive', action='store_true', help='Perform a recursive search within subdirectories')
    parser.add_argument('-c', '--context', action='store_true', help='Display context around occurrences of the word in files')
    return parser.parse_args()

def search_word_in_files(directory, word, extensions, recursive, display_context):
    found_files = []
    # Determine whether to perform a recursive search
    if recursive:
        walk_method = os.walk(directory)
    else:
        walk_method = [(directory, [], files) for _, _, files in os.walk(directory)]
    # Iterate through all files and directories in the given directory
    for root, dirs, files in walk_method:
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(tuple(extensions)):
                # Open the file and search for the word
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line in lines:
                        if fnmatch.fnmatch(line, '*' + word):
                            found_files.append((file_path, line))
                            break
    return found_files

def main():
    args = parse_arguments()
    directory_to_search = args.directory
    word_to_find = args.word
    output_file = args.output
    extensions = args.extensions
    recursive_search = args.recursive
    display_context = args.context
    
    if not directory_to_search or not word_to_find:
        print("Error: Both directory and word arguments are required.")
        return
    
    found_files = search_word_in_files(directory_to_search, word_to_find, extensions, recursive_search, display_context)
    
    if output_file:
        with open(output_file, 'w') as f:
            for file_path, _ in found_files:
                f.write(file_path + '\n')
        print("Results saved to", output_file)
    elif found_files:
        for file_path, content in found_files:
            print("Found '{}' in file: {}".format(word_to_find, file_path))
            if display_context:
                print("Context:")
                # Split content into lines and find the line containing the word
                lines = content.split('\n')
                for line in lines:
                    if fnmatch.fnmatch(line, '*' + word_to_find + '*'):
                        print(line)
                print()
        print("Total files found:", len(found_files))
    else:
        print("No files containing '{}' were found.".format(word_to_find))

if __name__ == "__main__":
    main()
