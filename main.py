import aiohttp
import json
from asyncio import run
from discord.ext import commands
from munch import munchify
from os import getenv
from random import choice
from urllib.parse import quote_plus

### required for running locally
# from dotenv import load_dotenv 
# load_dotenv()

TOKEN = getenv('TOKEN')
APPID = getenv('APPID')

bot = commands.Bot(command_prefix="$")

with open("exchanges.json", "r") as f:
    exchanges = json.load(f)
sessions = []
conversations = {}
async def aiohttpinit():
    return aiohttp.ClientSession()
aiohttpsession = run(aiohttpinit())


async def wolframalpha(appid, msg):
    async with msg.channel.typing():
        if msg.author.id not in conversations:
            conversations[msg.author.id] = munchify({"host": "", "id": "", "s": ""})

        url = f"https://{conversations[msg.author.id].host or 'api.wolframalpha.com'}/v1/conversation.jsp?" \
            f"appid={appid}" \
            f"&i={quote_plus(msg.content)}"
        if conversations[msg.author.id].id:
            url += f"&conversationid={conversations[msg.author.id].id}"
        if conversations[msg.author.id].s:
            url += f"&s={conversations[msg.author.id].s}"

        async with aiohttpsession.request("GET", url) as resp:
            response = munchify(await resp.json(content_type="application/json"))

        if not hasattr(response, "error"):
            conversations[msg.author.id].host = response.host + "/api"
            conversations[msg.author.id].id = response.conversationID
            conversations[msg.author.id].s = response.s if hasattr(response, "s") else ""
            return response.result
        else:
            raise ValueError(response.error)


def new_topic():
    """
    Start talking about a random topic.
    """
    topics = ["wasps", "ice cream", "school", "Fortnite",
              "burgers", "hotels", "getting a suntan"]
    topic = choice(topics) # choose a topic at random
    phrases = [f"So what do you think about {topic}?",
               f"Anyway, I really like {topic}!", f"That's really interesing but what about {topic}???"]
    phrase = choice(phrases)
    return phrase


async def respond(msg):
    """
    Generate a response to the user input.
    """
    user_input = msg.content.lower()
    words = user_input.split()
    response = responsecopy = new_topic()
    for word in words:
        if word in exchanges:
            responses = exchanges[word]
            response = choice(responses)
            break
    if response == responsecopy:
        try:
            response = await wolframalpha(APPID, msg)
        except ValueError:
            pass
    return response


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command()
async def hello(ctx):
    """Starts a new chatbot session"""
    if ctx.author.id not in sessions:
        sessions.append(ctx.author.id)
        await ctx.reply("Hello, nice to meet you!")
    else:
        await ctx.reply("There is already an ongoing bot session!")


@bot.command()
async def bye(ctx):
    """Exits the chatbot session"""
    if ctx.author.id in sessions:
        sessions.remove(ctx.author.id)
        await ctx.reply("It was nice chatting to you!")
    else:
        await ctx.reply("There is no active bot session!")


@bot.event
async def on_message(msg):
    if (await bot.get_context(msg)).valid:
        await bot.process_commands(msg)
        return  # Exit if the message invokes another command

    if msg.author.id in sessions:
        await msg.reply(await respond(msg))


bot.run(TOKEN)
