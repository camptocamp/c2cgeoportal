.. _integrator_preparative_work:

============================================================
Configuring Windows tools required to connect to our servers
============================================================

Creating a SSH Key with Windows
===============================

1. Download PuTTYgen:

   a. Windows: http://the.earth.li/~sgtatham/putty/latest/x86/puttygen.exe
   b. Other operating systems: http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html

2. Choose key type  "SSH-2 RSA"

3. Click "Generate" and move the mouse over the window until the blue bar shows 100%.

4. Enter a password into "Key passphrase" and confirm with "confirm passphrase"

5. Save the private and public part of the key. Send the public part to the system administrators of the server you want to have access.

Add your SSH Public Key to Github
=================================

In order to pull and push to Github from your server, you need to add the key to Github: https://help.github.com/articles/generating-ssh-keys/#step-4-add-your-ssh-key-to-your-account

Connecting to a server from Windows
===================================

Command Line
------------

Based on the PuTTY software. Useful to launch commands on the server.

1. Download PuTTY: http://the.earth.li/~sgtatham/putty/latest/x86/putty.exe
2. Configurate PuTTY:
   a. In the left-hand column (Category), choose "Connection>SSH>Auth"
   b. Fill the "Private key file for authentication" field
3. Auto-login:
   a. One may save his/her username in "Connection>Data" > "Auto-login username"
4. Connect to the server:
   a. Fill connection info in the Session tab ("Connection Type" should be set at "SSH")
   b. Save the configuration
   c. Click on "Open" and type your passphrase when prompted
5. if you get disconnected because of your network configuration (proxies etc.) you should follow [this explanation](http://superuser.com/questions/389378/winscp-and-putty-drop-out-constantly-on-other-computer-they-dont)

Visual Interface
----------------

Based on the WinSCP software. Useful to browse the server, download/upload/edit files in a Windows-like interface. WinSCP manual is available online at http://winscp.net/eng/docs/start

1. Download WinSCP: http://winscp.net/eng/download.php
2. Open WinSCP
3. Edit your connection info in the "Session" tab
4. In the "SSH > Protocol Options" section, make sure that SSH version is set to "2".
5. Click on "Connect" and type your passphrase when prompted.
6. if you get disconnected because of your network configuration (proxies etc.) you should follow [this explanation](http://superuser.com/questions/389378/winscp-and-putty-drop-out-constantly-on-other-computer-they-dont)

Saving your Passphrase with PuTTY or WinSCP
-------------------------------------------

To avoid having to type your passphrase every time you connect to the server using PuTTY or WinSCP, you may use Pageant, an authentication agent program, part of WinSCP (Windows Start Menu > All Programs > WinSCP > Key Tools > Pageant):

Launch Pageant (appears in the status bar in Windows bottom-right corner)
Click on "Add Key" and choose your private key
Type your passphrase when prompted.

Using PuTTY to Access the Server Database
-----------------------------------------

The following page explains how to set up an SSH tunnel using PuTTY: http://www.postgresonline.com/journal/archives/38-PuTTY-for-SSH-Tunneling-to-PostgreSQL-Server.html

We do recommend to use the PuTTY SSH tunnel and not the PGAdminIII tunnelling functionality.
