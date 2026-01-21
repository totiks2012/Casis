#!/usr/bin/env python3
"""
Ассистент для вайб кодинга с ИИ
casis.py - Простой скрипт с маркерами ***
Автор -- totiks
январь 2026
ver-04 (обновлён по запросу)
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
import fnmatch
from typing import Dict, List, Tuple, Optional

SNAPSHOT_FILE = "project_for_ai.txt"
FILTERS_FILE = "filters.txt"
MARKER = "***"

def create_new_project(project_path: str = ".") -> bool:
    """Создаёт новый проект с конфигурационными файлами"""
    path = Path(project_path)

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # Создаем filters.txt
    (path / FILTERS_FILE).write_text(
        "# ВКЛЮЧИТЬ\n*.py\n*.js\n*.html\n*.css\n*.json\n*.md\n*.txt\n"
        "*.sh\n*.yml\n*.yaml\n*.toml\n*.ini\n*.cfg\n*.xml\n*.sql\n"
        "*.java\n*.cpp\n*.c\n*.h\n*.hpp\n*.go\n*.rs\n*.php\n*.rb\n"
        "*.pl\n*.lua\n*.swift\n*.kt\n*.dart\n\n"
        "# ИСКЛЮЧИТЬ\n.git\nnode_modules\n__pycache__\n*.log\n*.tmp\n"
        "*.bak\nvenv\n.venv\ndist\nbuild\n.vscode\n.idea\n*.egg-info\n"
        "__pycache__\n*.pyc\n*.pyo\n.env\n*.env\n",
        encoding='utf-8'
    )

    # Создаем начальный project_for_ai.txt
    create_first_snapshot(path)

    print(f"✓ Проект создан: {path.resolve()}")
    print(f"  Конфиг: {FILTERS_FILE}")
    print(f"  История: {SNAPSHOT_FILE}")
    return True

def create_first_snapshot(project_path: Path) -> None:
    """Создаёт первый снимок проекта"""
    lines = [
        "=" * 60,
        f"ПРОЕКТ: {project_path.name}",
        f"СОЗДАН: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
        "# ИСТОРИЯ И ПРАВИЛА",
        "",
        "## Идея",
        "Опишите идею проекта...",
        "",
        "## ПРАВИЛА ДЛЯ ИИ:",
        "-- скрипт включает ТОЛЬКО файлы с числовыми индексами в имени (например, script-01.py)",
        "-- все остальные файлы игнорируются",
        "-- код последних версий группируется по базовому имени",
        "-- каждая группа отделяется строкой ====================",
        "",
        "ИСТОРИЯ РАЗРАБОТКИ",
        "ИТЕРАЦИИ И ВАЖНЫЕ МОМЕНТЫ:",
        "",
        "=" * 60,
        "ПЕРВЫЙ СНИМОК",
        "=" * 60,
        "",
        MARKER,
        "",
        "# Код проекта будет здесь после первого запуска скрипта",
        "",
        MARKER,
        "",
        "=" * 60,
        f"📊 ФАЙЛОВ ВКЛЮЧЕНО: 0",
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
    ]

    (project_path / SNAPSHOT_FILE).write_text('\n'.join(lines), encoding='utf-8')

def read_filters(project_path: Path) -> Dict[str, List[str]]:
    """Читает фильтры из filters.txt"""
    filters = {'include': [], 'exclude': []}
    filters_file = project_path / FILTERS_FILE

    if not filters_file.exists():
        return {
            'include': ['*.py', '*.js', '*.html', '*.css', '*.json', '*.md'],
            'exclude': ['.git', 'node_modules', '__pycache__', '*.log']
        }

    try:
        content = filters_file.read_text(encoding='utf-8')
    except:
        try:
            content = filters_file.read_text(encoding='cp1251')
        except:
            content = ""

    current_section = None
    for line in content.split('\n'):
        line = line.strip()

        if line.startswith('# ВКЛЮЧИТЬ'):
            current_section = 'include'
            continue
        elif line.startswith('# ИСКЛЮЧИТЬ'):
            current_section = 'exclude'
            continue
        elif not line or line.startswith('#'):
            continue

        if current_section and line:
            filters[current_section].append(line)

    return filters

def should_include(filepath: Path, filters: Dict[str, List[str]], project_root: Path) -> bool:
    """Проверяет, должен ли файл быть включен в снимок (до проверки индекса)"""
    rel_path = str(filepath.relative_to(project_root))

    for pattern in filters['exclude']:
        if pattern in rel_path.split(os.sep):
            return False
        if fnmatch.fnmatch(filepath.name, pattern):
            return False

    if filters['include']:
        for pattern in filters['include']:
            if fnmatch.fnmatch(filepath.name, pattern):
                return True
        return False

    return True

def extract_version_info(filename: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Извлекает базовое имя и номер версии.
    Возвращает (base_name_with_ext, version) только если есть числовой индекс.
    Иначе — (None, None).
    """
    if '.' in filename:
        name_part, ext_part = filename.rsplit('.', 1)
        full_ext = f'.{ext_part}'
    else:
        name_part = filename
        full_ext = ''

    # Ищем числовой суффикс или инфикс вида -NN или _NN
    match = re.search(r'[-_](\d+)$', name_part)
    if match:
        number = int(match.group(1))
        base_name = name_part[:-(len(match.group(1)) + 1)]
    else:
        match = re.search(r'(\d+)$', name_part)
        if match:
            number = int(match.group(1))
            base_name = name_part[:-len(match.group(1))]
        else:
            # Нет индекса → не включаем
            return (None, None)

    base_name = base_name.rstrip('-_')
    if not base_name:
        # Защита от пустого имени (например, "01.py")
        return (None, None)

    return (f"{base_name}{full_ext}", number)

def find_latest_versions_by_family(files: List[Path]) -> Dict[str, Path]:
    """
    Группирует файлы по базовому имени (с расширением),
    выбирает последнюю версию в каждой группе.
    Возвращает словарь: {base_name_with_ext: latest_path}
    Только файлы с индексом!
    """
    groups = {}

    for filepath in files:
        filename = filepath.name
        base_name, version = extract_version_info(filename)

        if base_name is None or version is None:
            continue  # Пропускаем файлы без индекса

        if base_name not in groups:
            groups[base_name] = []

        groups[base_name].append((version, filepath))

    # Выбираем последнюю версию в каждой группе
    result = {}
    for base, versions in groups.items():
        if len(versions) == 1:
            result[base] = versions[0][1]
        else:
            # Сортируем по версии по убыванию
            versions.sort(key=lambda x: x[0], reverse=True)
            latest = versions[0][1]
            result[base] = latest

            # Опционально: вывод замены
            old_names = [fp.name for _, fp in versions[1:]]
            print(f"  🔄 {latest.name} (вместо: {', '.join(old_names)})")

    return result

def replace_between_markers(old_content: str, new_code: str) -> str:
    """
    Заменяет всё между маркерами *** на новый код.
    """
    lines = old_content.split('\n')
    markers = [i for i, line in enumerate(lines) if line.strip() == MARKER]

    if len(markers) < 2:
        # Если нет двух маркеров, создаем их
        return old_content + f"\n\n{MARKER}\n{new_code}\n{MARKER}\n"

    before = '\n'.join(lines[:markers[0] + 1])
    after = '\n'.join(lines[markers[1]:])
    return before + "\n" + new_code + "\n" + after

def create_snapshot(project_path: str = ".") -> Optional[Path]:
    """Создаёт снимок проекта — ТОЛЬКО файлы с индексами"""
    path = Path(project_path)

    print(f"📦 Создаю снимок проекта: {path.name}")

    # Читаем фильтры
    filters = read_filters(path)

    # Собираем файлы
    all_files = []
    for item in path.rglob("*"):
        if item.is_file() and item.name not in [SNAPSHOT_FILE, FILTERS_FILE]:
            if should_include(item, filters, path):
                all_files.append(item)

    if not all_files:
        print("✗ Нет файлов для включения")
        return None

    # Отбираем ТОЛЬКО файлы с индексами и группируем по семействам
    print("  Отбираю файлы с индексами...")
    latest_by_family = find_latest_versions_by_family(all_files)

    if not latest_by_family:
        print("⚠️  Нет файлов с числовыми индексами (например, -01, _02 и т.п.)")
        code_content = ""
        included = 0
        skipped = len(all_files)
    else:
        # Формируем код: каждое семейство — отдельный блок
        print("  Формирую код по семействам...")
        code_blocks = []
        included = 0

        # Сортируем по имени базового файла для предсказуемости
        for base_name in sorted(latest_by_family.keys()):
            filepath = latest_by_family[base_name]
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                rel_path = str(filepath.relative_to(path))
                block = f"--- {rel_path} ---\n{content}"
                code_blocks.append(block)
                included += 1
            except Exception as e:
                rel_path = str(filepath.relative_to(path))
                code_blocks.append(f"--- {rel_path} ---\n[Ошибка чтения]")
                included += 1

        # Разделяем блоки символами ====================
        code_content = "\n\n====================\n\n".join(code_blocks)
        skipped = len(all_files) - included

    # Читаем старый снимок
    old_snapshot = path / SNAPSHOT_FILE
    if old_snapshot.exists():
        try:
            old_content = old_snapshot.read_text(encoding='utf-8')
        except:
            old_content = ""
    else:
        old_content = ""

    # Формируем статистику
    stats = [
        f"\n📊 ФАЙЛОВ ВКЛЮЧЕНО: {included}",
        f"🔄 Старых версий пропущено: {skipped}",
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ]

    # Заменяем код между маркерами
    if old_content:
        new_content = replace_between_markers(old_content, code_content)

        # Обновляем статистику в конце
        lines = new_content.split('\n')
        last_sep_index = -1
        for i in range(len(lines)-1, -1, -1):
            if '=' * 60 in lines[i]:
                last_sep_index = i
                break

        if last_sep_index != -1:
            lines = lines[:last_sep_index]
            lines.append("=" * 60)
            lines.extend(stats)
            lines.append("=" * 60)
            new_content = '\n'.join(lines)
    else:
        # Создаём новый файл
        new_content = f"""============================================================
ПРОЕКТ: {path.name}
СОЗДАН: {datetime.now().strftime('%Y-%m-%d %H:%M')}
============================================================

# ИСТОРИЯ И ПРАВИЛА

## Идея
Опишите идею проекта...

## ПРАВИЛА ДЛЯ ИИ:
-- скрипт включает ТОЛЬКО файлы с числовыми индексами в имени (например, script-01.py)
-- все остальные файлы игнорируются
-- код последних версий группируется по базовому имени
-- каждая группа отделяется строкой ====================

ИСТОРИЯ РАЗРАБОТКИ
ИТЕРАЦИИ И ВАЖНЫЕ МОМЕНТЫ:

============================================================
ПЕРВЫЙ СНИМОК
============================================================

***
{code_content}
***

============================================================
{chr(10).join(stats)}
============================================================"""

    # Сохраняем
    snapshot_path = path / SNAPSHOT_FILE
    snapshot_path.write_text(new_content, encoding='utf-8')

    print(f"✅ Снимок создан: {snapshot_path}")
    print(f"  Файлов с индексами: {included}")
    if skipped > 0:
        print(f"  Пропущено (без индекса или старые): {skipped}")

    size = snapshot_path.stat().st_size / 1024
    if size > 500:
        print(f"⚠️  Размер: {size:.1f} KB")

    return snapshot_path

def main():
    """Основная функция"""
    if len(sys.argv) == 1:
        create_snapshot()
    elif sys.argv[1] == "-n":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        create_new_project(path)
    elif sys.argv[1] in ["-h", "--help"]:
        print("casis.py - Ассистент для вайб кодинга с ИИ")
        print("\nИспользование:")
        print("  casis.py -n [путь]    Создать проект")
        print("  casis.py               Создать/обновить снимок")
        print("  casis.py [путь]        Снимок указанной папки")
        print("  casis.py -h            Справка")
        print("\nОсобенности:")
        print("  • Сохраняет историю до маркеров ***")
        print("  • Заменяет код между маркерами ***")
        print("  • Включает ТОЛЬКО файлы с индексами: name-01.py, core_02.js и т.п.")
        print("  • Группирует код по семействам, разделяя ====================")
    else:
        create_snapshot(sys.argv[1])

if __name__ == "__main__":
    main()