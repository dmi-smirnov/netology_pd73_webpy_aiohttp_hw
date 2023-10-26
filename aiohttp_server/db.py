import os

import sqlalchemy as sql
import sqlalchemy.orm as sql_orm
import sqlalchemy.ext.asyncio as sql_asyncio
from sqlalchemy.exc import IntegrityError


DBMS = 'postgresql+asyncpg'
DB_HOST_ADDR = os.getenv('POSTGRESQL_HOST_ADDR', '127.0.0.1')
DB_HOST_PORT = os.getenv('POSTGRESQL_HOST_PORT', '5432')
DB_USER = os.getenv('POSTGRESQL_USER', 'test')
DB_PWD = os.getenv('POSTGRESQL_PWD', 'test')
DB_NAME = os.getenv('POSTGRESQL_DB', 'test')

DSN = \
    f'{DBMS}://{DB_USER}:{DB_PWD}@{DB_HOST_ADDR}:{DB_HOST_PORT}/{DB_NAME}'

engine = sql_asyncio.create_async_engine(DSN)

BaseClass = sql_orm.declarative_base()

Session = sql_orm.sessionmaker(class_=sql_asyncio.AsyncSession,
                               expire_on_commit=False,
                               bind=engine)


class User(BaseClass):
    __tablename__ = 'user'

    id = sql.Column(sql.Integer, primary_key=True)
    created = sql.Column(sql.DateTime, server_default=sql.func.now())
    email = sql.Column(sql.String(length=40), nullable=False, unique=True)
    pwd_hash = sql.Column(sql.String(length=50), nullable=False)


class Advertisement(BaseClass):
    __tablename__ = 'advertisement'

    id = sql.Column(sql.Integer, primary_key=True)
    created = sql.Column(sql.DateTime, server_default=sql.func.now())
    title = sql.Column(sql.String(length=50), nullable=False)
    description = sql.Column(sql.Text)
    owner_id = sql.Column(sql.Integer, sql.ForeignKey('user.id'), nullable=False)

    owner = sql_orm.relationship(User, backref='advertisement')

    def to_dict(self):
        return {
            'id': self.id,
            'created': str(self.created),
            'title': self.title,
            'description': self.description,
            'owner_id': self.owner_id
        }


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(BaseClass.metadata.create_all)

async def dispose():
    await engine.dispose()

async def create_user(data: dict):
    async with Session() as session:
        user = User(**data)
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            return False
        return user.id

async def get_user_by_email(email: str):
    async with Session() as session:
        query = sql.select(User).filter(User.email==email)
        query_result = await session.execute(query)
        if query_result:
            return query_result.scalar()

async def create_adv(data: dict):
    async with Session() as session:
        adv = Advertisement(**data)
        session.add(adv)
        await session.commit()
        new_adv_id = adv.id
    return new_adv_id

async def get_adv(adv_id: int):
    async with Session() as session:
        adv = await session.get(Advertisement, adv_id)
    return adv

async def update_adv(adv_id, data: dict):
    adv = await get_adv(adv_id)
    if not adv:
        return None
    
    for k, v in data.items():
        setattr(adv, k, v)
    
    async with Session() as session:
        session.add(adv)
        try:
            await session.commit()
        except IntegrityError:
            return False
    return True

async def delete_adv(adv_id: int) -> bool:
    adv = await get_adv(adv_id)
    if not adv:
        return False
    
    async with Session() as session:
        await session.delete(adv)
        await session.commit()
    return True
