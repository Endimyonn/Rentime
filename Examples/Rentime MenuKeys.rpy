# This mod allows number keys to be used to select Menu choices.
# It defines a screen to add the keybinds for each choice, then embeds that screen into the Menu screen.
init 999 screen MenuKeysScreen(items):
    $ iter = 0
    for mItem in items:
        if iter < 10:
            key "noshift_K_" + "1234567890"[iter] action mItem.action
            $ iter += 1
        else:
            break

init 999 python:
    InsertScreenUse(GetScreen("choice"), "MenuKeysScreen", "items") # 'items' is the argument for the 'use' statement we're embedding