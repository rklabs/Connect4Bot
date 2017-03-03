Connect4Bot
-------------

Connect4Bot is a slack bot which can be added to slack group and any player can initiate connect4 game with another user. The connect4 game has been implemented as separate module which can be used or run independently.


Introduction:
--------------
Below are the steps to setup the bot 

1. Create virtual env for connect4bot

    ```mkvirtualenv connect4botenv```
2. Install SlackClient Python package and it's dependencies

    ```pip install -r requirements.txt```
3. Export api token generated while creating bot, which is used for setting up websocket connection

    ``` export SLACK_BOT_API_TOKEN='xxxyyyyyzzzzz' ```
    
4. Create new slack group and add connect4 bot and add atleast 2 users
(I have created https://connect4group.slack.com and added ```connect4bot``` and 2 users)    

5. You should be all set to start the connect4 bot 

``` (connect4botenv) rkadam@rkadam-vbox:~/github/connect4bot$ python connect4bot.py```

connect4.py
------------
This Python module contains `class Connect4`. It implements all methods required for connect4 game play.
It can also independently simulate connect4 game play by choosing random columns. 

connect4bot.py
---------------
This Python module contains three classes `class SlackApi`, `class RTMHandler` and `class Connect4Bot`.

`class SlackApi`
-----------------
This class contains methods for initializing slack client using api token, for getting all users in the team(group)
and posting slack messages(DM)

`class RTMHandler`
-------------------
This class has methods for connecting to slack websocket server and for reading slack messages from server 

`class Connect4Bot`
-------------------
This class contains the core functionality of the slack bot. It has methods for initializing connect4 game,
initializing bot, starting game, selecting board column, handle different commands from user and sending
board to user.


Results:
---------
The connect4 game has been implemented as separate module and it can run independently.
I have used randomnly simulated columns for each user and below is the result from one
such run. Connect4 game is full functional.

[Screencast of terminal](https://asciinema.org/a/4kg197m6r1t1m19ukq4ndjjtd)

Enhancements:
--------------
1. Handle multiple boards between multiple user pairs
2. Handle specific exceptions instead of using Exception base class
3. Need better way of dealing with user commands to bot instead of searching for keywords in input string
4. Ask for opponent confirmation before starting the game
