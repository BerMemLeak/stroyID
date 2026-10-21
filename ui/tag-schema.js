const DOCUMENT_TAG_SCHEMA = {
  "version": 2,
  "roles": [
    "СтройконтрольЗаказчика",
    "ПредставительСтроительства",
    "СтройконтрольПодрядчика",
    "Проектировщик",
    "ИсполнительРабот"
  ],
  "fields": {
    "Объект.Наименование": {
      "source": "Карточка объекта",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "Объект.Адрес": {
      "source": "Карточка объекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Объект.Шифр": {
      "source": "Карточка объекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Объект.Договор": {
      "source": "Карточка объекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Шифр": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Код": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Наименование": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Дата": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Наименование": {
      "source": "Настройки комплекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Год": {
      "source": "Настройки комплекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Город": {
      "source": "Настройки комплекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Логотип": {
      "source": "Настройки комплекта",
      "type": "image",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.Наименование": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.КраткоеНаименование": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.ИНН": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.КПП": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.ОГРН": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.Адрес": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.Телефон": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.Email": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.СРО": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Компания.Реквизиты": {
      "source": "Комплект.Компания",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.Наименование": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.КраткоеНаименование": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.ИНН": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.КПП": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.ОГРН": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.Адрес": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.Телефон": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.Email": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.СРО": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Комплект.Получатель.Реквизиты": {
      "source": "Комплект.Получатель",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.Наименование": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.КраткоеНаименование": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.ИНН": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.КПП": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.ОГРН": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.Адрес": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.Телефон": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.Email": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.СРО": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Генподрядчик.Реквизиты": {
      "source": "Участники.Генподрядчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.Наименование": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.КраткоеНаименование": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.ИНН": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.КПП": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.ОГРН": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.Адрес": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.Телефон": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.Email": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.СРО": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Застройщик.Реквизиты": {
      "source": "Участники.Застройщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.Наименование": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.КраткоеНаименование": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.ИНН": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.КПП": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.ОГРН": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.Адрес": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.Телефон": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.Email": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.СРО": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Техзаказчик.Реквизиты": {
      "source": "Участники.Техзаказчик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.Наименование": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.КраткоеНаименование": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.ИНН": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.КПП": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.ОГРН": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.Адрес": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.Телефон": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.Email": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.СРО": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Проектировщик.Реквизиты": {
      "source": "Участники.Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.Наименование": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.КраткоеНаименование": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.ИНН": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.КПП": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.ОГРН": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.Адрес": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.Телефон": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.Email": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.СРО": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.АвторскийНадзор.Реквизиты": {
      "source": "Участники.АвторскийНадзор",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.Наименование": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.КраткоеНаименование": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.ИНН": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.КПП": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.ОГРН": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.Адрес": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.Телефон": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.Email": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.СРО": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Участники.Эксплуатация.Реквизиты": {
      "source": "Участники.Эксплуатация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.Наименование": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.КраткоеНаименование": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.ИНН": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.КПП": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.ОГРН": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.Адрес": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.Телефон": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.Email": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.СРО": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Организация.Реквизиты": {
      "source": "Подписанты.СтройконтрольЗаказчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.Наименование": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.КраткоеНаименование": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.ИНН": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.КПП": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.ОГРН": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.Адрес": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.Телефон": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.Email": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.СРО": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Организация.Реквизиты": {
      "source": "Подписанты.ПредставительСтроительства.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.Наименование": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.КраткоеНаименование": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.ИНН": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.КПП": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.ОГРН": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.Адрес": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.Телефон": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.Email": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.СРО": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Организация.Реквизиты": {
      "source": "Подписанты.СтройконтрольПодрядчика.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.Наименование": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.КраткоеНаименование": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.ИНН": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.КПП": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.ОГРН": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.Адрес": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.Телефон": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.Email": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.СРО": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Организация.Реквизиты": {
      "source": "Подписанты.Проектировщик.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.Наименование": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.КраткоеНаименование": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.ИНН": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.КПП": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.ОГРН": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.Адрес": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.Телефон": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.Email": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.СРО": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Организация.Реквизиты": {
      "source": "Подписанты.ИсполнительРабот.Организация",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Наименование": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Дата": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Начало": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Окончание": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Номер": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Дата": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Работы": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.МестоРабот": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.РабочаяДокументация": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Начало": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Окончание": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Нормативы": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.ПоследующиеРаботы": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Материалы": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.ПодтверждающиеДокументы": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Приложения": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.ДополнительныеСведения": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.КоличествоЭкземпляров": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Номер": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Дата": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Материал": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Количество": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Наименование": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Номер": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Дата": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Тип": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.ДокументыКачества": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Примечание": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Содержание": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.ФИО": {
      "source": "Назначение роли: СтройконтрольЗаказчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.ФамилияИнициалы": {
      "source": "Назначение роли: СтройконтрольЗаказчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Должность": {
      "source": "Назначение роли: СтройконтрольЗаказчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.ОснованиеПолномочий": {
      "source": "Назначение роли: СтройконтрольЗаказчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.НРС": {
      "source": "Назначение роли: СтройконтрольЗаказчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольЗаказчика.Описание": {
      "source": "Назначение роли: СтройконтрольЗаказчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.ФИО": {
      "source": "Назначение роли: ПредставительСтроительства",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.ФамилияИнициалы": {
      "source": "Назначение роли: ПредставительСтроительства",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Должность": {
      "source": "Назначение роли: ПредставительСтроительства",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.ОснованиеПолномочий": {
      "source": "Назначение роли: ПредставительСтроительства",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.НРС": {
      "source": "Назначение роли: ПредставительСтроительства",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ПредставительСтроительства.Описание": {
      "source": "Назначение роли: ПредставительСтроительства",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.ФИО": {
      "source": "Назначение роли: СтройконтрольПодрядчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.ФамилияИнициалы": {
      "source": "Назначение роли: СтройконтрольПодрядчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Должность": {
      "source": "Назначение роли: СтройконтрольПодрядчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.ОснованиеПолномочий": {
      "source": "Назначение роли: СтройконтрольПодрядчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.НРС": {
      "source": "Назначение роли: СтройконтрольПодрядчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.СтройконтрольПодрядчика.Описание": {
      "source": "Назначение роли: СтройконтрольПодрядчика",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.ФИО": {
      "source": "Назначение роли: Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.ФамилияИнициалы": {
      "source": "Назначение роли: Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Должность": {
      "source": "Назначение роли: Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.ОснованиеПолномочий": {
      "source": "Назначение роли: Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.НРС": {
      "source": "Назначение роли: Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.Проектировщик.Описание": {
      "source": "Назначение роли: Проектировщик",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.ФИО": {
      "source": "Назначение роли: ИсполнительРабот",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.ФамилияИнициалы": {
      "source": "Назначение роли: ИсполнительРабот",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Должность": {
      "source": "Назначение роли: ИсполнительРабот",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.ОснованиеПолномочий": {
      "source": "Назначение роли: ИсполнительРабот",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.НРС": {
      "source": "Назначение роли: ИсполнительРабот",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Подписанты.ИсполнительРабот.Описание": {
      "source": "Назначение роли: ИсполнительРабот",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Ведомость.Наименование": {
      "source": "Ведомость текущего акта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Ведомость.Проект": {
      "source": "Ведомость текущего акта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Ведомость.Основание": {
      "source": "Ведомость текущего акта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Ведомость.Примечание": {
      "source": "Ведомость текущего акта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Реестр.Текст": {
      "source": "Фактический состав комплекта",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Дата.День": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Дата.Месяц": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Дата.МесяцПрописью": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Дата.Год": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Дата.Прописью": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": true,
      "empty": "error"
    },
    "АОСР.Начало.День": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Начало.Месяц": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Начало.МесяцПрописью": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Начало.Год": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Начало.Прописью": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Окончание.День": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Окончание.Месяц": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Окончание.МесяцПрописью": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Окончание.Год": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АОСР.Окончание.Прописью": {
      "source": "Текущий АОСР / АООК",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Дата.День": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Дата.Месяц": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Дата.МесяцПрописью": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Дата.Год": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "АИК.Дата.Прописью": {
      "source": "Текущий акт входного контроля",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Дата.День": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Дата.Месяц": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Дата.МесяцПрописью": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Дата.Год": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Документ.Дата.Прописью": {
      "source": "Текущий документ",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Дата.День": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Дата.Месяц": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Дата.МесяцПрописью": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Дата.Год": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Дата.Прописью": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Начало.День": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Начало.Месяц": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Начало.МесяцПрописью": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Начало.Год": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Начало.Прописью": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Окончание.День": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Окончание.Месяц": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Окончание.МесяцПрописью": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Окончание.Год": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Выполнение.Окончание.Прописью": {
      "source": "Выполнение текущего документа",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Дата.День": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Дата.Месяц": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Дата.МесяцПрописью": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Дата.Год": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Раздел.Дата.Прописью": {
      "source": "Текущий раздел",
      "type": "text",
      "required": false,
      "empty": "blank"
    },
    "Реестр.Номер": {
      "source": "Повторяемые строки: Реестр",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Реестр.Тип": {
      "source": "Повторяемые строки: Реестр",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Реестр.Наименование": {
      "source": "Повторяемые строки: Реестр",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Реестр.Номер_Дата": {
      "source": "Повторяемые строки: Реестр",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Реестр.Листы": {
      "source": "Повторяемые строки: Реестр",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Реестр.КоличествоСтраниц": {
      "source": "Повторяемые строки: Реестр",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Номер": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_1": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_2": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_3": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_4": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_5": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_6": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_7": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_8": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_9": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_10": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_11": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_12": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_13": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_14": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_15": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_16": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_17": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_18": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_19": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Строки.Колонка_20": {
      "source": "Повторяемые строки: Строки",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Фото.Номер": {
      "source": "Повторяемые строки: Фото",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Фото.Подпись": {
      "source": "Повторяемые строки: Фото",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Фото.Изображение": {
      "source": "Повторяемые строки: Фото",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Объемы.Номер": {
      "source": "Повторяемые строки: Объемы",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Объемы.Наименование": {
      "source": "Повторяемые строки: Объемы",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Объемы.Место": {
      "source": "Повторяемые строки: Объемы",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Объемы.Единица": {
      "source": "Повторяемые строки: Объемы",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Объемы.Количество": {
      "source": "Повторяемые строки: Объемы",
      "type": "collection",
      "required": false,
      "empty": "blank"
    },
    "Лист.Надпись": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Ширина": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка1.ФамилияИнициалы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Лист.Формат": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Лист.МестоРабот": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Приложение.Номер": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Высота": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Высота_Рамки": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Наименование": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка5.Роль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Номер": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка2.Роль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка3.ФамилияИнициалы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Y_Надпись": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка2.ФамилияИнициалы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Шифр": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.X_Приложение": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Лист.Всего": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Приложение.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Здание": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка6.Роль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Приложение.Основание": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка4.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Лист.Номер": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка6.ФамилияИнициалы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Стадия": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.X_Центр_Листа": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка3.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Y_Инвентарных_Граф": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Схема.Работы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка5.ФамилияИнициалы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Y_Центр_Листа": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Разработал": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.X_Формат": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка5.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка6.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.X_Надпись": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Ширина_Надписи_Листа": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Нормоконтроль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка1.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка2.Дата": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Ширина_Рамки": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка1.Роль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка4.ФамилияИнициалы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка4.Роль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Строка3.Роль": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Лист.НомерСхемы": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Рамка.Проверил": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Геометрия.Y_Формат": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    },
    "Приложение.Документ": {
      "source": "Рамка / исходный лист чертежа",
      "type": "frame",
      "required": false,
      "empty": "blank"
    }
  },
  "collections": {
    "Реестр": [
      "Номер",
      "Тип",
      "Наименование",
      "Номер_Дата",
      "Листы",
      "КоличествоСтраниц"
    ],
    "Строки": [
      "Номер",
      "Колонка_1",
      "Колонка_2",
      "Колонка_3",
      "Колонка_4",
      "Колонка_5",
      "Колонка_6",
      "Колонка_7",
      "Колонка_8",
      "Колонка_9",
      "Колонка_10",
      "Колонка_11",
      "Колонка_12",
      "Колонка_13",
      "Колонка_14",
      "Колонка_15",
      "Колонка_16",
      "Колонка_17",
      "Колонка_18",
      "Колонка_19",
      "Колонка_20"
    ],
    "Фото": [
      "Номер",
      "Подпись",
      "Изображение"
    ],
    "Объемы": [
      "Номер",
      "Наименование",
      "Место",
      "Единица",
      "Количество"
    ]
  }
};
