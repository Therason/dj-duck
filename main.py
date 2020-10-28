import discord
import youtube_dl
import asyncio
from discord.ext import commands

ytdl_opts = {
    'format': 'bestaudio/best',
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

queue_list = []
title_list = []

ytdl = youtube_dl.YoutubeDL(ytdl_opts)

class YTSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Makes the bot join the specified voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, url=""):
        """Plays from the beginning of the queue or the provided url"""
        if url == "":
            for link in queue_list:
                async with ctx.typing():
                    player = await YTSource.from_url(link, loop=self.bot.loop)
                    ctx.voice_client.play(player, after=None)
                await ctx.send('Now playing: {}'.format(player.title))
                while(ctx.voice_client.is_playing()):
                    await asyncio.sleep(1)
        else:
            if(ctx.voice_client.is_playing()):
                await ctx.voice_client.stop()
                await asyncio.sleep(2)
            async with ctx.typing():
                player = await YTSource.from_url(url, loop=self.bot.loop)
                ctx.voice_client.play(player, after=None)
            await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def add(self, ctx, *, url):
        """Adds the provided url to the queue"""
        queue_list.append(url)
        vid = await YTSource.from_url(url, loop=self.bot.loop)
        title_list.append(vid.title)
        await ctx.send('Added {} to the queue!'.format(vid.title))

    @commands.command()
    async def queue(self, ctx):
        """Lists items in the queue"""
        if len(queue_list) == 0:
            await ctx.send("The queue is empty")
        else:
            idx = 1
            for title in title_list:
                await ctx.send(str(idx) + ': {}'.format(title))
                idx += 1

    @commands.command()
    async def skip(self, ctx):
        """Skips an item in the queue"""
        await ctx.voice_client.stop()
        await ctx.send("Skipped!")

    @commands.command()
    async def clear(self, ctx):
        """Clears the queue"""
        queue_list.clear()
        title_list.clear()
        await ctx.send("Cleared the queue")

    @commands.command()
    async def dc(self, ctx):
        """Disconnects the bot from the voice channel"""
        await ctx.voice_client.disconnect()

    @commands.command()
    async def code(self, ctx):
        """Displays info about the code"""
        await ctx.send("```My code can be found here: https://github.com/Therason/dj-duck```")

    @commands.command()
    async def remove(self, ctx, *, url):
        """Removes an item from a queue based on its position or url"""
        title = ""
        if url.isdigit():
            if int(url) <= 0 or int(url) > len(queue_list):
                await ctx.send("Error: out of range number")
            else:
                title = title_list[int(url)-1]
                queue_list.pop(int(url)-1)
                title_list.pop(int(url)-1)
                await ctx.send("Removed {} from the queue!".format(title))
        else:
            exists = False
            for i in range(0, len(queue_list)):
                if queue_list[i] == url:
                    queue_list.pop(i)
                    title = title_list[i]
                    title_list.pop(i)
                    exists = True
                    break
            if exists:
                await ctx.send("Removed {} from the queue!".format(title))
            else:
                await ctx.send("Request not in queue!")


bot = commands.Bot(command_prefix=commands.when_mentioned_or("-"), description="Basic music bot")
@bot.event
async def on_ready():
    print('Logged in as {0}'.format(bot.user))

bot.add_cog(Music(bot))
bot.run('BOT_TOKEN')
