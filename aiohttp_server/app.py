from base64 import b64decode
from hashlib import md5

from aiohttp import web
from pydantic import ValidationError

import db
from validation_schemas import CreateAdv, CreateUser, UpdateAdv


app = web.Application()

async def db_context(app: web.Application):
    await db.create_all()
    yield
    await db.dispose()

app.cleanup_ctx.append(db_context)


async def check_req_auth(req_headers):
    auth_header = req_headers.get('Authorization')
    if not auth_header:
        return
    
    auth_header_split = auth_header.split()
    if len(auth_header_split) < 2:
        return

    auth_type = auth_header_split[0]
    if auth_type != 'Basic':
        return

    unicode_b64_utf8_logpas = auth_header_split[1]
    try:
        b64_utf8_logpas_bytes = \
            unicode_b64_utf8_logpas.encode(encoding='utf-8')
    except UnicodeEncodeError:
        return
    
    utf8_logpas_bytes = b64decode(b64_utf8_logpas_bytes)
    try:
        logpas = utf8_logpas_bytes.decode(encoding='utf-8')
    except UnicodeDecodeError:
        return
    
    logpas_split = logpas.split(':', maxsplit=2)
    if len(logpas_split) != 2:
        return

    req_login = logpas_split[0]
    if not req_login:
        return
    req_pwd = logpas_split[1]

    user = await db.get_user_by_email(req_login)
    if not user:
        return
    
    req_pwd_hash = md5(req_pwd.encode()).hexdigest()
    if req_pwd_hash != user.pwd_hash:
        return
    
    return user

class APIUserView(web.View):
    async def post(self):
        json_data = await self.request.json()
        if not json_data:
            return web.json_response(
                {
                    'status': 'error',
                    'description': "There is no JSON data in the request"
                }, status=400
            )
        
        try:
            validated_user_data = CreateUser(**json_data)
        except ValidationError as valid_error:
            return valid_error.errors(), 400
        
        user_data = validated_user_data.model_dump()
        user_pwd = user_data.pop('password')
        user_data['pwd_hash'] = md5(user_pwd.encode()).hexdigest()
        new_user_id = await db.create_user(user_data)
        if not new_user_id:
            raise web.HTTPConflict
        return web.json_response(
            {'id': new_user_id},
            status=201
        )


class APIAdvView(web.View):
    resp_no_json_data = web.json_response(
        {
            'status': 'error',
            'description': "There is no JSON data in the request"
        }, status=400
    )
    resp_adv_not_found = web.json_response(
        {
            'status': 'error',
            'description': f'Advertisement with this id not found.'
        }, status=404
    )
    
    @property
    def adv_id(self) -> int:
        return int(self.request.match_info.get('adv_id', '0'))

    async def get(self):
        adv = await db.get_adv(self.adv_id)
        if not adv:
            return self.resp_adv_not_found
        return web.json_response(adv.to_dict())
    
    async def post(self):
        json_data = await self.request.json()
        if not json_data: 
            return self.resp_no_json_data
        
        user = await check_req_auth(self.request.headers)
        if not user:
            raise web.HTTPUnauthorized
        
        try:
            validated_adv_data = CreateAdv(**json_data)
        except ValidationError as valid_error:
            return web.json_response(valid_error.errors(), status=400)

        adv_data = validated_adv_data.model_dump(exclude_unset=True)
        adv_data['owner_id'] = user.id
        new_adv_id = await db.create_adv(adv_data)
        return web.json_response({'id': new_adv_id}, status=201)

    async def patch(self):
        json_data = await self.request.json()
        if not json_data: 
            return self.resp_no_json_data
        
        user = await check_req_auth(self.request.headers)
        if not user:
            raise web.HTTPUnauthorized
        
        adv = await db.get_adv(self.adv_id)
        if not adv:
            return self.resp_adv_not_found
        
        if adv.owner_id != user.id:
            raise web.HTTPForbidden
        
        try:
            validated_adv_data = UpdateAdv(**json_data)
        except ValidationError as valid_error:
            return web.json_response(valid_error.errors(), status=400)

        adv_data = validated_adv_data.model_dump(exclude_unset=True)

        updated_adv = await db.update_adv(self.adv_id, adv_data)
        if updated_adv:
            raise web.HTTPNoContent
        if updated_adv is None:
            return self.resp_adv_not_found
        if updated_adv is False:
            raise web.HTTPBadRequest

    async def delete(self):
        user = await check_req_auth(self.request.headers)
        if not user:
            raise web.HTTPUnauthorized
        
        adv = await db.get_adv(self.adv_id)
        if not adv:
            return self.resp_adv_not_found
        
        if adv.owner_id != user.id:
            raise web.HTTPForbidden
        
        if not await db.delete_adv(self.adv_id):
            return self.resp_adv_not_found
        raise web.HTTPNoContent


API_ROUTE = '/api'

app.add_routes(
    [
        web.post(API_ROUTE + '/user/', APIUserView),
        web.post(API_ROUTE + '/adv/', APIAdvView),
        web.get(API_ROUTE + '/adv/{adv_id:\d+}', APIAdvView),
        web.delete(API_ROUTE + '/adv/{adv_id:\d+}', APIAdvView),
        web.patch(API_ROUTE + '/adv/{adv_id:\d+}', APIAdvView),
    ]
)

if __name__ == '__main__':
    web.run_app(app)