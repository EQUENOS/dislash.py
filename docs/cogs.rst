Cogs
====

Sorting commands between cogs is a popular practice in bot development.
This section shows how to build slash commands in cogs.

It's as simple as this:

::

    from dislash import *
    from discord.ext import commands


    class mycog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        # Example of a slash command in a cog
        @slash_commands.command(description="Says Hello")
        async def hello(self, ctx):
            await ctx.send("Hello from cog!")
        
        # Buttons in cogs (no changes basically)
        @commands.command()
        async def test(self, ctx):
            row_of_buttons = ActionRow(
                Button(
                    style=ButtonStyle.green,
                    label="Green button",
                    custom_id="green"
                ),
                Button(
                    style=ButtonStyle.red,
                    label="Red button",
                    custom_id="red"
                )
            )
            msg = await ctx.send("This message has buttons", components=[row_of_buttons])
            # Wait for a button click
            def check(inter):
                return inter.author == ctx.author
            inter = await msg.wait_for_button_click(check=check)
            # Process the button click
            inter.reply(f"Button: {inter.button.label}", type=ResponseType.UpdateMessage)
    
    def setup(bot):
        bot.add_cog(mycog(bot))

**What's different in cogs:**

* :class:`@slash_commands.command()` instead of :class:`@SlashClient.command()`

* ``self`` is a required first argument 

* :class:`self.bot` instead of :class:`bot`

* :class:`SlashClient` is accessible via :class:`self.bot.slash`
