import aiohttp
from munch import munchify
from urllib.parse import quote_plus

conversations = {}
session = aiohttp.ClientSession()

async def wolframalpha(appid, ctx, query):
    async with ctx.channel.typing():
        if ctx.author.id not in conversations:
            conversations[ctx.author.id] = munchify({"host": "", "id": "", "s": ""})

        url = f"https://{conversations[ctx.author.id].host or 'api.wolframalpha.com'}/v1/conversation.jsp?" \
            f"appid={appid}" \
            f"&i={quote_plus(query)}"
        if conversations[ctx.author.id].id:
            url += f"&conversationid={conversations[ctx.author.id].id}"
        if conversations[ctx.author.id].s:
            url += f"&s={conversations[ctx.author.id].s}"

        async with session.request("GET", url) as resp:
            response = munchify(await resp.json(content_type="application/json"))

        if not hasattr(response, "error"):
            conversations[ctx.author.id].host = response.host + "/api"
            conversations[ctx.author.id].id = response.conversationID
            conversations[ctx.author.id].s = response.s if hasattr(response, "s") else ""
            return response.result
        else:
            raise ValueError(response.error)
