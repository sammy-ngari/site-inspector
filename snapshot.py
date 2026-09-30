import os

# Define folders and files to completely ignore
IGNORE_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env', 
    'build', 'dist', '.next', 'out', '.idea', '.vscode'
}
IGNORE_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', '.DS_Store', 
    'bundle_project.py', 'project_context.txt'
}
# Supported text/code extensions to read
VALID_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.html', '.css', 
    '.md', '.env', 'Dockerfile', 'requirements.txt'
}

def generate_tree(dir_path, prefix=""):
    """Generates a text-based visual directory tree."""
    tree_lines = []
    try:
        items = sorted(os.listdir(dir_path))
    except PermissionError:
        return []
        
    items = [i for i in items if i not in IGNORE_DIRS and i not in IGNORE_FILES]
    
    for i, item in enumerate(items):
        path = os.path.join(dir_path, item)
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        
        if os.path.isdir(path):
            tree_lines.append(f"{prefix}{connector}{item}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            tree_lines.extend(generate_tree(path, new_prefix))
        else:
            _, ext = os.path.splitext(item)
            if ext in VALID_EXTENSIONS or item in VALID_EXTENSIONS:
                tree_lines.append(f"{prefix}{connector}{item}")
    return tree_lines

def bundle_codebase(root_dir, output_file):
    """Gathers directory structure and file contents into one file."""
    with open(output_file, 'w', encoding='utf-8') as out:
        # 1. Write the visual tree structure
        out.write("=== DIRECTORY STRUCTURE ===\n")
        out.write(os.path.basename(os.path.abspath(root_dir)) + "/\n")
        tree = generate_tree(root_dir)
        out.write("\n".join(tree) + "\n\n")
        
        # 2. Append content of each valid file
        for root, dirs, files in os.walk(root_dir):
            # Modifying dirs in-place filters out ignored directories from os.walk
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in sorted(files):
                if file in IGNORE_FILES:
                    continue
                    
                _, ext = os.path.splitext(file)
                if ext in VALID_EXTENSIONS or file in VALID_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    
                    out.write(f"=========================================\n")
                    out.write(f"=== FILE: {rel_path} ===\n")
                    out.write(f"=========================================\n")
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            out.write(f.read() + "\n\n")
                    except Exception as e:
                        out.write(f"[Error reading file: {str(e)}]\n\n")

if __name__ == "__main__":
    current_directory = os.getcwd()
    output_filename = "project_context.txt"
    print(f"Bundling project from: {current_directory}")
    bundle_codebase(current_directory, output_filename)
    print(f"Done! Created '{output_filename}'. Upload this file to your ChatGPT Project.")
