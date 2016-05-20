async def testfeature(msg, content):
    if content[:6] == "'marco":
        reply("polo")
handlers.append(testfeature)
