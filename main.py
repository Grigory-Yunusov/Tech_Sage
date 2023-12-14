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

        # self.phones = [p for p in self.phones if p.value != phone]

        # for p in self.phones:
        #     if p.value == phone:
        #         self.phones.remove(p)
        #         break

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

    # def __str__(self):
    #     return f"Contact name: {self.name._value}, phones: {'; '.join(p.value for p in self.phones)}"

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

    def __init__(self, file="adress_book.pkl"):
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


    # if __name__ == "__main__":
    #
    #     def find(self, term):
    #         matching_records = self.find_by_term(term)
    #         if matching_records:
    #             return matching_records
    #         else:
    #             return None

class Controller(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.book = AddressBook()
        self.prompt = ">>>"
        self.intro = "Ласкаво просимо до Адресної Книги"

    def do_exit(self, arg):
        self.book.dump()
        print("Вихід...")
        return True

    def do_save(self, arg):
        self.book.dump()
        print("Адресна книга збережена!")

    def do_load(self, arg):
        self.book.load()
        print("Адресна книга відновлена")

    def do_add(self, line):
        data = line.split(",")
        name = data[0].strip().capitalize()
        phones = [phone.strip() for phone in data[1:3]]
        birthday = data[3].strip() if len(data) > 3 else None
        try:
            record = Record(name)
            for phone in phones:
                record.add_phone(phone)
            if birthday:
                record.add_birthday(birthday)

            self.book.add_record(record)
            print("Новий контакт успішно збережено!")
        except ValueError as e:
            print(f"помилка при створенні контакту: {e}")



    def do_list(self, arg):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            for record_id, record in self.book.data.items():
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = f", День народження: {record.birthday.value}" if record.birthday else ""
                print(f"{record_id}: {record.name.value}, {phones}{birthday_info}")

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

    def do_birthday(self, line):
        name = line.strip().capitalize()
        record = self.book.find(name)
        if record:
            days_until_birthday = record.days_to_birthday()
            if days_until_birthday > 0:
                print(f"до дня народження контакту {name}, залишилось {days_until_birthday} днів")
            elif days_until_birthday == 0:
                print(f"День народження контакту {name} сьогодні!!!")
            else:
                print(f"день народження не додано в книгу контактів")

        else:
            print(f"контакт {name} не знайдений")



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
    john_record = Record("John")
    john_record.birthday = Birthday("2011-12-03")
    john_record.add_phone("1234567890")
    john_record.add_phone("7575757575")

    grigi_record = Record("Grigi")
    grigi_record.add_phone("8098465323")
    grigi_record.add_phone("2345678910")

    selim_record = Record("Selim")
    selim_record.add_phone("7098461111")
    selim_record.add_phone("5010101010")

    jane_record = Record("Jane")
    jane_record.add_phone("9876543210")
    jane_record.add_phone("7576541010")

    alex_record = Record("Alex")
    alex_record.add_phone("7834567000")
    alex_record.add_phone("7875757005")

    # Додавання запису до адресної книги
    controller.book.add_record(john_record)
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

    # record_with_birthday = Record("John", "2023-01-15")
    # days_until_birthday = record_with_birthday.days_to_birthday()
    # print(f"До дня народження залишилось {days_until_birthday} днів.")
    #
    # print(">>>>>>>>>>>>>>>>")
    #
    # search_term_1 = "7575"
    # results_1 = controller.book.find(search_term_1)
    #
    # print(f"результат для пошуку: '{search_term_1}':")
    # for result in results_1:
    #     print(result)



# Ласкаво просимо до Адресної Книги
# >>>add ron,1234567890,1992-12-12
# помилка при створенні контакту: Phone must be a string containing only digits.
# >>>add ron, 1234567890,0987654321
# Новий контакт успішно збережено!
# >>>add roki, 1234567890,0987654321, 1992-12-12
# Новий контакт успішно збережено!