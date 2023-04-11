import logging
import traceback
from time import strftime

from colorama import Fore, Style

from bot.config import conf

logging.basicConfig(
    level=logging.INFO,
    filename=f"{conf.logs_dir}/{strftime('%Y %m-%d %H.%M.%S')}.log",
    filemode="w", encoding='utf-8',
    format="%(asctime)s %(levelname)s %(message)s"
)

def log(message: str, lvl: int = 1, prefix: str = 'Бот') -> None:
    """
    LVL: \n
    0 - debug (активируется в config)\n
    1 - info\n
    2 - warning\n
    3 - error\n
    4 - critical
    """
    
    if lvl == 0:
        if conf.debug:
            logging.info(f'DEBUG: {message}')
            print(Fore.CYAN + f"{strftime('%Y %m-%d %H.%M.%S')} {prefix}: {message}" + Style.RESET_ALL)
    elif lvl == 1:
        logging.info(message)
        print(Fore.GREEN + f"{strftime('%Y %m-%d %H.%M.%S')} {prefix}: {message}" + Style.RESET_ALL)
    elif lvl == 2:
        logging.warning(message)
        print(Fore.BLUE + f"{strftime('%Y %m-%d %H.%M.%S')} {prefix}: {message}" + Style.RESET_ALL)
    elif lvl == 3:
        logging.error(message)
        print(Fore.YELLOW + f"{strftime('%Y %m-%d %H.%M.%S')} {prefix}: {message}" + Style.RESET_ALL)
    else:
        logging.critical(message)
        print(Fore.RED + f"{strftime('%Y %m-%d %H.%M.%S')} {prefix}: {message}" + Style.RESET_ALL)