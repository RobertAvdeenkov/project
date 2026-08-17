from fastapi import FastAPI,Body,APIRouter,Form,Depends,Request,HTTPException,Query,Cookie
from database import get_db
from models import Base,Message
from fastapi.responses import FileResponse,RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from sqlalchemy import select,desc,text
from models import*
from auth import*
from fastapi import WebSocket

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
    response=RedirectResponse('/connection')
    response.set_cookie(key='token',value=token, max_age=3600, path='/')
    return response

@router.get('/connection')
async def connection(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/connect.html')

@router.websocket('/ws')
async def wso(websockets:WebSocket, token=Cookie(),  db:AsyncSession=Depends(get_db)):
    await websockets.accept()
    name=get_by_token(token)
    ex1=select(User).filter(User.name==name)
    result1=(await db.execute(ex1)).first()
    if not(result1):
        raise HTTPException(401, 'Вы не зарегистрированы')
    user=result1[0]
    ip=websockets.scope['client'][0]
    print(ip)
    if not(user.ip):
        user.ip=ip
        await db.commit()
    ex=select(Baned).filter(Baned.ip==ip)
    result=(await db.execute(ex)).first()
    if not(result):
        await websockets.close()
    else:
        return {'Сообщение':'В данный момент вы находитесь в бане.'}

@router.get('/mainpage')
async def root(request:Request,db:AsyncSession=Depends(get_db), token=Cookie()):
    name=get_by_token(token)

    ex1=select(User).filter(User.name==name)
    result1=(await db.execute(ex1)).first()
    if not(result1):
        raise HTTPException(401, 'Вы не зарегистрированы')
    user=result1[0]
    ex=select(Baned).filter(Baned.ip==user.ip)
    result=(await db.execute(ex)).first()
    if result:
        return RedirectResponse('/')
    return FileResponse('templates/messages.html')

@router.post('/messagesSHOW')
async def show(db:AsyncSession=Depends(get_db), token=Cookie()):
    name=get_by_token(token)
    ex=select(Message).order_by(desc(Message.likes_count), desc(Message.created_at))
    result=await (db.execute(ex))
    res=result.all()
    if not res:
        return {'message':'Сообщений пока нет :('}

    ex=select(User).filter(User.name==name)
    result=await (db.execute(ex))
    r=result.first()
    if not(result or r):raise HTTPException(401,'Вы не авторизованы')
    user=r[0] #type:ignore
    print(res)
    txt=f'<h2>Здравствуйте, {user.name}. Ваш премиум активирован<h2>' if user.pro==True else f'<h2>Здравствуйте, {user.name}.'
    txt+='<p></p>'
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

@router.get('/tops')
async def top(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/leaders.html')

@router.post('/topsSHOW')
async def topsSHOW(db:AsyncSession=Depends(get_db), token=Cookie()):
    get_by_token(token)
    ex=text('''
    with tables as(
    select users.name as name, COUNT(textUSERS.id) as colvo
    from users
    inner join textUSERS on users.id=textUSERS.user_id
    group by users.id
    order by COUNT(textUSERS.id) DESC
    limit 10
    )

    select name,
    colvo,
    row_number() over() as stage
    from tables
    ''')
    execute=(await (db.execute(ex))).all()
    if not(execute):
        return {'message':'<h2>Лидеров пока нет. Стань первым!<h2>'}
    txt=''
    for i in execute:
        txt+=f'<h2 style="color: {"#bcb645" if i[2]==1 else ''}{'gray;' if i[2]==2 else ''}{'#ff8e37' if i[2]==3 else ''}{"black;" if i[2]>3 else ''}">№{i[2]}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Имя: {i[0]}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Всего сообщений: {i[1]}<h2><p></p>'
    return {'message':txt}
    
    


