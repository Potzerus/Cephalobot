import json
from typing import List

import discord
import requests
import yaml
from discord.ext import commands
from tinydb import Query, TinyDB

server = TinyDB("Data.json")

config_file = open("config.yaml")
config = yaml.load(config_file, Loader=yaml.FullLoader)
config_file.close()

bot = commands.Bot(command_prefix=config["bot_prefix"])


@bot.event
async def on_ready():
    app_info = await bot.application_info()
    print("Logged in! bot invite: https://discordapp.com/api/oauth2/authorize?client_id=" +
          str(app_info.id) + "&permissions=0&scope=bot")


@bot.event
async def on_member_remove(member : discord.Message):
    for stickied in config["sticky_roles"]:
        if member.guild.get_role(stickied) in member.roles:
            server.insert({"server_id": member.guild.id, "member_id": member.id, "role_id": stickied})
            print(member.name + " caught leaving with a stickied role")


@bot.event
async def on_member_join(member : discord.Message):
    for stickied in server.search((Query().server_id == member.guild.id) & (Query().member_id == member.id)):
        await member.add_roles(member.guild.get_role(stickied["role_id"]), reason="Role Persistence")
        server.remove((Query().server_id == member.guild.id) & (Query().member_id == member.id))
        print(member.name + " stickied roles restored")

@bot.event
async def on_message_delete(message : discord.Message):
    url = config["deleted_webhook"]
    payload = GenerateDeletedJsonBody(message)
    headers = {
        'Content-Type': "application/json",
        'Accept': "*/*",
    }

    requests.request("POST", url, data=payload, headers=headers)

@bot.event
async def on_bulk_message_delete(messages: List[discord.Message]):
    url = config["deleted_webhook"]
    headers = {
        'Content-Type': "application/json",
        'Accept': "*/*",
    }

    for message in messages:
        payload = GenerateDeletedJsonBody(message)
        requests.request("POST", url, data=payload, headers=headers)


def GenerateDeletedJsonBody(message : discord.Message):
    body = {
        "embeds": [
        {
            "author": {
                "name": "[DELETED] " + str(message.author),
                "icon_url": "https://cdn.discordapp.com/avatars/"+str(message.author.id)+"/"+str(message.author.avatar)+".png"
            },
            "description": "The following message was deleted",
            "fields": [
                {
                    "name": "User",
                    "value": message.author.mention,
                    "inline": "true"
                },
                {
                    "name": "Channel",
                    "value": "<#" + str(message.channel.id) +">",
                    "inline": "true"
                },
                {
                    "name": "Message",
                    "value": message.content
                }],
            "color": config["deleted_highlight"]
        }]
    }

    return json.dumps(body)

bot.run(config["bot_secret"])
