import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import SwapiPeople

load_dotenv()

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
BASE_URL = "https://swapi-node.vercel.app/api"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def fetch_json(session, url):
    async with session.get(url) as response:
        return await response.json()

async def resolve_homeworld(session, homeworld_url):
    data = await fetch_json(session, BASE_URL + homeworld_url)
    return data['name']

async def resolve_films(session, films_urls):
    titles = []
    for url in films_urls:
        data = await fetch_json(session, BASE_URL + url)
        titles.append(data['title'])
    return ", ".join(titles)

async def resolve_starships(session, starships_urls):
    classes = []
    for url in starships_urls:
        data = await fetch_json(session, BASE_URL + url)
        classes.append(data['starship_class'])
    return ", ".join(classes)

async def resolve_vehicles(session, vehicles_urls):
    names = []
    for url in vehicles_urls:
        data = await fetch_json(session, BASE_URL + url)
        names.append(data['name'])
    return ", ".join(names)

async def process_character(session, character):
    fields = character['fields']
    id_val = fields['url'].split('/')[-1]

    homeworld = await resolve_homeworld(session, fields['homeworld'])
    films = await resolve_films(session, fields['films'])
    starships = await resolve_starships(session, fields['starships'])
    vehicles = await resolve_vehicles(session, fields['vehicles'])

    data = {
        'id': id_val,
        'name': fields['name'],
        'birth_year': fields['birth_year'],
        'eye_color': fields['eye_color'],
        'gender': fields['gender'],
        'hair_color': fields['hair_color'],
        'height': fields['height'],
        'mass': fields['mass'],
        'skin_color': fields['skin_color'],
        'homeworld': homeworld,
        'films': films,
        'starships': starships,
        'vehicles': vehicles
    }

    async with AsyncSession() as db:
        db_obj = SwapiPeople(**data)
        db.add(db_obj)
        await db.commit()

async def main():
    async with aiohttp.ClientSession() as session:
        page = 1
        all_tasks = []
        while True:
            url = f"{BASE_URL}/people?page={page}&limit=10"
            data = await fetch_json(session, url)

            for character in data['results']:
                task = asyncio.create_task(process_character(session, character))
                all_tasks.append(task)
            page += 1
        await asyncio.gather(*all_tasks)
        print("Все данные загружены!")


if __name__ == "__main__":
    asyncio.run(main())
