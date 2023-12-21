from collections import UserDict
from datetime import datetime
import cmd
import pickle
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
import sys
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.table import Table
import re
from sort_files import run

console = Console()
COMMANDS = {'add_name': ['add_name', 'Додавання нового контакту у довідник'],
            'add_phone': ['add_phone Name', 'Додавання телефонного номеру до контакту Name.\nКожен контакт може мати кілька номерів'],
            'add_birthday': ['add_birthday Name', 'Додавання для контакта Name дня народження у форматі РРРР-ММ-ДД'],
            'add_email': ['add_email Name', 'Додавання адреси електроної пошти для контакта Name'],
            'add_address': ['add_address Name', 'Додавання адреси для контакта Name'],
            'find_record_by_trem': ['find_record_by_trem text', "Пошук рядку 'text' у всіх полях телефонного довідника"],
            'list_book': ['list_book', 'Вивід на екран телефонного довідника'],
            'delete_phone': ['delete_phone Name', 'Видалення номеру телефону у контакту Name'],

            'add_note': ['add_note', 'Додавання нотатки для контакту ____'],
            'find_note_by_name': ['find_note_by_name', 'Пошук у нотатках за іменем ____'],
            'find_notes_by_term': ['find_notes_by_term', 'Пошук у нотатках за будь яким терміном ____'],
            'list_note': ['list_note', 'Вивід на екран усіх нотаток'],
            'edit_note': ['edit_note', 'Коригування нотаток'],
            'delete_all_notes': ['delete_all_notes', 'Видалення усіх нотаток'],

            'days_to_birthday': ['days_to_birthday Name', 'Розрахунок залишку днів до дня народження контакта "Name"'],
            'when': ['when Number', 'Виводить на екран список контактів, у яких день народження впродовж "Number" днів від сьогодні'],
            'sort_files': ['sort_files Path', 'Сортує файли у папці "Path" на вашому диску по папках в залежності від типу файлу'],

            'help': ['help', 'Виклик довідника команд, що вміє цей бот'],
            'load': ['load', 'Завантаження довідника з файла на диску. \nПерезапише зміни, що були внесені та не збережені у файл.\nТакож відбувається автоматично при запуску програми'],
            'save': ['save', 'Зберігання змін у довіднику у файл на диску.\nТакож відбувається автоматично при закінченні роботи з програмою'],
            'exit': ['exit', 'Вихід із програми із автоматичним записом змін у файл'],
}

class Field:
    def __init__(self, value):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def __str__(self):
        return str(self._value)

    def validate(self):
        pass


class Name(Field):
    def __init__(self, name):
        super().__init__(name)


class Phone(Field):

    def validate(self):
        if self._value and not (isinstance(self._value, str) and len(self._value) == 10 and self._value.isdigit()):
            raise ValueError("Phone must be a 10-digit number.")

    @Field.value.setter
    def value(self, new_value):
        if not isinstance(new_value, str) or not new_value.isdigit():
            raise ValueError("Phone must be a string containing only digits.")
        self._value = new_value
        self.validate()


class Address(Field):
    def __init__(self, value):
        super().__init__(value)


class Email(Field):
    @Field.value.setter
    def value(self, new_value):
        result = re.findall(r"[a-zA-Z0-9_.]+@\w+\.\w{2,3}", new_value)
        try:
            self._value = result[0]
        except IndexError:
            raise IndexError("E-mail must be 'name@domain'")


class Birthday(Field):

    @Field.value.setter
    def value(self, new_value):

        try:
            datetime.strptime(new_value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format!!! Use YYYY-MM-DD.")

        self._value = new_value


class Record:
    def __init__(self, name, email=None, address=None, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.email = Email(email) if email else None
        self.address = Address(address) if address else None
        self.birthday = Birthday(birthday) if birthday else None

    def add_phone(self, phone):
        phone_field = Phone(phone)
        phone_field.validate()
        self.phones.append(phone_field)

    def add_email(self, email):
        email_field = Email(email)
        self.email = email_field

    def add_address(self, address):
        address_field = Address(address)
        self.address = address_field

    def add_birthday(self, birthday):
        new_birthday = Birthday(birthday)
        self.birthday = new_birthday

    def remove_phone(self, phone):
        if (list(filter(lambda p: p.value == phone, self.phones)) == []):
            print (f'Телефон {phone} не існує.')
        else:
            self.phones = list(filter(lambda p: p.value != phone, self.phones))
            print(f"Телефон {phone} видалений.")

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                return
        raise ValueError("Не існує запису!!")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        return f"Record(name={self.name.value}, birthday={self.birthday}, phones={[phone.value for phone in self.phones]})"

    def days_to_birthday(self):
        if not self.birthday:
            return -1

        today = datetime.now().date()
        next_birthday = datetime.strptime(self.birthday.value, "%Y-%m-%d").date().replace(year=today.year)
        if today > next_birthday:
            next_birthday = next_birthday.replace(year=today.year + 1)

        days_until_birthday = (next_birthday - today).days
        return days_until_birthday


class AddressBook(UserDict):
    record_id = None

    def __init__(self, file="adress_book_1.pkl"):
        self.file = Path(file)
        self.record_id = 0
        self.record = {}
        super().__init__()

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, term):

        if term in self.data:
            return self.data[term]
        else:
            return None

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def iterator(self, item_number):
        counter = 0
        result = []
        for item, record in self.data.items():
            result.append(record)
            counter += 1
            if counter >= item_number:
                yield result
                counter = 0
                result = []

    def dump(self):
        with open(self.file, "wb") as file:
            pickle.dump((self.record_id, dict(self.data)), file)

    def load(self):
        if not self.file.exists():
            return
        with open(self.file, "rb") as file:
            self.record_id, data = pickle.load(file)
            self.data.update(data)


    def find_by_term(self, term: str) -> List[Record]:
        matching_records = []

        for record in self.data.values():
            for phone in record.phones:
                if term in phone.value:
                    matching_records.append(record)
            if term in str (record.email):
                matching_records.append(record)
            if term in str (record.address):
                matching_records.append(record)

        matching_records.extend(record for record in self.data.values() if term.lower() in record.name.value.lower())
        return matching_records


class Note(Field):
    def __init__(self, text, date, tags=None):
        super().__init__(text)
        self.tags = tags if tags is not None else []
        self.date = date

    def add_tag(self, tag):
        self.tags.append(tag)

    def remove_tag(self, tag):
        self.tags.remove(tag)


class NoteRecord(Record):
    def __init__(self, name, birthday=None):
        super().__init__(name, birthday=None)
        self.notes = []

    def add_note(self, text, tags=None):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        note = Note(text, date, tags)
        self.notes.append(note)

    def remove_note(self, text):
        if not text:
            raise ValueError("Введіть нотаток!")
        self.notes = [note for note in self.notes if note.value != text]

    def edit_note(self, new_text, new_tags=None):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        for idx, a in enumerate(self.notes):
            if new_text:
                note = new_text
                tags = new_tags
                self.notes[idx] = Note(note, date, tags) 

    def find_notes_by_tag(self, tag):
        return [note for note in self.notes if tag in note.tegs]
    
    def find_notes_by_term(self, term):
        return [note for note in self.notes if term.lower() in note.value.lower() or any(term.lower() in tag.lower() for tag in note.tags)]

    def __str__(self):
        notes_str = " | ".join([f"{note.value} [{' ,'.join(note.tags)}]" for note in self.notes])
        return f"NoteRecord(name={self.name.value}, notes={notes_str})"


class Controller():
    def __init__(self):
        super().__init__()
        self.book = AddressBook()

    def do_exit(self):
        self.book.dump()
        print("Адресна книга збережена! Вихід...")
        return True

    def do_save(self):
        self.book.dump()
        print("Адресна книга збережена!")

    def do_load(self):
        self.book.load()
        print("Адресна книга відновлена")

    def do_help(self):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column('Синтаксис команди')
        table.add_column('Опис')

        for commands in COMMANDS.values():
            table.add_row(commands[0], commands[1])
            table.add_section()
        console.print(table)
        print('Після введення команди натисни Enter')

    def do_add_name(self):
        while True:
            line = input("Введіть: <Ім'я>: ")
            if not line:
                print("Будь ласка введіть: <Ім'я>: ")
                continue
            name = line.strip().title()
            if name in self.book:
                print(f"Контакт з ім'ям '{name}' вже існує.")
                return
            try:
                record = NoteRecord(name)
                self.book.add_record(record)
                print(f"Контакт з ім'ям '{name}' успішно створено.")
                break
            except ValueError as e:
                print(f"Помилка при створенні контакту: {e}")

    def do_add_phone(self, name):

        record = self.book.get(name.title())

        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        phone = input ('Введіть номер телефону: 10 цифр:  ')

        try:
            record.add_phone(phone)
            print(f"Телефон '{phone}' додано до контакта '{name}'.")
        except ValueError as e:
            print(f"Помилка при додаванні телефону: {e}")

    def do_delete_phone(self, name):

        record = self.book.get(name.title())

        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        phone = input ('Введіть номер телефону: 10 цифр:  ')

        try:
            record.remove_phone(phone)
        except ValueError as e:
            print(f"Помилка при видаленні телефону: {e}")

    def do_add_birthday(self, name):
        name = name.title()  # Ensure that the name's first letter is capital
        record = self.book.get(name.title())

        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        birthday_str = input ('Введіть дату дня народження у форматі РРРР-ММ-ДД:  ')
        try:
            record.add_birthday(birthday_str)
            print(f"День народження {birthday_str} додано для контакта '{name}'.")
        except ValueError as e:
            print(f"Помилка при додаванні дні народження: {e}")

    def do_add_email(self, name):
        record = self.book.get(name.title())
        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        email = input('Введіть email:  ')
        try:
            record.add_email(email)
            print(f"Email '{email}' додано до контакта '{name}'.")
        except IndexError as e:
            print(f"Помилка при додаванні email: {e}")

    def do_add_address(self, name):
        record = self.book.get(name.title())
        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        address = input('Введіть адресу: ')
        try:
            record.add_address(address)
            print(f"Адреса '{address}' додана до контакта '{name}'.")
        except ValueError as e:
            print(f"Помилка при додаванні адреси: {e}")

    def do_list_book(self):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column('Name')
            table.add_column("Phone")
            table.add_column("Address")
            table.add_column("Email")
            table.add_column("Birthday")
            for record_id, record in self.book.data.items():
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = record.birthday.value if record.birthday else ""
                address_info = record.address.value if record.address else ""
                email_info = record.email.value if record.email else ""
                table.add_row(record.name.value, phones, address_info, email_info, birthday_info)
                table.add_section()
            console.print(table)

    def do_list_note(self):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            table = Table(show_header=True, header_style="bold yellow")
            table.add_column('Author')
            table.add_column("Note")
            table.add_column("Tag")
            table.add_column("Date", style="dim", width=12)
            for name, record in self.book.data.items():
                if isinstance(record, NoteRecord) and record.notes:
                    for h in record.notes:
                        table.add_row(name, h.value, h.tags, h.date)
                        table.add_section()
            console.print(table)

    def do_find_record_by_trem(self, line):
        matching_records = self.book.find_by_term(line)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column('Name')
        table.add_column("Phone")
        table.add_column("Address")
        table.add_column("Email")
        table.add_column("Birthday")
        if matching_records:
            for record in matching_records:
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = record.birthday.value if record.birthday else ""
                address_info = record.address.value if record.address else ""
                email_info = record.email.value if record.email else ""
                table.add_row(record.name.value, phones, address_info, email_info, birthday_info)
                table.add_section()
            console.print(table)
        else:
            print("Даних із таким текстом не існує!!!.")
    
    def do_find_notes_by_term(self, term):
        term = term.strip().lower()
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column('Name')
        table.add_column('Note')
        table.add_column('Date')
        table.add_column('Tags')
        
        found_notes = False
        for name, record in self.book.data.items():
            if isinstance(record, NoteRecord):
                matching_notes = record.find_notes_by_term(term)
                for note in matching_notes:
                    tag_string = ', '.join(note.tags) if note.tags else ''
                    table.add_row(name, note.value, note.date, tag_string)
                    found_notes = True
        
        console = Console()
        if found_notes:
            console.print(table)
        else:
            print("Даних із таким текстом не існує!!!.")
    
    def do_days_to_birthday(self, line, when=9999): # >>>birthday John (до дня народження контакту John, залишилось 354 днів)
        name = line.strip().title()
        record = self.book.find(name)
        if record:
            days_until_birthday = record.days_to_birthday()
            if 0 < days_until_birthday < when:
                print(f"До дня народження {name} {record.birthday} залишилось {days_until_birthday} днів")
            elif days_until_birthday == 0:
                print(f"День народження контакту {name} сьогодні!!!")
            elif (days_until_birthday > when or days_until_birthday == -1) and (when != 9999):
                pass
            else:
                print(f"День народження не додано в книгу контактів")
        else:
            print(f"Контакт '{name}' не знайдений")
            
    def do_when (self, days):
        if not days:
            print ("Введіть 'when' та кількість днів, на які хочете побачити прогноз")
            return
        if not days.isdigit():
            print ("Введіть кількість днів додатнім числовим значенням")
            return
        for record in self.book.values():
            self.do_days_to_birthday (record.name.value, int(days)) 

    def do_add_note(self, name):
        name_normal = name.strip().title()
        record = self.book.data.get(name_normal)
        if record is None:
            print(f"Контакт з ім'ям '{name_normal}' не знайдено.")
            return
        if not isinstance(record, NoteRecord):
            print(f"Для контакта '{name_normal}' не підтримуються нотатки.")
            return
        note_text = input('Введіть нотатку: ')
        tags = input('Введіть теги: ')
        record.add_note(note_text, tags)
        print(f"Заметка додана до контакта {name_normal}.")

    def do_find_note_by_name(self, line):
        name = line.strip().title()
        record = self.book.data.get(name)
        if not record:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        if isinstance(record, NoteRecord) and record.notes:
            for note in record.notes:
                print(f"{name}: {note.value} [Tags: {''.join(note.tags)}]")
        else:
            print(f"Для контакта '{name}' не знайдено нотаток або вони не підтримуються.")

    def do_delete_all_notes(self, line):
        name = input("Введіть ім'я для видалення всіх нотаток: ")
        name_normal = name.strip().title()
        if name_normal in self.book:
            record = self.book[name_normal]
            if isinstance(record, NoteRecord):
                record.notes.clear()
                print(f"Усі нотатки для '{name_normal}' було видалено.")
            else:
                print("Для цього контакта нотатки не підтримуються.")
        else:
            print("Контакт не знайдено.")

    

    def do_edit_note(self, line):
        name = line.strip().title()
        record = self.book.data.get(name)
        if record is None:
            print(f"Контакт з ім'ям '{name}' не знайдено.")
            return
        new_text= input("Введіть нову нотатку: ")
        new_tags = input("Введіть новий тег: ")
        record.edit_note(new_text, new_tags)
        print("Примітка успішно відредагована.")

    def do_sort_files(self, line):
        if not line:
            print("Введіть шлях до папки, яку треба сортувати")
            return
        try:
            run(line)
        except FileNotFoundError:
            print('Така папка не існує на диску. Можливо треба ввести повний шлях\n')


class CommandValidator(Validator):
    def validate(self, document):
        text = document.text
        if text.startswith("add_phone"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))
#            if (not x[2].isdigit()):
#                raise ValidationError(message='Телефон повинен складатися з цифр', cursor_position=len(text))

        if text.startswith("delete_phone"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_birthday"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("find_record_by_trem"):
            x = text.split(" ")
            if len(x) == 1:
                raise ValidationError(message="Введіть: будь який термін для пошуку", cursor_position=len(text))

        if text.startswith("days_to_birthday"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я> для пошуку", cursor_position=len(text))

        if text.startswith("when"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: кількість днів для пошуку", cursor_position=len(text))

        if text.startswith("sort_files"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: шлях до папки, яку треба сортувати", cursor_position=len(text))

        if text.startswith("add_note"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("find_note_by_name"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я> для пошуку", cursor_position=len(text))
            
        if text.startswith("find_notes_by_term"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я> для пошуку", cursor_position=len(text))
            
        if text.startswith("edit_note"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position = len(text))
            
        if text.startswith("delete_all_notes"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_email"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_address"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))


def handle_command(command):
    if command.lower().startswith("add_name"):
        return controller.do_add_name()
    elif command.lower().startswith("help"):
        return controller.do_help()
    elif command.lower().startswith("add_phone"):
        _, name = command.split(" ")
        return controller.do_add_phone(name)
    elif command.lower().startswith("delete_phone"):
        _, name = command.split(" ")
        return controller.do_delete_phone(name)
    elif command.lower().startswith("add_email"):
        _, line = command.split(" ")
        return controller.do_add_email(line)
    elif command.lower().startswith("add_address"):
        _, line = command.split(" ")
        return controller.do_add_address(line)
    elif command.lower().startswith("add_birthday"):
        _, name = command.split(" ")
        return controller.do_add_birthday(name)
    elif command.lower().startswith("list_book"):
        return controller.do_list_book()
    elif command.lower().startswith("load"):
        return controller.do_load()
    elif command.lower().startswith("list_note"):
        return controller.do_list_note()
    elif command.lower().startswith("find_record_by_trem"):
        _, line = command.split(" ")
        return controller.do_find_record_by_trem(line)
    elif command.lower().startswith("days_to_birthday"):
        _, name = command.split(" ")
        return controller.do_days_to_birthday(name)
    elif command.lower().startswith("when"):
        _, name = command.split(" ")
        return controller.do_when(name)
    elif command.lower().startswith("sort_files"):
        _, name = command.split(" ")
        return controller.do_sort_files(name)
    elif command.lower().startswith("add_note"):
        _, name = command.split(" ")
        return controller.do_add_note(name)
    
    elif command.lower().startswith("find_note_by_name"):
        _, name = command.split(" ")
        return controller.do_find_note_by_name(name)
    
    elif command.lower().startswith("find_notes_by_term"):
        _, name = command.split(" ")
        return controller.do_find_notes_by_term(name)
    
    elif command.lower().startswith("edit_note"):
         _, name = command.split(" ")
         return controller.do_edit_note(name)
    elif command.lower().startswith("delete_all_notes"):
        _, name = command.split(" ")
        return controller.do_delete_all_notes(name)
    elif command.lower() == "exit":
        controller.do_exit()
        return 'Good bye!'
    elif command.lower() == "save":
        return controller.do_save()


def main():
    controller.do_load()
    print("Ласкаво просимо до Адресної Книги")

    while True:
        commands_for_interp = {}
        for command in COMMANDS.keys():
            commands_for_interp[command] = None
        command_interpreter = NestedCompleter.from_nested_dict(commands_for_interp)

        user_input = prompt('Enter command: ', completer=command_interpreter, validator=CommandValidator(),
                            validate_while_typing=False)
        if user_input.lower() == "exit":
            print("Good bye!")
            break
        response = handle_command(user_input)


if __name__ == "__main__":
    controller = Controller()
    main()
