from aiohttp import web

app = web.Application()

@app.route('/')
async def health_check(request):
    return web.Response(text='Bot Health OK')

@app.route('/health')
async def health(request):
    return web.json_response({"status": "running"})

if __name__ == "__main__":
    web.run_app(app, host='0.0.0.0', port=10000)
