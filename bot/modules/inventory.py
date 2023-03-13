from bot.modules.data_format import chunks
from bot.modules.item import get_data, get_name, is_standart, item_code


def inventory_pages(items: list[dict], lang: str = 'en', 
                    view: list[int] = [2, 3], type_filter: list[str] = [],
                    item_filter: list[str] = []):
    """ Создаёт и сортируем страницы инвентаря

    type_filter - если не пустой то отбирает предметы по их типу
    item_filter - если не пустой то отбирает предметы по id
    !: Предмет добавляется если соответствует хотя бы одному фильтру

    item: {
        items_data: {
            item_id: str
            abilities: dict (может отсутствовать)
        },
        count: int
    }
    """
    items_data, items_names = {}, []
    horizontal, vertical = view

    for base_item in items:
        item = base_item['item'] # Сам предмет
        data = get_data(item['item_id']) # Дата из json
        add_item = False
        
        # Если предмет найден в базе
        if data:
            # Проверка на соответсвие фильтров
            if not (type_filter or item_filter):
                # Фильтры пустые
                add_item = True
            else:
                if data['type'] in type_filter:
                    add_item = True
                if item['item_id'] in item_filter:
                    add_item = True
            
            # Если предмет показывается на страницах
            if add_item:
                name = get_name(item['item_id'], lang)
                count = base_item['count']
                standart = is_standart(item)

                if standart:
                    end_name = f"{name} x{count}"
                else:
                    code = item_code(item, False)
                    end_name = f"{name} ({code}) x{count}"

                items_data[end_name] = item
                
    items_names = list(items_data.keys())
    items_names.sort()

    # Создаёт список, повторяюзий панель инвентаря
    pages = chunks(chunks(items_names, horizontal), vertical)

    # Добавляет пустые панели для поддержания структуры
    for i in pages:
        if len(i) != vertical:
            for _ in range(vertical - len(i)):
                i.append([' ' for _ in range(horizontal)])
    
    # Нужно, чтобы стрелки корректно отображались
    if horizontal < 3:
        horizontal = 3

    return pages, horizontal, items_data, items_names