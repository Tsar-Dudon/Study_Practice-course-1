from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from  aiogram.fsm.context import FSMContext
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users(
    userid INTEGER,
    task TEXT,
    deadline TEXT);
""")
conn.commit()

router = Router()

@router.message(CommandStart())
async def command_start(message:types.Message):
    await message.answer('''Салам родной! Вот что я умею:
/add_task - добавить задачу
/my_tasks - список дел
/deadlines - ближайшие дедлайны''')
    
    
class addTask(StatesGroup):
    name = State()
    when = State()

@router.message(StateFilter(None), Command('add_task'))
async def command_add_task(message:types.Message, state: FSMContext):
    await state.set_state(addTask.name)
    await message.answer('Введите задачу(введите "/cancel" или "отмена" для отмены)')

@router.message(StateFilter('*'), Command('cancel'))
@router.message(StateFilter('*'), F.text.casefold() == 'отмена')
async def command_cancel(message:types.Message, state: FSMContext):
    if (await state.get_state()) is None:
        return
    await message.answer('Задача отменена')
    await state.clear()

@router.message(addTask.name, F.text)
async def command_add_name(message:types.Message, state: FSMContext):
    await state.update_data(name = message.text)
    await message.answer('Введите дедлайн в формате YYYY-MM-DD')
    await state.set_state(addTask.when)

@router.message(addTask.when, F.text)
async def command_last(message:types.Message, state: FSMContext):
    await state.update_data(when = message.text)
    data = await state.get_data()
    task_name = data['name']  
    deadline = message.text   
    cur.execute("INSERT INTO users (userid, task, deadline) VALUES (?,?,?)", (message.chat.id, task_name, deadline))
    conn.commit()
    await message.answer('Задача записана')
    await state.clear()


@router.message(Command('my_tasks'))
async def command_my_tasks(message:types.Message):
    cur.execute("SELECT task, deadline FROM users WHERE userid = ?", (message.chat.id,))
    tasks = cur.fetchall()
    if not tasks:
        await message.answer("У вас пока нет задач")
        return
    response = "Ваши задачи:\n"
    for task in range(len(tasks)):
        response += f"{task+1}. {tasks[task][0]} (до {tasks[task][1]})\n"
    await message.answer(response)

@router.message(Command('deadlines'))
async def command_deadlines(message:types.Message):
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""SELECT task, deadline FROM users WHERE userid = ? AND deadline >= ? ORDER BY deadline LIMIT 5""", (message.chat.id, today))
    upcoming_tasks = cur.fetchall()
    if not upcoming_tasks:
        await message.answer("Ближайшие дедлайны не найдены")
        return
    response = "Ближайшие дедлайны:\n"
    for task in upcoming_tasks:
        response += f"• {task[0]} - {task[1]}\n"
    await message.answer(response)


class DeleteTask(StatesGroup):
    task_number = State()

@router.message(Command('delete_task'))
async def command_delete_task(message: types.Message, state: FSMContext):
    cur.execute("SELECT rowid, task, deadline FROM users WHERE userid = ? ORDER BY deadline", (message.chat.id,))
    tasks = cur.fetchall()
    if not tasks:
        await message.answer("У вас нет задач для удаления!")
        return
    task_list = "Выберите номер задачи для удаления:\n"
    for index, task in enumerate(tasks, start=1):
        task_list += f"{index}. {task[1]} (до {task[2]})\n"
    await message.answer(task_list)
    await state.set_state(DeleteTask.task_number)
    await state.update_data(tasks=tasks)  

@router.message(DeleteTask.task_number, F.text)
async def process_delete_task(message: types.Message, state: FSMContext):
    try:
        selected_index = int(message.text)
        data = await state.get_data()
        tasks = data['tasks']
        if 1 <= selected_index <= len(tasks):
            task_id = tasks[selected_index-1][0]
            cur.execute("DELETE FROM users WHERE rowid = ? AND userid = ?", (task_id, message.chat.id))
            conn.commit()
            await message.answer(f"Задача '{tasks[selected_index-1][1]}' удалена!")
        else:
            await message.answer("Пожалуйста, введите номер из списка!")
    except ValueError:
        await message.answer("Пожалуйста, введите число!")
    finally:
        await state.clear()

