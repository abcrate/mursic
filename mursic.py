import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=["mursic ", "jarvis "], intents=intents, help_command=None
)

queues = {}

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
    "executable": "ffmpeg",
}


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = deque()
    return queues[guild_id]


async def play_next(ctx):
    queue = get_queue(ctx.guild.id)

    if len(queue) == 0:
        await ctx.send("✅ Queue finished!")
        await ctx.voice_client.disconnect()
        return

    url, title = queue.popleft()

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
    except Exception as e:
        await ctx.send(f"❌ Skipping **{title}** — could not load: {e}")
        await play_next(ctx)
        return

    source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

    def after_playing(error):
        if error:
            print(f"Player error: {error}")
        asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

    ctx.voice_client.play(source, after=after_playing)
    await ctx.send(f"🎵 Now playing: **{title}**")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")


@bot.command(name="play")
async def play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel first!")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)

    await ctx.send("🔍 Fetching info...")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Unknown")
    except Exception as e:
        await ctx.send(f"❌ Could not fetch video info: {e}")
        return

    queue = get_queue(ctx.guild.id)

    if ctx.voice_client.is_playing():
        queue.append((url, title))
        await ctx.send(f"➕ Added to queue: **{title}** (position {len(queue)})")
    else:
        queue.appendleft((url, title))
        await play_next(ctx)


@bot.command(name="skip")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!")
    else:
        await ctx.send("Nothing is playing!")


@bot.command(name="queue")
async def show_queue(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        await ctx.send("The queue is empty!")
        return

    msg = "**📋 Queue:**\n"
    for i, (url, title) in enumerate(queue, 1):
        msg += f"`{i}.` {title}\n"
    await ctx.send(msg)


@bot.command(name="clear")
async def clear(ctx):
    queues[ctx.guild.id] = deque()
    await ctx.send("🗑️ Queue cleared!")


@bot.command(name="stop")
async def stop(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = deque()
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Stopped and disconnected!")
    else:
        await ctx.send("I'm not in a voice channel!")


@bot.command(name="help")
async def help_command(ctx):
    await ctx.send("""
🎵 **Mursic Bot Commands**

`mursic play <url>` — play a YouTube video or add it to the queue
`mursic skip` — skip the current song
`mursic queue` — show the upcoming songs
`mursic clear` — clear the queue
`mursic stop` — stop playing and disconnect

💡 You can also use `jarvis` instead of `mursic` for all commands!
    """)


bot.run(os.environ["BOT_TOKEN"])
