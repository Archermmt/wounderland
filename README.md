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
2.1 prepare a ckpt.json file for simulate, it should looks like:
    {
        "keys": {
            "OPENAI_API_KEY": "",
            "QIANFAN_AK": "$YOUR_AK",
            "QIANFAN_SK": "$YOUR_SK",
            "ZHIPUAI_API_KEY": ""
        },
        "keep_storage": false,
        "agents": {},
        "time": "20230213-09:30"
    }
    meaning of kwargs:
    keys: keys for calling llm service
    keep_storage: whether to use stored memory
    time: start time for simulation
2.2 start the simulation:
    cd tests
    python test_village.py --step 20 --verbose debug --stride 10 --checkpoint ckpt.json
    arguments:
    step: how many steps to simulate
    stride: how many minutes to forward after each step, e.g 9:00->9:10->9:20 if stride=10
    ckeckpoint: from which checkpoint the simulation starts
