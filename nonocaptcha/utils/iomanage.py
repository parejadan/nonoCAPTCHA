import os
import aiofiles
import asyncio
import shutil
import pickle


async def save_file(file, data, binary=False):
    mode = "w" if not binary else "wb"
    async with aiofiles.open(file, mode=mode) as f:
        await f.write(data)


async def load_file(file, binary=False):
    mode = "r" if not binary else "rb"
    async with aiofiles.open(file, mode=mode) as f:
        return await f.read()


def clean_path(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    except Exception:
        raise


def create_path(path):
    try:
        os.makedirs(path, exist_ok=True, mode=0o777)
    except Exception:
        raise


def serialize(obj, p):
    """Must be synchronous to prevent corrupting data"""
    with open(p, "wb") as f:
        pickle.dump(obj, f)


async def deserialize(p):
    data = await load_file(p, binary=True)
    return pickle.loads(data)