# This example demonstrates how to use LayeredRen to replace certain images in the game, without replacing them on disk.
# This mod is only designed for the freeware version of Doki Doki Literature Club, and will not run on another game.
# 
# Inside the mod directory (in this case, it should be game/mods/Example/LayeredRen example), we have a directory called "layer".
# Using LayeredRen, we will register this folder as a "layered game directory" by creating an FSPatch targeting "mods/Example/LayeredRen example/layer/".
# A "layered game directory" will be considered to be literally a second "game" directory placed on top of the real one.
# When the game requests a file to be loaded, LayeredRen intercepts this request to check the layered game directory to see if it has its own version of it.
# For example, if the game requests "gui/logo.png" to be loaded, LayeredRen will check if "mods/Example/LayeredRen example/layer/gui/logo.png" exists.
# If it finds it, it will be used instead of the base game's version of the file.
# As such, to replace any file used by the game, the proper directory structure must be recreated within the layer directory, and then the desired file.
#
# Doki Doki Literature Club is owned by Team Salvato.
# Wii, the Wiimote, and the Wii Classic Controller are owned by Nintendo.
# The assets belonging to the above in this mod are used in a transformative manner, and distributed under fair use.
init 1 python:
    # We create a dedicated init method and call it soon after instead of doing init directly under the "init" block.
    # This ensures cleanliness and that no defined variables are added to the global store.
    def Rentime_LayeredRenExample_Init():
        if config.name == "Doki Doki Literature Club!":
            LayeredRen_AddFSPatch("mods/Examples/LayeredRen example/layer/")
        else:
            Rentime_LayeredRenExample_NotifyWrongGame()
    
    def Rentime_LayeredRenExample_NotifyWrongGame():
        failure_str = "LayeredRen example: not activating because this isn't the target game"
        print(failure_str)
        if renpy.has_label("main_menu"):
            InsertScreenCode(GetLabel("main_menu"), "$ renpy.notify(\"" + failure_str + "\")")
    
    # Run the init method
    Rentime_LayeredRenExample_Init()