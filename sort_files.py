import sys
import shutil
from pathlib import Path
from normalize_for_sort import normalize
from rich.console import Console
from rich.table import Table

# словник з розширеннями файлів, що оброблюються
DICT_FOR_EXT = {'archives': ['ZIP', 'GZ', 'TAR'],
                  'video': ['AVI', 'MP4', 'MOV', 'MKV'],
                  'audio': ['MP3', 'OGG', 'WAV', 'AMR'],
                  'documents': ['DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX'],
                  'images': ['JPEG', 'PNG', 'JPG', 'SVG'],
                  'other': []}

#PATH = Path('D:/Crap') # вихідна папка для тестування сортування
#while True:
#    try:
PATH = 0 #Path(sys.argv [1])
#        break
#    except IndexError:
#        input ('Треба ввести путь до папки, яку хочете відсортувати: ')
#        PATH = Path(sys.argv [0])
#        break

all_files = []
suff_used_known = set ()
suff_used_unknown = set()

# функція визначення типу файлу, виходячи зі словника
# визначає по розширенню файлу з крапкою перед ним ".ХХХ"
def filetype (suffix): 
    suffix = suffix.removeprefix ('.')
    for type, suffixes in DICT_FOR_EXT.items():
        for suff in suffixes:
            if suffix.lower() == suff.lower():
                 suff_used_known.add(suffix.upper())
                 return type
    suff_used_unknown.add(suffix.upper())
    return "other"

# функція створення папок, в які розсортуємо, та видалення пустих
# працює, якщо відповідаємо 'у' після першого прогону
# action 'new' створює, action 'del' удаляє 
def work_with_directories (path_: Path, action):
    from normalize_for_sort import normalize
    if action == 'new':
        for dir in path_.iterdir(): #ім'я папки нормалізую
            if dir.is_dir():
                dir.replace (PATH / normalize (dir.name))
        for dir_ in DICT_FOR_EXT.keys(): #створюю папки, якщо немає
            path_new_dir = path_ / dir_
            path_new_dir.mkdir (exist_ok = True, parents = True)
    if action == 'del':
        for dir in path_.iterdir():
            if dir.is_dir() and (dir.name not in DICT_FOR_EXT.keys()):
                try: 
                    dir.rmdir ()
                except OSError:
                    work_with_directories (dir, action = 'del')
                    print ('Велика вкладеність папок. Запусти програму ще раз')

# функція власне сортування, параметр action - для другого прогону
# з нормалізацією та переміщенням
# перший прогон - тільки для інформації скільки і чого є 
def sorting (path_, action = False):
    from normalize_for_sort import normalize
    for file in path_.iterdir(): #ім'я файлу з розширенням
        if file.is_dir():
            if action:
                sorting (file, action = True) #рекурсуємо, якщо папка
            else: sorting (file) #рекурсуємо, якщо папка
        else:
            all_files.append (filetype (file.suffix)) # список усіх типів
# нормалізую ім'я файлу та переміщую у відповідну папку
            if action: 
                file_name_norm = f'{normalize (file.stem)}{file.suffix}'
                file.replace (PATH / filetype (file.suffix) / file_name_norm)
# а тут розпаковую архів
                if filetype (file.suffix) == 'archives':
                    shutil.unpack_archive (PATH / 'archives' / file_name_norm, 
                                           PATH / 'archives' / file.stem)
    return all_files

# функція із діалогами для коректної роботи як консольний скрипт
def run (line):
    global PATH
    PATH = Path(line)
    sorting (PATH)

#вивід результатів першого прогону
    console = Console()
    table = Table (show_header=True)
    print ('')
    print (f'Вміст папки: {PATH}')
#    print ('|{:-^15}|{:-^10}|'.format ('-', '-'))
#    print ('|{:^15}|{:^10}|'.format ('Типи файлів', 'Кількість'))
    table.add_column ('Типи файлів')
    table.add_column ('Кількість')
#    print ('|{:-^15}|{:-^10}|'.format ('-', '-'))
#    print ('|{:<15}|{:^10}|'.format ('Зображення', all_files.count('images')))
    table.add_row ('Зображення', str (all_files.count('images')))
#    print ('|{:<15}|{:^10}|'.format ('Відео', all_files.count('video')))
    table.add_row ('Відео', str (all_files.count('video')))
#    print ('|{:<15}|{:^10}|'.format ('Документи', all_files.count('documents')))
    table.add_row ('Документи', str (all_files.count('documents')))
#    print ('|{:<15}|{:^10}|'.format ('Музика', all_files.count('audio')))
    table.add_row ('Музика', str (all_files.count('audio')))
#    print ('|{:<15}|{:^10}|'.format ('Архіви', all_files.count('archives')))
    table.add_row ('Архіви', str (all_files.count('archives')))
#    print ('|{:<15}|{:^10}|'.format ('Інші типи', all_files.count('other')))
    table.add_row ('Інші типи', str (all_files.count('other')))
#    print ('|{:-^15}|{:-^10}|'.format ('-', '-'))
#    print ('|{:<15}|{:^10}|'.format ('Разом', len (all_files)))
    table.add_row ('Разом', str (len (all_files)))
    console.print (table)
    print ('')
    print (f'Знайдено наступні відомі типи файлів: {suff_used_known}')
    print (f'Знайдено наступні невідомі типи файлів ("Інші типи"): {suff_used_unknown}')
    print ('')
    yn = input ('Продовжити виконання завдання: транслітерація імен файлів \
та їх переміщення у папки за типами (y - yes / n - no): ')
    print ('')
    while True:
        if yn not in 'yn':
            yn = input("Будь ласка, введіть 'y' або 'n': ") 
        else: break
    if yn == 'n':
        print ('Дякую за увагу!\n')
    else:
        work_with_directories (PATH, 'new') # створюємо цільові папки
        sorting (PATH, action = True) # нормалізуємо та переміщуємо файли
        work_with_directories (PATH, 'del') # видаляємо усі пусті папки
        print ('Імена файлів нормалізовані. Файли перемещені у\
 відповідні папки.\n')
# власне запуск
if __name__ == '__main__':
    run()