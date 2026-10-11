"""Read-only boundary checks against the two running local workbenches."""
import urllib.error
import urllib.request

opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
checks=[
    (5212,'/api/resume',{'Origin':'https://example.invalid','Content-Type':'application/json'},b'{}',403),
    (5213,'/api/jobs',{'Origin':'https://example.invalid','Content-Type':'application/json'},b'{}',403),
    (5212,'/outputs/%2e%2e/tasks.sqlite3',{},None,404),
    (5213,'/outputs/%2e%2e/jobs.json',{},None,404),
]
for port,path,headers,body,expected in checks:
    try:
        with opener.open(urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=body,headers=headers)) as response:
            code=response.status
    except urllib.error.HTTPError as exc: code=exc.code
    assert code==expected,(port,path,code)
    print(port,path,code)
print('PASS: cross-origin mutations and path traversal rejected')
