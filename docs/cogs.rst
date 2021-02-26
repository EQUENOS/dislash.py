Cogs
====

Sorting commands between cogs is a popular practice in bot development.
This section shows how to build slash commands in cogs.

It's as simple as that:

::

    from dislash import slash_commands
    from dislash.interactions import *
    from discord.ext import commands


    class mycog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @slash_commands.command(description="Says Hello")
        async def hello(self, ctx):
            await ctx.send("Hello from cog!")
    
    def setup(bot):
        bot.add_cog(mycog(bot))

**What's different in cogs:**

* :class:`@slash_commands.command()` instead of :class:`@SlashClient.command()`

* ``self`` is a required first argument 

* :class:`self.bot` instead of :class:`bot`

* :class:`SlashClient` is accessible via :class:`self.bot.slash`