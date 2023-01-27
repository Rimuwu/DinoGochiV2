import asyncio
from bot.modules.logs import log

task_dict = {}

def add_task(function, units: int=1, wait: int=0):
    """Добавить для функции таймер выполнения 
        time_type: str - second / minute / hour
        units: int - повторение каждые ? секунд / минут / часов
    """
    
    if function in task_dict:
        raise Exception(f'Функция {function.__name__} добавлена повторно.')
        
    task_dict[function] = units, wait
    return True

async def task_executor(function, seconds: int, wait: int=0):
    """Исполнитель всех задач с обработчиком ошибок и созданием потока
       seconds: int - количество секунд между повторами
       wait: int - ожидание перед стартом
    """
    await asyncio.sleep(wait)

    while True:
        try:
            await function()
        except Exception as error:
            log(prefix=F"{function.__name__} error", message=str(error), lvl=3)
        
        await asyncio.sleep(seconds)