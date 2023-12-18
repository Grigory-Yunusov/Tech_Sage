"""
Функція normalize:
Проводить транслітерацію кирилічного алфавіту на латинський.
Замінює всі символи крім латинських літер, цифр на '_'.

Вимоги до функції normalize:
приймає на вхід рядок та повертає рядок;
проводить транслітерацію кирилічних символів на латиницю;
замінює всі символи, крім літер латинського алфавіту та цифр, на символ '_';
транслітерація може не відповідати стандарту, але бути читабельною;
великі літери залишаються великими, а маленькі — маленькими після транслітерації.
"""
import re
CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ0123456789"
LATIN_SYMBOLS = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", 
               "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "h", "ts",
               "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", 
               "ji", "g", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
DICT_TRANSLATE = {}
    
for c, t in zip (CYRILLIC_SYMBOLS, LATIN_SYMBOLS):
    DICT_TRANSLATE [ord(c)] = t
    DICT_TRANSLATE [ord(c.upper())] = t.upper()

def normalize(name):
    name_ = name
    for letter in name:
        if (DICT_TRANSLATE.get (ord(letter)) == None) and \
           (re.search('\W', letter)):
            name_ = name_.replace (letter, '_')
    return name_.translate (DICT_TRANSLATE)

if __name__ == '__main__':
# тестовий рядок для нормалізації
    print (normalize('К:и%р;и!л№о123Kiriloc?'))