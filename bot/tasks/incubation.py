from bot.tasks.taskmanager import add_task

async def incuation():
    print('incubation')

async def inc():
    print('inc')



if __name__ != '__main__':
    add_task(incuation, 1, 3)
    add_task(inc, 5)