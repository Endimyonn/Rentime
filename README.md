# Rentime
Rentime is a library providing tools to create powerful Ren'Py game mods without modifying files on disk. It's made for Ren'Py 8, and supports 6.99 and newer (see [Compatibility](#Compatibility)).

The primary driver behind its development was to enable the creation of mods in such a way that no base game files are altered, thereby ensuring created mods can be easily packaged, distributed, installed, and removed. It also helps enable mods that are resistant to game updates through scan-based content editing.



## Table of Contents
1. [Features](#Features)
    - [Script modification](#Script-modification)
    - [Screen (UI) modification](#Screen-UI-modification)
    - [LayeredRen](#LayeredRen)
2. [Compatibility](#Compatibility)
    - [Engine Versions](#Engine-Versions)
    - [Platforms](#Platforms)
3. [Installation](#Installation)
4. [Usage](#Usage)
    - [Examples](#Examples)
5. [Contributing](#Contributing)
6. [License](#License)



## Features
### Script modification
- Find labels by name
- Scan node trees for arbitrary nodes meeting criteria
- Create new blocks of script
- Insert blocks of script into existing ones
    - Automatically patch tree branches to ensure accurate logic flow
- Modify menus:
    - Add/edit/remove menu caption
    - Edit/remove menu caption's speaker
    - Modify menu choice label/condition/result
    - Add new menu choices
    - Get index of specific choice based on characteristics
- Modify If statements:
    - Edit condition/result
    - Get index of specific item based on condition

### Screen (UI) modification
- Find screens by name
- Scan screens for arbitrary elements meeting criteria
- Create new screens
- Insert additional content into existing screens
- Embed a screen into another
- Find and modify If statements' conditions and results

### LayeredRen
LayeredRen is a component of Rentime. It allows mods to substitute most files with ones of their choice.  
It works by altering file load requests prior to fulfillment, based on registered "patches".

The main use for LayeredRen (much like its namesake, LayeredFS of the Luma3DS and Atmosphère CFWs) is game asset substitution -- replacing images, videos, audio, etc..

LayeredRen offers three ways to substitute files:
- **FSPatches** allow mods to designate a directory as a "layered game directory", where it is treated as an alternative version of the "game" directory, and any files whose path inside it matches a "game" directory file's path will be loaded over that file.
    - This can be thought of as analogous to LayeredFS.
- **FilePatches** allow a single file path to be redirected to another.
    - This is intended as a lightweight way to substitute a single file without having to recreate the folder structure leading to it.
- **DirPatches** allow all files whose path starts with a specific substring to have that substring changed.
    - This is intended mostly for redirecting from one RPA archive to another.

**FSPatch is the generally recommended solution.** The other two are auxiliary and should not be used without a specific reason.

In addition, all three patch types are able to have priority values assigned per-patch, determining if one patch is applied over another conflicting patch. If the priorities are identical, precedence is taken in order of first-loaded, followed by type: FilePatch > FSPatch > DirPatch.  
Further, they allow a "condition" Python statement to be provided, which must then evaluate to True at the time any potential victim file is loaded in order for the patch to be applied.

Note that it is unable to safely substitute a handful of engine-related file types, namely .rpy scripts and .rpa archives, due to the nature of how they are loaded. That said, the core goal of Rentime is to remove the need to replace these files in the first place by allowing picky content replacement and modification, so you shouldn't be doing that anyway.



## Compatibility
### Engine Versions
**Ren'Py 8.3.0** and newer is the primary target of Rentime. It should have excellent compatibility with any version of Ren'Py 8.  
**Ren'Py 7.3.5** has been tested to work.  
**Ren'Py 6.99** has been tested to work non-exhaustively.  
**Ren'Py 6.18** and older are untested, and due to its age (over 10 years old), is not supported. Expect things to not work.

Certain methods involving modifying Menu captions are unavailable below Ren'Py 7.3.3.  
Given the wide range of versions Rentime targets, it is difficult to test on all of them. If you encounter any bugs, please make an issue so it can be addressed.

### Platforms
**Windows** is supported.  
**Linux** is supported.  
**MacOS** is supported, but untested (I don't own one).  
**Android** is untested. Newer OS versions block access to the `game` directory used for installation. Some features are likely nonfunctional.  
**iOS** is untested. Some features are likely nonfunctional.  
**Consoles** are nigh-untestable, but should work fine if you can get it installed.  
**Web/HTML5** is unsupported.



## Installation
To install Rentime, head to the Releases page and download `Rentime.rpy`. Place this file anywhere inside the game's `game` directory or a subdirectory of it, which is found in the same directory as its executable.

I highly recommend creating a new directory inside `game` called `mods`, and putting it in that for organization purposes (and so it doesn't get mixed in with base game files).



## Usage
Rentime is designed to be as accessible as it can, but there is a learning curve involving parts of the engine's internals.  
It is strongly advised to gain a basic understanding of [Ren'Py's AST system](https://github.com/renpy/renpy/blob/master/renpy/ast.py), which is the form scripts take once loaded. While many goals can be accomplished without doing so (for instance, embedding a new screen into another), it is necessary to understand it to perform more complex modifications, such as modifying choice menus and altering the outcomes of conditionals.  
Additionally, Ren'Py's UI system uses a very similar, but [separate](https://github.com/renpy/renpy/tree/master/renpy/sl2) AST system.

That being said, the bread and butter of Rentime is node searching (FindNode & SLSearch) and LayeredRen. Plenty of additional utility methods are provided to manipulate nodes and node trees, but the most capable of mods will be created with an understanding of the AST systems, and of Ren'Py's other internals.

### Examples
See the `Examples` directory in the source tree for scripts demonstrating most of the capabilities of Rentime.

Most examples are designed to operate in any Ren'Py game.  
If an example is designed for one specific game, it will note that in its header, and disable itself if run in a different game.



## Contributing
Pull requests are welcome.



## License
Rentime is licensed under the Apache 2.0 license.  
As such, you're mostly free to do whatever you want with it, as long as the notice header included at the top of `Rentime.rpy` remains unaltered.  
See the "LICENSE" file or go [here](http://www.apache.org/licenses/LICENSE-2.0) for more info on what you can and cannot do.