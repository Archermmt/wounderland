# wounderland
This repo reconstruct the AI agent project: https://github.com/joonspk-research/generative_agents
using vue, phaser and django. The default llm model is Yi-34B-Chat of QIANFAN platform, register for llm model @ https://qianfan.cloud.baidu.com/

To test the agents in village, 2 ways are provided:
0. install wounderland
    cd wounderland && pip install -r requirements.txt && python setup.py install

1. simulate with frontend
1.1 setup django (only the first time you start the project):
    cd playground && python manage.py makemigrations && python mange.py migrate
1.2 start server
    cd playground && python manager.py runserver
1.3 setup llm keys
    Visit the server in browser (e.g. http://127.0.0.1:8000/village). Now the agent think and move randomly in the village.
    To enable the agent with llm "brain", please follow the following steps:
        1.3.1 Open "User" board on the left part of game, go to tag "info" and login with your name+password (type in anything you like, but make sure to remember the password).
        1.3.2 Goto "keys" tag and set service keys for QIANFAN, to make the llm work, QIANFAN_AK && QIANFAN_SK are needed.
        1.3.3 Refresh the page, and you'll see agents walking around on time (calling llm service takes some time, so the agent may "freezed" when other agent thinking). You can check the agent status from "Agent" board.

2. simulate locally