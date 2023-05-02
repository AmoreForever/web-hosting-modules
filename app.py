
#      ______     __    __     ______     ______     ______    
#     /\  __ \   /\ "-./  \   /\  __ \   /\  == \   /\  ___\   
#     \ \  __ \  \ \ \-./\ \  \ \ \/\ \  \ \  __<   \ \  __\   
#      \ \_\ \_\  \ \_\ \ \_\  \ \_____\  \ \_\ \_\  \ \_____\ 
#       \/_/\/_/   \/_/  \/_/   \/_____/   \/_/ /_/   \/_____/ 
                                                         
#     Copyright 2023 t.me/amorescam
#     Licensed under the GNU GPLv3


import shutil
import re
import uvicorn
from fastapi import (
    FastAPI,
    Request,
    Response,
    File,
    UploadFile,
    Depends,
    HTTPException,
    status,
)
from fastapi.templating import Jinja2Templates
from config import DOMAIN, MODS_DIR, TOKEN, FULL_FILE, PORT, SITE_TITLE

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def add_module_to_full_txt(modname):
    with FULL_FILE.open("r") as f:
        dmb = {line.strip() for line in f}
    if modname not in dmb:
        with FULL_FILE.open("a") as f:
            f.write(modname[:-3] + "\n")
            dmb.add(modname[:-3])
    else:
        return False


def delete_module_from_full_txt(modname):
    pattern = re.compile(re.escape(modname[:-3]))

    with open("mods/full.txt", "r") as file_handle:
        lines = file_handle.readlines()

    with open("mods/full.txt", "w") as file_handle:
        lines = [line for line in lines if not pattern.match(line)]
        file_handle.writelines(lines)


async def validate_token(token: str = None):
    if token is None or token != TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - ban / lack of rights",
        )


@app.post("/upload/")
async def upload(module: UploadFile = File(...), token: str = Depends(validate_token)):
    try:
        with open(MODS_DIR / module.filename, "wb") as f:
            shutil.copyfileobj(module.file, f)
        add_module_to_full_txt(module.filename)
    except Exception as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        module.file.close()
    return {
        "message": f"Successfully uploaded {module.filename}",
        "link": f"{DOMAIN}{module.filename}",
        "code": 200,
    }


@app.get("/view/{mod}")
async def get_web_view_of_mod(request: Request, mod: str):
    try:
        with open(MODS_DIR / mod, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        return Response(content="Not found", status_code=404)

    return templates.TemplateResponse(
        "view.html",
        {"request": request, "mod_code": code, "site_title": SITE_TITLE},
    )


@app.get("/full.txt")
async def get_full_list_of_modules():
    with FULL_FILE.open("r") as f:
        content = f.read()
    return Response(content=content, media_type="text/plain; charset=utf-8")


@app.get("/{mod}")
async def get_one_particular_mod(mod: str):
    try:
        with open(MODS_DIR / mod, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        return Response(content="Not found", status_code=404)

    return Response(content=code, media_type="text/plain; charset=utf-8")


@app.delete("/delete/{files}")
async def delete_file(files: str, token: str = Depends(validate_token)):
    try:
        (MODS_DIR / files).unlink()
        delete_module_from_full_txt(files)
        return {"message": "File deleted successfully", "code": 200}
    except Exception as e:
        return {"message": f"Error deleting file: {e}"}


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return Response(content="Not found", status_code=404)


if __name__ == "__main__":
    uvicorn.run(app, port=PORT)
