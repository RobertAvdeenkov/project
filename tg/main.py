import asyncio
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import models


TOKEN='8855129809:AAEoIdAeTPTPw5oXA0aSgn4WrQXkvHkRvK4'
engine=create_async_engine('postgresql+asyncpg://neondb_owner:npg_L7yqXFH3EfZh@ep-sweet-union-axsilaf7-pooler.c-4.us-east-2.aws.neon.tech/neondb', connect_args={'ssl':True})
SessionLocal=sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) #type:ignore

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Здравсвуйте! Введите свой ник') #type:ignore

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):
    name=update.message.text.strip() #type:ignore
    async with SessionLocal() as db: #type:ignore
        ex=select(models.User).filter(models.User.name==name)
        result=(await db.execute(ex)).first()
        if result:
            await update.message.reply_text('Такой пользователь есть!')
            keyboard = [
                [InlineKeyboardButton("1 уровень — 79 ₽", callback_data="level_1")],
                [InlineKeyboardButton("2 уровень — 169 ₽", callback_data="level_2")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Выбери уровень:',reply_markup=reply_markup)
        else:
            await update.message.reply_text('Такого пользователя нет! Зарегистрируйтесь на сайте или перепроверьте написанный ник')

async def button_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    await query.answer() #type:ignore
    level=query.data #type:ignore
    await query.edit_message_text(f'Вы выбрали {level}. Переведите на карту Юмани: 1234 5678 9012 3456. В комментарии ОБЯЗАТЕЛЬНО укажите ник и уровень. Просим набраться терпения, так как премиум может быть активирован в течении 1-2 дня')


def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start',start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__=='__main__':
    main()