#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para detectar archivos obsoletos y no utilizados en el proyecto
Ejecutar: python find_obsolete_files.py
"""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

class ObsoleteFileFinder:
    """Encuentra archivos Python no utilizados en el proyecto"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.python_files = []
        self.imports = defaultdict(set)  # {archivo: set(imports)}
        self.imported_by = defaultdict(set)  # {archivo: set(archivos_que_lo_importan)}
        self.entry_points = set()  # Archivos que son entry points
        
    def scan_project(self):
        """Escanear todos los archivos Python del proyecto"""
        print("🔍 Escaneando proyecto...")
        
        ignore_dirs = {'__pycache__', 'venv', '.git', '.vscode', 'build', 'dist'}
        
        for py_file in self.root_dir.rglob("*.py"):
            # Ignorar directorios específicos
            if any(ignored in py_file.parts for ignored in ignore_dirs):
                continue
            
            self.python_files.append(py_file)
            
            # Detectar entry points
            if py_file.name in ['main.py', 'app.py', 'run.py', '__main__.py']:
                self.entry_points.add(py_file)
            
            # Analizar imports
            self._analyze_imports(py_file)
        
        print(f"✅ Encontrados {len(self.python_files)} archivos Python")
        print(f"📌 Entry points: {len(self.entry_points)}")
    
    def _analyze_imports(self, file_path: Path):
        """Analizar imports de un archivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parsear AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                print(f"⚠️  Error de sintaxis en {file_path}")
                return
            
            imports = set()
            
            for node in ast.walk(tree):
                # import module
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                
                # from module import ...
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            
            self.imports[file_path] = imports
            
            # Registrar qué archivos importan a este
            for imported in imports:
                # Intentar resolver el path del import
                possible_files = self._resolve_import(imported, file_path)
                for pf in possible_files:
                    self.imported_by[pf].add(file_path)
        
        except Exception as e:
            print(f"⚠️  Error analizando {file_path}: {e}")
    
    def _resolve_import(self, import_name: str, from_file: Path) -> List[Path]:
        """Intentar resolver un import a un archivo físico"""
        possible_files = []
        
        # Buscar en el mismo directorio
        same_dir = from_file.parent / f"{import_name}.py"
        if same_dir.exists():
            possible_files.append(same_dir)
        
        # Buscar en src/
        src_file = self.root_dir / "src" / f"{import_name}.py"
        if src_file.exists():
            possible_files.append(src_file)
        
        # Buscar como paquete
        package_init = self.root_dir / "src" / import_name / "__init__.py"
        if package_init.exists():
            possible_files.append(package_init)
        
        return possible_files
    
    def find_unused_files(self) -> Dict[str, List[Path]]:
        """Encontrar archivos no utilizados"""
        print("\n" + "=" * 80)
        print("🔍 BUSCANDO ARCHIVOS NO UTILIZADOS")
        print("=" * 80)
        
        results = {
            'never_imported': [],      # Nunca importado por nadie
            'entry_points': [],         # Entry points (siempre se consideran usados)
            'test_files': [],           # Archivos de test
            'potentially_unused': [],   # Potencialmente no usados
            'config_files': [],         # Archivos de configuración
        }
        
        for py_file in self.python_files:
            relative_path = py_file.relative_to(self.root_dir)
            
            # Clasificar archivo
            if py_file in self.entry_points:
                results['entry_points'].append(py_file)
            
            elif 'test' in py_file.name.lower() or 'test' in str(py_file.parent).lower():
                results['test_files'].append(py_file)
            
            elif py_file.name in ['config.py', 'settings.py', 'setup.py', '__init__.py']:
                results['config_files'].append(py_file)
            
            elif py_file not in self.imported_by or len(self.imported_by[py_file]) == 0:
                # No es importado por nadie
                if py_file not in self.entry_points:
                    results['never_imported'].append(py_file)
        
        return results
    
    def find_duplicate_files(self) -> List[Tuple[Path, Path, float]]:
        """Encontrar archivos con nombres similares (posibles duplicados)"""
        print("\n" + "=" * 80)
        print("🔍 BUSCANDO ARCHIVOS DUPLICADOS")
        print("=" * 80)
        
        duplicates = []
        filenames = defaultdict(list)
        
        # Agrupar por nombre
        for py_file in self.python_files:
            if py_file.name != '__init__.py':
                filenames[py_file.name].append(py_file)
        
        # Reportar duplicados
        for name, files in filenames.items():
            if len(files) > 1:
                duplicates.append((name, files))
        
        return duplicates
    
    def find_empty_files(self) -> List[Path]:
        """Encontrar archivos vacíos o casi vacíos"""
        print("\n" + "=" * 80)
        print("🔍 BUSCANDO ARCHIVOS VACÍOS")
        print("=" * 80)
        
        empty_files = []
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Contar líneas no vacías y no comentarios
                code_lines = [
                    line for line in lines 
                    if line.strip() and not line.strip().startswith('#')
                ]
                
                if len(code_lines) <= 3:  # Menos de 3 líneas de código
                    empty_files.append((py_file, len(code_lines)))
            
            except Exception as e:
                print(f"⚠️  Error leyendo {py_file}: {e}")
        
        return empty_files
    
    def analyze_file_sizes(self) -> Dict[str, List[Tuple[Path, int]]]:
        """Analizar tamaño de archivos"""
        print("\n" + "=" * 80)
        print("📊 ANÁLISIS DE TAMAÑO DE ARCHIVOS")
        print("=" * 80)
        
        sizes = {
            'very_large': [],   # > 500 líneas
            'large': [],        # 300-500 líneas
            'medium': [],       # 100-300 líneas
            'small': []         # < 100 líneas
        }
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                
                if lines > 500:
                    sizes['very_large'].append((py_file, lines))
                elif lines > 300:
                    sizes['large'].append((py_file, lines))
                elif lines > 100:
                    sizes['medium'].append((py_file, lines))
                else:
                    sizes['small'].append((py_file, lines))
            
            except Exception as e:
                print(f"⚠️  Error leyendo {py_file}: {e}")
        
        return sizes
    
    def generate_report(self):
        """Generar reporte completo"""
        print("\n" + "=" * 80)
        print("📋 REPORTE DE ARCHIVOS OBSOLETOS")
        print("=" * 80)
        
        # 1. Archivos no utilizados
        unused = self.find_unused_files()
        
        print("\n🔴 ARCHIVOS NUNCA IMPORTADOS (Posiblemente obsoletos):")
        print("-" * 80)
        if unused['never_imported']:
            for file in sorted(unused['never_imported']):
                rel_path = file.relative_to(self.root_dir)
                print(f"  ❌ {rel_path}")
            print(f"\n  Total: {len(unused['never_imported'])} archivos")
        else:
            print("  ✅ No se encontraron archivos sin usar")
        
        # 2. Entry points (informativo)
        print("\n✅ ENTRY POINTS (Siempre se consideran usados):")
        print("-" * 80)
        for file in sorted(unused['entry_points']):
            rel_path = file.relative_to(self.root_dir)
            print(f"  📌 {rel_path}")
        
        # 3. Archivos de test (informativo)
        print("\n🧪 ARCHIVOS DE TEST:")
        print("-" * 80)
        if unused['test_files']:
            for file in sorted(unused['test_files']):
                rel_path = file.relative_to(self.root_dir)
                print(f"  🧪 {rel_path}")
            print(f"\n  Total: {len(unused['test_files'])} archivos")
        else:
            print("  ⚠️  No se encontraron archivos de test")
        
        # 4. Duplicados
        duplicates = self.find_duplicate_files()
        print("\n⚠️  ARCHIVOS CON NOMBRES DUPLICADOS:")
        print("-" * 80)
        if duplicates:
            for name, files in duplicates:
                print(f"\n  📄 {name}:")
                for file in sorted(files):
                    rel_path = file.relative_to(self.root_dir)
                    print(f"    - {rel_path}")
        else:
            print("  ✅ No se encontraron duplicados")
        
        # 5. Archivos vacíos
        empty = self.find_empty_files()
        print("\n⚠️  ARCHIVOS VACÍOS O CASI VACÍOS:")
        print("-" * 80)
        if empty:
            for file, lines in sorted(empty, key=lambda x: x[1]):
                rel_path = file.relative_to(self.root_dir)
                print(f"  🗑️  {rel_path} ({lines} líneas de código)")
        else:
            print("  ✅ No se encontraron archivos vacíos")
        
        # 6. Archivos grandes
        sizes = self.analyze_file_sizes()
        print("\n📊 ARCHIVOS MUY GRANDES (>500 líneas):")
        print("-" * 80)
        if sizes['very_large']:
            for file, lines in sorted(sizes['very_large'], key=lambda x: x[1], reverse=True):
                rel_path = file.relative_to(self.root_dir)
                print(f"  🔴 {rel_path}: {lines} líneas")
        else:
            print("  ✅ No hay archivos muy grandes")
        
        print("\n📊 ARCHIVOS GRANDES (300-500 líneas):")
        print("-" * 80)
        if sizes['large']:
            for file, lines in sorted(sizes['large'], key=lambda x: x[1], reverse=True):
                rel_path = file.relative_to(self.root_dir)
                print(f"  🟡 {rel_path}: {lines} líneas")
        else:
            print("  ✅ No hay archivos grandes")
        
        # 7. Resumen
        print("\n" + "=" * 80)
        print("📊 RESUMEN")
        print("=" * 80)
        print(f"Total archivos Python: {len(self.python_files)}")
        print(f"Entry points: {len(unused['entry_points'])}")
        print(f"Archivos de test: {len(unused['test_files'])}")
        print(f"❌ Nunca importados: {len(unused['never_imported'])}")
        print(f"⚠️  Duplicados: {len(duplicates)}")
        print(f"🗑️  Vacíos: {len(empty)}")
        print(f"🔴 Muy grandes (>500): {len(sizes['very_large'])}")
        print(f"🟡 Grandes (300-500): {len(sizes['large'])}")
        
        # 8. Recomendaciones
        print("\n" + "=" * 80)
        print("💡 RECOMENDACIONES")
        print("=" * 80)
        
        if unused['never_imported']:
            print("\n🔴 ARCHIVOS PARA ELIMINAR:")
            for file in sorted(unused['never_imported']):
                rel_path = file.relative_to(self.root_dir)
                print(f"  rm {rel_path}")
        
        if duplicates:
            print("\n⚠️  REVISAR DUPLICADOS:")
            for name, files in duplicates:
                print(f"  • {name}: revisar cuál mantener")
        
        if empty:
            print("\n🗑️  ARCHIVOS VACÍOS PARA ELIMINAR:")
            for file, lines in empty:
                rel_path = file.relative_to(self.root_dir)
                print(f"  rm {rel_path}")
        
        if sizes['very_large'] or sizes['large']:
            print("\n📏 ARCHIVOS PARA REFACTORIZAR:")
            for file, lines in sorted(sizes['very_large'] + sizes['large'], 
                                     key=lambda x: x[1], reverse=True):
                rel_path = file.relative_to(self.root_dir)
                print(f"  • {rel_path}: {lines} líneas")
        
        # Guardar a archivo
        self._save_report(unused, duplicates, empty, sizes)
    
    def _save_report(self, unused, duplicates, empty, sizes):
        """Guardar reporte a archivo"""
        output_file = self.root_dir / "OBSOLETE_FILES_REPORT.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE DE ARCHIVOS OBSOLETOS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("ARCHIVOS PARA ELIMINAR (Nunca importados):\n")
            f.write("-" * 80 + "\n")
            for file in sorted(unused['never_imported']):
                rel_path = file.relative_to(self.root_dir)
                f.write(f"rm {rel_path}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("ARCHIVOS VACÍOS O CASI VACÍOS:\n")
            f.write("-" * 80 + "\n")
            for file, lines in sorted(empty, key=lambda x: x[1]):
                rel_path = file.relative_to(self.root_dir)
                f.write(f"rm {rel_path}  # {lines} líneas\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("DUPLICADOS (Revisar manualmente):\n")
            f.write("-" * 80 + "\n")
            for name, files in duplicates:
                f.write(f"\n{name}:\n")
                for file in sorted(files):
                    rel_path = file.relative_to(self.root_dir)
                    f.write(f"  - {rel_path}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("ARCHIVOS GRANDES (Candidatos a refactorizar):\n")
            f.write("-" * 80 + "\n")
            for file, lines in sorted(sizes['very_large'] + sizes['large'], 
                                     key=lambda x: x[1], reverse=True):
                rel_path = file.relative_to(self.root_dir)
                f.write(f"{rel_path}: {lines} líneas\n")
        
        print(f"\n✅ Reporte guardado en: {output_file}")


def main():
    """Función principal"""
    root_dir = Path.cwd()
    
    print("=" * 80)
    print("🔍 DETECTOR DE ARCHIVOS OBSOLETOS")
    print("=" * 80)
    print(f"Directorio: {root_dir}")
    print("=" * 80)
    print()
    
    finder = ObsoleteFileFinder(root_dir)
    finder.scan_project()
    finder.generate_report()
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 80)
    print("\n💡 Revisa OBSOLETE_FILES_REPORT.txt para un resumen completo")
    print("\n⚠️  IMPORTANTE: Revisa manualmente antes de eliminar archivos!")


if __name__ == "__main__":
    main()