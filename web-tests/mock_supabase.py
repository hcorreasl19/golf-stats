"""Local-only Supabase HTTP double. No external requests or real credentials."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from datetime import datetime, timezone
import base64
import copy
import json
import time

USER_ID='11111111-1111-4111-8111-111111111111'
OTHER_ID='22222222-2222-4222-8222-222222222222'
STAMP='2025-01-01T00:00:00Z'
USER={'id':USER_ID,'aud':'authenticated','role':'authenticated','email':'player@example.test','email_confirmed_at':STAMP,'phone':'','confirmed_at':STAMP,'app_metadata':{'provider':'email','providers':['email']},'user_metadata':{},'identities':[],'created_at':STAMP,'updated_at':STAMP}


def fixture(id,owner,course):
    return dict(id=id,user_id=owner,course=course,date='01/01/2025',handicap=12,
                pars=[4]*9,scores=[5]*9,putts=[2]*9,girs=[0]*9,penalties=[0]*9,
                fairway_opportunities=9,fairways_hit=3,up_and_down_opportunities=3,up_and_downs_converted=1)

STATE={}


def reset():
    STATE.update(user=copy.deepcopy(USER),rows=[fixture(1,USER_ID,'Campo antigo'),fixture(900,OTHER_ID,'Campo de outro usuário')],password='test-password',password_updates=0,emails=0,requests=[])


reset()


def token():
    encode=lambda d:base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip('=')
    return encode({'alg':'HS256','typ':'JWT'})+'.'+encode({'sub':USER_ID,'aud':'authenticated','role':'authenticated','email':USER['email'],'exp':int(time.time())+3600,'iat':int(time.time()),'iss':'http://127.0.0.1:8900/auth/v1'})+'.'+base64.urlsafe_b64encode(b'test-only-signature').decode().rstrip('=')


def session():
    return dict(access_token=token(),token_type='bearer',expires_in=3600,expires_at=int(time.time())+3600,refresh_token='test-only-refresh',user=STATE['user'])


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass

    def respond(self,status,data):
        raw=json.dumps(data).encode() if status!=204 else b''
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
        return json.loads(raw) if raw else {}

    def route(self):
        parts=urlsplit(self.path);path=parts.path;query=parse_qs(parts.query)
        if path=='/test/reset':reset();return self.respond(200,{})
        if path=='/test/state':return self.respond(200,{'rows':STATE['rows'],'metadata':STATE['user']['user_metadata'],'password_updates':STATE['password_updates'],'emails':STATE['emails'],'requests':STATE['requests']})
        STATE['requests'].append({'method':self.command,'path':path,'query':query})
        body=self.body() if self.command in ('POST','PUT','PATCH') else {}
        if path=='/auth/v1/token':
            kind=query.get('grant_type',[''])[0]
            if kind=='password' and (body.get('email')!=USER['email'] or body.get('password')!=STATE['password']):return self.respond(400,{'code':'invalid_credentials','msg':'Invalid login credentials'})
            return self.respond(200,session())
        if path=='/auth/v1/signup':return self.respond(200,STATE['user'])
        if path=='/auth/v1/verify':return self.respond(200,session())
        if path in ('/auth/v1/recover','/auth/v1/resend'):
            STATE['emails']+=1;return self.respond(200,{})
        if path=='/auth/v1/logout':return self.respond(204,{})
        if path=='/auth/v1/user':
            if not self.headers.get('Authorization','').startswith('Bearer '):return self.respond(401,{'code':'bad_jwt','msg':'Missing session'})
            if self.command=='PUT':
                if isinstance(body.get('data'),dict):STATE['user']['user_metadata'].update(body['data'])
                if body.get('password'):STATE['password']=body['password'];STATE['password_updates']+=1
            return self.respond(200,STATE['user'])
        if path=='/rest/v1/rounds':
            if not self.headers.get('Authorization','').startswith('Bearer '):return self.respond(401,{'code':'42501','message':'Unauthorized'})
            rows=[r for r in STATE['rows'] if r['user_id']==USER_ID]
            for key in ('id','user_id'):
                if key in query:
                    expected=query[key][0].removeprefix('eq.');rows=[r for r in rows if str(r[key])==expected]
            if self.command=='GET':
                offset=int(query.get('offset',['0'])[0]);limit=int(query.get('limit',['500'])[0]);rows=sorted(rows,key=lambda r:r['id'])[offset:offset+limit]
            elif self.command=='POST':
                if body.get('user_id')!=USER_ID:return self.respond(403,{'code':'42501','message':'Wrong owner'})
                row=dict(body,id=max(r['id'] for r in STATE['rows'])+1);STATE['rows'].append(row);rows=[row]
            elif self.command in ('PATCH','DELETE'):
                if 'id' not in query or query.get('user_id')!=['eq.'+USER_ID]:return self.respond(403,{'code':'42501','message':'Owner filter required'})
                if self.command=='PATCH':
                    for r in rows:r.update(body)
                else:
                    ids={r['id'] for r in rows};STATE['rows']=[r for r in STATE['rows'] if r['id'] not in ids]
            if 'application/vnd.pgrst.object+json' in self.headers.get('Accept',''):
                if len(rows)!=1:return self.respond(406,{'code':'PGRST116','message':'Expected one row'})
                return self.respond(200,rows[0])
            return self.respond(200,rows)
        return self.respond(404,{'message':'Not found'})

    do_GET=route
    do_POST=route
    do_PUT=route
    do_PATCH=route
    do_DELETE=route


if __name__=='__main__':
    print('Local Supabase double listening on 127.0.0.1:8900',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8900),Handler).serve_forever()
