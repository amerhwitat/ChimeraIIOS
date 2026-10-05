Short:    Updates AmigaOS 3.1/5/9 with 3.1.4
Author:   kurq@yahoo.com (Ignacio Gully)
Uploader: kurq@yahoo.com (Ignacio Gully)
Type:     misc/os
Version:  46.5
Requires: AmigaOS 3.1 or AmigaOS 3.5 or AmigaOS 3.9, and AmigaOS 3.1.4
Architecture: generic



Updateto314 46.5 (12th October 2018)
                            

Introduction:
 
This a quick and dirty hack of a program/AmigaDOS script that 
performs an update over an existing AmigaOS 3.1/5/9 system with the 
most recent AmigaOS 3.1.4.

Be warned though, that there are much more efficient ways of doing 
this, but reading the script code, you will get the notion on how to
do it yourself, and may eventually decide to follow an 
easier/alternative/customized route and share it with everyone else.


Requirements: 
 
AmigaOS 3.1, 3.5 or 3.9 already installed in your harddrive.
About 4MB of free hdd space and some ram.


Usage:

Back up your harddisk first. No complaints if something wrong happens!

The entire package should be unarchived as it is, in the 
AmigaOS 3.1/3.5/3.9 system you are going to update.

Just boot from your AmigaOS 3.1/3.5/3.9 system and double click on the 
Update drawer, and then double click on the Updateto314 icon.

Be ready to have your 3.1.4 floppies at hand to insert them when the 
program asks you to.


Details:

Updateto314 will attempt to perform a full AmigaOS 3.1.4 installation 
on top of your existing AmigaOS 3.1/3.5/3.9 system.

It will install all languages, keymaps, and printers. 

The icons the user had already been using on their system, will not be 
replaced, but their tooltypes will be updated to meet 3.1.4 standards.

If the program finds the IconEdit program from 3.5/3.9 in the Tools 
drawer, it will not update it, as I do prefer the 3.5/3.9 one, beyond 
what 3.1.4 offers (it is my personal choice).

CacheCDFS is the cdrom filesystem that came with AmigaOS 3.9. It will 
still remain functional but not by default, because AmigaOS 3.1.4 
brings along an updated and more robust cdrom filing system, which 
the user will have to configure manually, using the new CD0 mountlist 
located in the sys:Storage/DOSDrivers drawer. 

However, if the user still prefers to continue using CacheCDFS, he 
can do it just by instead using the mountlist named "CD0.old" 
which will be in the usual place (sys:Storage/DOSDrivers).

The old catalogs from 3.1/5/9 will be backed up in your 
SYS:Locale:OldCatalogs drawer, just in case you want to use them for 
something.

Your old startup-sequence has also been backed up as 
sys:s/startup-sequence.bak in case you need to tweak your current one 
to reach the functional status you desire.

I decided to leave all 3.5/3.9 prefs untouched with the exception of 
the new 3.1.4 workbench prefs program, that I set to be installed, as 
it has the ability to set maximun filename length (the 3.9 counterpart 
does not allow this).

Thanks to:

Geri for the prepcard typo report.
Stefan Haubenthal for the tip on lha.
Tim Ocock for the failat suggestion.

Have fun!
Ignacio

Changelog:

46.0 Initial release.
46.1 Now leaves all 3.9 prefs programs except workbench.
46.2 Fixed a harmless bug (prepcard typo). Internal Release.
46.3 Added Loadmodule to all installations + failat 21. Internal test.
46.4 Added the option to update a 3.1 system + minor fixes.
46.5 Code cleanup, fixed documentation, added more code comments.