from fastapi import APIRouter, Response

frontend_router = APIRouter()


@frontend_router.get("/ui/login", include_in_schema=False)
async def login_page() -> Response:
    html = """
    <!doctype html>
    <html>
    <head><meta charset='utf-8'><title>User Service - Login</title></head>
    <body>
      <h1>Login (user-service)</h1>
      <form id="login">
        <label>Email: <input name="email" value="test@example.com"></label><br>
        <label>Password: <input name="password" type="password" value="test_pass"></label><br>
        <button type="submit">Login</button>
      </form>
      <pre id="out"></pre>
      <script>
      document.getElementById('login').addEventListener('submit', async (e)=>{
        e.preventDefault();
        const form = new FormData(e.target);
        const body = { username: form.get('email'), password: form.get('password') };
        const r = await fetch('/api/v1/login/', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const text = await r.text();
        document.getElementById('out').innerText = text;
      });
      </script>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")
