

def get_events():
    return []

def get_one_event(event_type: str='', event_id: int=0, alternative: str='standart'):
    events = get_events()

    if events:
        return events[0]
    else:
        return alternative