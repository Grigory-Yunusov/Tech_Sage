from collections import UserDict
from datetime import datetime
import cmd
import pickle
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod

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


class Birthday(Field):

    @Field.value.setter
    def value(self, new_value):

        try:
            datetime.strptime(new_value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format!!! Use YYYY-MM-DD.")

        self._value = new_value


class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = Birthday(birthday) if birthday else None

    def add_phone(self, phone):
        phone_field = Phone(phone)
        phone_field.validate()
        self.phones.append(phone_field)

    def add_birthday(self, birthday):
        new_birthday = Birthday(birthday)
        self.birthday = new_birthday

    def remove_phone(self, phone):
        self.phones = list(filter(lambda p: p.value != phone, self.phones))


    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                return
        raise ValueError("not on the list!!")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        # return f"{phone} - not on the list!!!"
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


class Printer(ABC):
    @abstractmethod
    def print_message(self, message):
        pass


class ConsolePrint(Printer):
    def print_message(self, message):
        print(message)



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

    def __iter__(self):
        return iter(self.data.values())

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

        matching_records.extend(record for record in self.data.values() if term.lower() in record.name.value.lower())
        return matching_records


class Note(Field):
    def __init__(self, text, tags=None):
        super().__init__(text)
        self.tags = list(tags) if tags else []

    def add_tag(self, tag):
        self.tags.appand(tag)

    def remove_tag(self, tag):
        self.tags.remove(tag)

class NoteRecord(Record):
    def __init__(self, name, birthday=None):
        super().__init__(name, birthday=None)
        self.notes = []

    def add_note(self, text, tags=None):
        note = Note(text, tags)
        self.notes.append(note)

    def remove_note(self, text):
        if not text:
            raise ValueError("Введіть нотаток!")
        self.notes = [note for note in self.notes if note.value != text]

    def edit_note(self, old_text, new_text, new_tags=None):
        for note in self.notes:
            if note.value == old_text:
                note.value = new_text
                if new_tags is not None:
                    note.tags = new_tags
                break

    def find_notes_by_tag(self, tag):
        return [note for note in self.notes if tag in note.teg]

    def __str__(self):
        notes_str = " | ".join([f"{note.value} [{' ,'.join(note.tags)}]" for note in self.notes])
        return f"NoteRecord(name={self.name.value}, notes={notes_str})"


class Controller(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.book = AddressBook()
        self.prompt = ">>>"
        self.intro = "Ласкаво просимо до Адресної Книги"

    def do_exit(self, arg):
        self.book.dump()
        print("Адресна книга збережена! Вихід...")
        return True

    def do_save(self, arg):
        self.book.dump()
        print("Адресна книга збережена!")

    def do_load(self, arg):
        self.book.load()
        print("Адресна книга відновлена")

    def do_add_name(self, line):
        if not line:
            print("Введіть: add_name Ім'я")
            return
        name = line.strip().capitalize()

        if name in self.book:
            print(f"Контакт з іменем {name} вже існує.")
            return

        try:
            record = NoteRecord(name)
            self.book.add_record(record)
            print(f"Контакт з іменем {name} успішно створено.")
        except ValueError as e:
            print(f"Помилка при створенні контакту: {e}")

    def do_add_phone(self, line):
        if not line:
            print("Введіть: add_phone Ім'я, Телефон")
            return
        data = line.split(",")
        if len(data) != 2:
            print("Для команди add_phone потрібно вказати ім'я та один телефон.")
            return
        name, phone = map(str.strip, data)
        record = self.book.get(name.capitalize())

        if not record:
            print(f"Контакт з іменем {name} не знайдено.")
            return

        try:
            record.add_phone(phone)
            print(f"Телефон {phone} додано до контакта {name}.")
        except ValueError as e:
            print(f"Помилка при додаванні телефону: {e}")

    def do_add_birthday(self, line):
        if not line:
            print("Введіть: add_birthday Ім'я, День народження")
            return
        data = line.split(",", 1)
        if len(data) != 2:
            print("Для команди add_birthday потрібно вказати ім'я та дату народження через кому.")
            return
        name, birthday_str = map(str.strip, data)
        name = name.capitalize()  # Ensure that the name's first letter is capital
        record = self.book.get(name)

        if not record:
            print(f"Контакт з іменем {name} не знайдено.")
            return

        try:
            record.add_birthday(birthday_str)
            print(f"День народження {birthday_str} додано для контакта {name}.")
        except ValueError as e:
            print(f"Помилка при додаванні дня народження: {e}")

    def do_list_book(self, arg):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            for record_id, record in self.book.data.items():
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = f", День народження: {record.birthday.value}" if record.birthday else ""

                print(f"{record_id}: {record.name.value}, {phones}{birthday_info}")
    def do_list_note(self, arg):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            for name, record in self.book.data.items():
                if isinstance(record, NoteRecord) and record.notes:
                    note_info = " | ".join([f'{note.value} [{" ,".join(tag for tag in note.tags)}]' for note in record.notes])
                    note_info = f" {note_info}"
                    print(f"{name}: {note_info}")

    def do_find(self, arg):
        term = input("Введіть термін для пошуку: ")
        matching_records = self.book.find_by_term(term)
        if matching_records:
            for record in matching_records:
                phones = ", ".join(phone.value for phone in record.phones )
                birthday_info = f", День народження: {record.birthday.value}" if record.birthday else ""
                print(f" {record.name.value}, {phones}{birthday_info}")
        else:
            print("Ничего не найдено!!!.")

    def do_days_to_birthday(self, line, when=9999):
        name = line.strip().capitalize()
        record = self.book.find(name)
        if record:
            days_until_birthday = record.days_to_birthday()
            if 0 < days_until_birthday < when:
                print(f"До дня народження {name} {record.birthday} залишилось {days_until_birthday} днів")
            elif days_until_birthday == 0:
                print(f"День народження {name} сьогодні!!!")
            elif (days_until_birthday > when or days_until_birthday == -1) and (when != 9999):
                pass
            else:
                print(f"День народження не додано в книгу контактів")

        else:
            print(f"контакт {name} не знайдений")

    def do_when (self, days):
        if not days:
            print ("Введіть 'when' та кількість днів, на які хочете побачити прогноз")
            return
        if not days.isdigit():
            print ("Введіть кількість днів числовим значенням")
            return
        for record in self.book:
            self.do_days_to_birthday (record.name.value, int(days))
    
    def do_add_note(self, line):
        data = line.split(',')
        if len(data) < 2:
            print("Недостатньо аргументів. Потрібно ім'я та текст заметки.")
            return

        name = data[0].strip().capitalize()
        note_text = data[1].strip()
        tags = [tag.strip() for tag in data[2:]] if len(data) > 2 else []

        record = self.book.data.get(name)
        if record is None:
            print(f"Контакт з ім'ям {name} не знайдено.")
            return

        if not isinstance(record, NoteRecord):
            print(f"Для контакта {name} не підтримуються нотатки.")
            return

        record.add_note(note_text, tags)
        print(f"Заметка додана до контакта {name}.")

    def do_find_note(self, line):
        name = line.strip().capitalize()
        record = self.book.data.get(name)
        if not record:
            print(f"Контакт з ім'ям {name} не знайдено.")
            return

        if isinstance(record, NoteRecord) and record.notes:
            for note in record.notes:
                print(f"{name}: {note.value} [Tags: {' ,'.join(note.tags)}]")
        else:
            print(f"Для контакта {name} не знайдено нотаток або вони не підтримуються.")

    def do_delete_all_notes(self, line):
        name = input("Введіть ім'я для видалення всіх нотаток: ")
        if name in self.book:
            record = self.book[name]
            if isinstance(record, NoteRecord):
                record.notes.clear()
                print(f"Усі нотатки для {name} було видалено.")
            else:
                print("Для цього контакта нотатки не підтримуються.")
        else:
            print("Контакт не знайдено.")

    def do_edit_note(self, line):
        pass


if __name__ == "__main__":
    controller = Controller()

    # Перевірка на коректність веденого номера телефону setter для value класу Phone.
    phone_field = Phone("1234567890")
    print(phone_field.value)  # Вивід значення через getter

    # спроба встановити не коректний номер телефону
    try:
        phone_field.value = "987-654-321"  # Це не число, викликає ValueError
    except ValueError as e:
        print(e)

    # Перевірка на коректність веденого дня народження setter для value класу Birthday.
    birthday_field = Birthday("1990-01-01")
    print(birthday_field.value)  # Вивід значення через getter

    # спроба встановити не коректне значенне для дня народження
    try:
        birthday_field.value = "1990/01/01"  # Некорректний формат дати, визиває ValueError
    except ValueError as e:
        print(e)

    # Створення нової адресної книги
    book = AddressBook()

    # Створення запису
    max_record = NoteRecord("Max")
    max_record.birthday = Birthday("2011-12-03")
    max_record.add_phone("1234567890")
    max_record.add_phone("7575757575")

    grigi_record = NoteRecord("Grigi")
    grigi_record.add_phone("8098465323")
    grigi_record.add_phone("2345678910")

    selim_record = NoteRecord("Selim")
    selim_record.add_phone("7098461111")
    selim_record.add_phone("5010101010")

    jane_record = NoteRecord("Jane")
    jane_record.add_phone("9876543210")
    jane_record.add_phone("7576541010")

    alex_record = Record("Alex")
    alex_record.add_phone("7834567000")
    alex_record.add_phone("7875757005")


    # Додавання запису до адресної книги
    controller.book.add_record(max_record)
    controller.book.add_record(grigi_record)
    controller.book.add_record(selim_record)
    controller.book.add_record(jane_record)
    controller.book.add_record(alex_record)


    controller.cmdloop()
    # використання ітератора
    for record in book:
        print(record)

    print(">>>>>>>>>>>>>>>>")

    # використання методу для отримання  уявлення для N записей

    for item in book.iterator(item_number=3):
        for record in item:
            print(record)

# >>>load
# Адресна книга відновлена
# >>>add_name kostya
# Контакт з іменем Kostya успішно створено.
# >>>add_note kostya, Hi is student in GoIt, junior


#создание таблиц через РИЧ

# from rich.console import Console
# from rich.table import Table
# from datetime import datetime
# console = Console()

# table = Table(show_header=True, header_style="bold magenta")
# table.add_column('Author')            #создание колонок
# table.add_column("Title")
# table.add_column("Note")
# table.add_column("Date", style="dim", width=12)
# now = datetime.now()                       #берем текущую дату. её надо ещё форматировать чтобы выглядела красиво
# author = input('Input Author:  ')             # Ввод данныз в таблицу через инпуты. 
# title = input('Input Title: ')
# note = input('Input note: ')
# table.add_row(author, title, note, str(now)        #эта функция принимает только строку поэтому время перевести в строку
# )


# console.print(table)                  # Вывод на консоль
