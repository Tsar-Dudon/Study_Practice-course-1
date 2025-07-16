import asyncio
from aiogram import Bot, Dispatcher
from handlers import router, cur
from datetime import datetime


bot=Bot(token="")
dp=Dispatcher()

prev_date = '2025-07-14'

async def Notifications():
    global prev_date
    while True:
        today = datetime.now().strftime("%Y-%m-%d")
        if today != prev_date:
            prev_date = today
            cur.execute("""SELECT userid, task, deadline FROM users WHERE deadline >= ? ORDER BY deadline LIMIT 5""", (today,))
            tasks = cur.fetchall()
            for task in tasks:
                try:
                    await bot.send_message(task[0], f"Напоминаю про задачу '{task[1]}', дедлайн - {task[2]}")
                except Exception as e:
                    print(f"Ошибка при отправке сообщения: {e}")
        await asyncio.sleep(86400) 
             

dp.include_router(router)


async def main():
    await bot.delete_webhook(drop_pending_updates = True)
    asyncio.create_task(Notifications())
    await dp.start_polling(bot)

asyncio.run(main())
