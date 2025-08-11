"""MT940 Parser Module"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from datetime import date
from datetime import datetime
from enum import Enum
from io import StringIO, TextIOWrapper
from typing import List, Generator, Any, Optional, Union, Tuple
from warnings import warn

__all__ = ['MT940', 'Transaction', 'Section', 'Balance']

TRANSACTION_RE = re.compile(
    r'''
    (?P<date>\d{6})
    (?P<booking>\d{4})?
    (?P<sign>D|C|RC|RD)
    (?P<code>\w)??  # ING skips this mandatory field
    (?P<amount>(\d|,){1,15})
    (?P<id>\w{4})
    (?P<reference>.{0,34})''',
    re.VERBOSE,
)

IS_BASE64 = re.compile(r'^([A-Za-z0-9+/]{4}|[\n\r])*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$')

LINE_RE = re.compile(r'^:(\d+\w?):(.*)|[\n\r]$')

WHITESPACE_RE = re.compile(r'[\n\r]')

MAX_BOOKING_DAYS = 60


class BaseData:
    DATE_FORMAT = '%y%m%d'

    @classmethod
    def _parse_date(cls, date_str):
        return datetime.strptime(date_str, cls.DATE_FORMAT).date()

    @classmethod
    def _parse_amount(cls, amount: str, sign: str = 'C'):
        amount = float(amount.replace(',', '.'))
        if sign in ('D', 'RC'):
            return -amount
        return amount


class Section(Enum):
    header = '20'
    account_iban = '25'
    information = '28'
    statement_number = '28C'
    start_balance = '60F'
    transaction = '61'
    description = '86'
    end_balance = '62F'
    available_balance = '64'
    unknown = None

    @classmethod
    def _missing_(cls, value):
        warn(f'Unknown Section: {value}')
        return Section.unknown


@dataclass
class Transaction(BaseData):
    """MT940 Transaction"""

    transaction_date: date
    booking_date: date
    amount: float
    id_: str
    reference: str
    institution_reference: str
    additional_data: str
    description: Optional[str] = field(default_factory=str)
    title: Optional[str] = field(default_factory=str)
    partner: Optional[str] = field(default_factory=str)
    account_number: Optional[str] = field(default_factory=str)

    @classmethod
    def create_from_str(cls, transaction_str: str) -> Transaction:
        lines = transaction_str.splitlines()
        if len(lines) == 1:
            (transaction,) = lines
            additional_data = None
        else:
            transaction, additional_data = lines

        transaction = TRANSACTION_RE.match(transaction)

        booking_date = transaction_date = cls._parse_date(transaction.group('date'))

        if transaction.group('booking'):
            booking_date = cls._parse_date(transaction.group('date')[:2] + transaction.group('booking'))

            # protection against wrong booking date and the end of the year
            # date str `2312300102` should be parse like: tx date `2023-12-30` and booking date `2024-01-02`, not `2023-01-02`
            if (transaction_date - booking_date).days >= MAX_BOOKING_DAYS:
                warn(
                    f'Probably wrong booking date: {booking_date} for transaction date: {transaction_date}. '
                    f'Adding 1 year.'
                )

                booking_date = booking_date.replace(year=booking_date.year + 1)

        amount = cls._parse_amount(transaction.group('amount'), transaction.group('sign'))
        id_ = transaction.group('id')
        reference = transaction.group('reference')
        reference, _, institution_reference = reference.partition('//')
        reference = False if reference == 'NONREF' else reference

        return Transaction(
            transaction_date, booking_date, amount, id_, reference, institution_reference, additional_data
        )


@dataclass
class Balance(BaseData):
    """Balance with date and currency aware amount"""

    balance_date: date
    amount: float
    currency: str

    @classmethod
    def create_from_str(cls, balance_str: str) -> Balance:
        balance_date = cls._parse_date(balance_str[1:7])
        amount = cls._parse_amount(balance_str[10:], balance_str[0])
        return Balance(balance_date=balance_date, amount=amount, currency=balance_str[7:10])


@dataclass
class Statement:
    """Single MT940 Statement"""

    header: str = None
    account_iban: str = None
    statement_number: str = None
    transactions: List[Transaction] = field(default_factory=list)
    start_balance: Optional[Balance] = None
    end_balance: Optional[Balance] = None
    available_balance: Optional[Balance] = None
    description: Optional[str] = ''


class MT940:
    """MT940 Parser Class"""

    statements: List[Statement] = []

    def __init__(self, content: Union[TextIOWrapper, str], encoding: Optional[str] = 'iso-8859-2') -> None:
        if isinstance(content, str):
            if IS_BASE64.match(content):
                try:
                    content = base64.b64decode(content).decode(encoding)
                except UnicodeDecodeError:
                    return
            content = StringIO(content)
        self._parse(content)

    def _parse(self, content: TextIOWrapper) -> None:
        statement = None
        transaction = None
        for section, section_info in self._read_lines(content):
            if section == Section.header:
                statement = Statement()
                self.statements.append(statement)
            elif statement and section == Section.transaction:
                transaction = Transaction.create_from_str(section_info)
                statement.transactions.append(transaction)
            elif statement and section == Section.description:
                if statement.end_balance:
                    statement.description += section_info
                elif transaction is not None:
                    transaction.description = section_info
                    # noinspection PyTypeChecker
                    section_info = dict(
                        (z.strip() for z in (x.split(':', maxsplit=1) if ':' in x else ('_', x)))
                        for x in section_info.split(';')
                    )

                    if section_info:
                        transaction.partner = section_info.get('OD') or section_info.get('DLA')
                        transaction.account_number = section_info.get('Z RACH.', section_info.get('NA RACH.'))
                        transaction.title = section_info.get('TYT.')
                else:
                    warn('?')
            elif statement and section in (Section.start_balance, Section.end_balance, Section.available_balance):
                balance = Balance.create_from_str(section_info)
                setattr(statement, section.name, balance)
                if section == Section.start_balance and statement.statement_number:
                    statement.statement_number = f'{statement.statement_number}/{balance.balance_date.year}'
            else:
                if statement and section != Section.unknown:
                    setattr(statement, section.name, section_info)
                else:
                    warn(f'section={section}, name={section.name}, section_info={section_info}')

    @staticmethod
    def _split_line(line: str) -> Tuple[Section, str]:
        re_match = LINE_RE.match(line)
        if re_match:
            section, section_info = re_match.groups()
            return Section(section), section_info

    @staticmethod
    def _read_lines(content: TextIOWrapper) -> Generator[str, Any, None]:
        gen = (line for line in content if not line.startswith('-'))

        previous_line = None
        while True:
            if previous_line is not None:
                buf_line = previous_line
                previous_line = None
            else:
                try:
                    buf_line = next(gen)
                except StopIteration:
                    break

            splited_line = MT940._split_line(buf_line)

            if splited_line:
                if splited_line[0] == Section.description:
                    description_buf = buf_line

                    next_line = next(gen)

                    while not MT940._split_line(next_line):
                        description_buf += next_line
                        next_line = next(gen)
                    else:
                        previous_line = next_line

                    description_buf = WHITESPACE_RE.sub('', description_buf)
                    splited_line = MT940._split_line(description_buf)

                yield splited_line

    def __str__(self, *args, **kwargs):
        return f'{self.__class__.__name__} statements={self.statements}'

    def __repr__(self, *args, **kwargs):
        return f'{self.__class__.__name__} statements={self.statements}'
