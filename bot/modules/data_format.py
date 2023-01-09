import random

    
def random_dict(data: dict[str, int]) -> int | dict:
    """ Предоставляет общий формат данных, подерживающий 
        случайные и статичные числа.
    
    Примеры словаря:
        >>> {"min": 1, "max": 2, "type": "random"}
        >>> {"act": 1, "type": "static"}
    """

    if 'type' in data.keys():
        if data["type"] in ["static", "random"]:

            if data["type"] == "static":
                return data['act']

            elif data["type"] == "random":
                if data['min'] >= data['max']:
                    return 0
                else:
                    return random.randint(data['min'], data['max'])
            else:
                return 0
        else:
            return data
    else:
        return data


if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")