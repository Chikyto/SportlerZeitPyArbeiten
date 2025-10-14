#!/usr/bin/env python3
"""
Script para generar árbol de archivos del proyecto
Ejecutar: python generate_tree.py
"""
import os
from pathlib import Path

# Directorios y archivos a ignorar
IGNORE_DIRS = {
    '__pycache__', 
    'venv', 
    '.git', 
    '.vscode',
    'node_modules',
    '.pytest_cache',
    '.idea',
    'build',
    'dist',
    '*.egg-info'
}

IGNORE_FILES = {
    '.DS_Store',
    'Thumbs.db',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.Python',
}

def should_ignore(path: Path) -> bool:
    """Verificar si un path debe ignorarse"""
    # Ignorar directorios
    for part in path.parts:
        if part in IGNORE_DIRS or part.startswith('.'):
            return True
    
    # Ignorar archivos
    if path.name in IGNORE_FILES:
        return True
    
    # Ignorar extensiones
    if path.suffix in ['.pyc', '.pyo', '.pyd']:
        return True
    
    return False

def generate_tree(directory: Path, prefix: str = "", output_lines: list = None, max_depth: int = 5, current_depth: int = 0):
    """
    Genera árbol de archivos recursivamente
    
    Args:
        directory: Directorio raíz
        prefix: Prefijo para indentación
        output_lines: Lista para acumular líneas
        max_depth: Profundidad máxima
        current_depth: Profundidad actual
    """
    if output_lines is None:
        output_lines = []
    
    if current_depth >= max_depth:
        return output_lines
    
    try:
        # Obtener todos los items del directorio
        items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        
        # Filtrar items ignorados
        items = [item for item in items if not should_ignore(item)]
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            
            # Símbolos del árbol
            if is_last:
                line_prefix = "└── "
                child_prefix = "    "
            else:
                line_prefix = "├── "
                child_prefix = "│   "
            
            # Agregar item actual
            if item.is_dir():
                output_lines.append(f"{prefix}{line_prefix}{item.name}/")
                # Recursión para subdirectorios
                generate_tree(
                    item, 
                    prefix + child_prefix, 
                    output_lines,
                    max_depth,
                    current_depth + 1
                )
            else:
                # Agregar tamaño de archivo
                size_kb = item.stat().st_size / 1024
                if size_kb < 1:
                    size_str = f"{item.stat().st_size}B"
                elif size_kb < 1024:
                    size_str = f"{size_kb:.1f}KB"
                else:
                    size_str = f"{size_kb/1024:.1f}MB"
                
                output_lines.append(f"{prefix}{line_prefix}{item.name} ({size_str})")
        
        return output_lines
        
    except PermissionError:
        output_lines.append(f"{prefix}[Permission Denied]")
        return output_lines

def analyze_python_files(root_dir: Path):
    """Analizar archivos Python y contar líneas"""
    python_files = []
    
    for py_file in root_dir.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Contar líneas no vacías y no comentarios
                code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
                total_lines = len(lines)
            
            python_files.append({
                'path': py_file.relative_to(root_dir),
                'total_lines': total_lines,
                'code_lines': code_lines
            })
        except Exception as e:
            print(f"Error leyendo {py_file}: {e}")
    
    return python_files

def main():
    """Función principal"""
    root_dir = Path.cwd()
    
    print("=" * 80)
    print("🌳 ÁRBOL DE ARCHIVOS DEL PROYECTO")
    print("=" * 80)
    print(f"Directorio: {root_dir}")
    print("=" * 80)
    print()
    
    # Generar árbol
    tree_lines = generate_tree(root_dir, max_depth=5)
    
    # Imprimir árbol
    print(root_dir.name + "/")
    for line in tree_lines:
        print(line)
    
    print()
    print("=" * 80)
    print("📊 ANÁLISIS DE ARCHIVOS PYTHON")
    print("=" * 80)
    
    # Analizar archivos Python
    python_files = analyze_python_files(root_dir)
    python_files.sort(key=lambda x: x['total_lines'], reverse=True)
    
    print(f"\n{'Archivo':<50} {'Líneas':>10} {'Código':>10}")
    print("-" * 80)
    
    total_lines = 0
    total_code = 0
    
    for file_info in python_files:
        path_str = str(file_info['path'])
        if len(path_str) > 47:
            path_str = "..." + path_str[-44:]
        
        print(f"{path_str:<50} {file_info['total_lines']:>10} {file_info['code_lines']:>10}")
        total_lines += file_info['total_lines']
        total_code += file_info['code_lines']
    
    print("-" * 80)
    print(f"{'TOTAL':<50} {total_lines:>10} {total_code:>10}")
    print()
    
    # Archivos grandes (>300 líneas)
    print("=" * 80)
    print("⚠️  ARCHIVOS GRANDES (>300 líneas) - Candidatos a refactorizar")
    print("=" * 80)
    
    large_files = [f for f in python_files if f['total_lines'] > 300]
    
    if large_files:
        for file_info in large_files:
            print(f"  🔴 {file_info['path']}: {file_info['total_lines']} líneas")
    else:
        print("  ✅ No hay archivos grandes")
    
    print()
    
    # Guardar a archivo
    output_file = root_dir / "PROJECT_STRUCTURE.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🌳 ÁRBOL DE ARCHIVOS DEL PROYECTO\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generado desde: {root_dir}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(root_dir.name + "/\n")
        for line in tree_lines:
            f.write(line + "\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("📊 ANÁLISIS DE ARCHIVOS PYTHON\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"{'Archivo':<50} {'Líneas':>10} {'Código':>10}\n")
        f.write("-" * 80 + "\n")
        
        for file_info in python_files:
            path_str = str(file_info['path'])
            f.write(f"{path_str:<50} {file_info['total_lines']:>10} {file_info['code_lines']:>10}\n")
        
        f.write("-" * 80 + "\n")
        f.write(f"{'TOTAL':<50} {total_lines:>10} {total_code:>10}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("⚠️  ARCHIVOS GRANDES (>300 líneas)\n")
        f.write("=" * 80 + "\n\n")
        
        if large_files:
            for file_info in large_files:
                f.write(f"  🔴 {file_info['path']}: {file_info['total_lines']} líneas\n")
        else:
            f.write("  ✅ No hay archivos grandes\n")
    
    print("=" * 80)
    print(f"✅ Árbol guardado en: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()