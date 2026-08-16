from fastapi import FastAPI,Body,APIRouter,Form,Depends,Request,HTTPException,Query,Cookie
from database import get_db
from models import Base,Message
from fastapi.responses import FileResponse,RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from sqlalchemy import select,desc
from models import*
from auth import*

router=APIRouter()

@router.get('/')
def main():
    return FileResponse('templates/reglog.html')

@router.post('/reglog')
async def reglog(data=Body(), db:AsyncSession=Depends(get_db)):
    ex=select(User).filter(User.name==data['name'])
    execute=await db.execute(ex)
    result=execute.first()
    print(result)
    if not(result):
        target=User(name=data['name'], password=bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode())
        db.add(target)
        await db.commit()
        await db.refresh(target)
    elif not(bcrypt.checkpw(data['password'].encode(), result[0].password.encode())):
        raise HTTPException(401,'Неверный логин или пароль')
    else: target=result[0]
    token=create_token(str(target.name))
    return {'status':'ok', 'redirect_url':f'/mainRED?token={token}'}


@router.get('/mainRED')
def mainRED(token=Query()):
    response=RedirectResponse('/mainpage')
    response.set_cookie(key='token',value=token, max_age=3600, path='/')
    return response

@router.get('/mainpage')
async def root(request:Request,db:AsyncSession=Depends(get_db), token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/messages.html')

@router.post('/messagesSHOW')
async def show(db:AsyncSession=Depends(get_db), token=Cookie()):
    name=get_by_token(token)
    ex=select(Message).order_by(desc(Message.likes_count), desc(Message.created_at))
    result=await (db.execute(ex))
    res=result.all()
    if not res:
        return {'message':'Сообщений пока нет :('}
    print(res)
    txt=''
    for i in res:
        target=i[0]
        ex=select(User).filter(User.id==target.user_id)
        result=await (db.execute(ex))
        user=result.first()[0] #type:ignore
        print('#ffcc00' if user.pro==True else '#15590d')
        txt+=f'''
        <div class="message">
            <div class="category">{target.category}</div>
            <strong class="{'premium' if user.pro==True else ''}">{f'{target.name} 🌟' if user.pro==True else target.name}</strong> — {target.text}
            <div class="date">{target.created_at}</div>
            <p></p>
            <strong>{target.likes_count} лайков</strong>
            <p></p>
            <button onclick="like({target.id})">Поставить лайк</button>
            <button onclick="unlike({target.id})">Убрать лайк</button>
        </div>
        '''
    return {'message':txt}

@router.get('/feedback')
async def feedback():
    return FileResponse('templates/feedback.html')

@router.post('/feedback')
async def send(name=Form(...), school=Form(...), category=Form(...), text=Form(...), db:AsyncSession=Depends(get_db), token=Cookie()):
    nam=get_by_token(token)
    ex=select(User).filter(User.name==nam)
    execute=await db.execute(ex)
    res=execute.first()[0]#type:ignore
    count=0
    if res.pro==True:count=5
    txt=''
    for index,i in enumerate(text):
        if index%70==0:
            txt+='<br>'+i
        else:
            txt+=i
    target=Message(name=name, school=school, category=category,text=txt, user_id=res.id, likes_count=count)
    db.add(target)
    await db.commit()
    return RedirectResponse('/mainpage', status_code=303)

@router.post('/like')
async def like(data=Body(), db:AsyncSession=Depends(get_db), token=Cookie()):
    name=get_by_token(token)
    ex=select(User).filter(User.name==name)
    result=await (db.execute(ex))
    res=result.first()
    if not(res):
        raise HTTPException(401, 'Такого пользователя нету!')
    user=res[0]

    ex=select(Like).filter(Like.user_id==user.id, Like.message_id==data['id'])
    result=await (db.execute(ex))
    res=result.first()
    if res:
        raise HTTPException(400,'Лайк уже поставлен')
    target=Like(user_id=user.id, message_id=data['id'])


    ex=select(Message).filter(Message.id==data['id'])
    result=await (db.execute(ex))
    res=result.first()
    post=res[0] #type:ignore
    if user.pro==True:
        post.likes_count+=5
    else:
        post.likes_count+=1

    db.add(target)
    await db.commit()


@router.delete('/unlike')
async def unlike(data=Body(), db:AsyncSession=Depends(get_db), token=Cookie()):
    name=get_by_token(token)
    ex=select(User).filter(User.name==name)
    result=await (db.execute(ex))
    res=result.first()
    if not(res):
        raise HTTPException(401, 'Такого пользователя нету!')
    user=res[0]

    ex=select(Like).filter(Like.user_id==user.id, Like.message_id==data['id'])
    result=await (db.execute(ex))
    res=result.first()
    if not(res):
        raise HTTPException(400,'Лайк еще не поставлен')
    target=res[0]
    ex=select(Message).filter(Message.id==data['id'])
    result=await (db.execute(ex))
    res=result.first()
    post=res[0] #type:ignore
    if user.pro==True:
        post.likes_count-=5
    else:
        post.likes_count-=1

    if post.likes_count<0: post.likes_count=0

    await db.delete(target)
    await db.commit()


@router.get('/promo')
def promoMENU(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/promo.html')

@router.post('/enter')
async def enter(token=Cookie(), promo=Form(...), db:AsyncSession=Depends(get_db)):
    name=get_by_token(token)
    ex=select(User).filter(User.name==name)
    result=await (db.execute(ex))
    res=result.first()
    if not(res):
        return RedirectResponse('/mainpage', status_code=303)
    user=res[0]
    if user.pro==True: raise HTTPException(400,'Вы уже обладатель премиума')

    ex=select(Promo).filter(Promo.value==promo)
    result=await (db.execute(ex))
    res=result.first()
    if not(res):
        return RedirectResponse('/mainpage', status_code=303)
    promocode=res[0]
    user.pro=True
    await db.delete(promocode)
    await db.commit()
    return RedirectResponse('/mainpage', status_code=303)
